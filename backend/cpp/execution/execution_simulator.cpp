// src/cpp/execution/execution_simulator.cpp

#include "execution/execution_simulator.h"
#include <chrono>
#include <iostream>
#include <algorithm>
#include <thread>

namespace nexus::execution {

namespace {
    /**
     * @brief Atomically adds a value to an atomic double using compare-and-swap.
     * @param atomic_var The atomic double variable to modify.
     * @param value The value to add.
     */
    void atomic_add_double(std::atomic<double>& atomic_var, double value) {
        double current = atomic_var.load(std::memory_order_acquire);
        while (!atomic_var.compare_exchange_weak(current, current + value,
                                                std::memory_order_acq_rel,
                                                std::memory_order_acquire)) {
            // Loop until successful
        }
    }
}

ExecutionSimulator::ExecutionSimulator(const MarketSimulationConfig& config) : config_(config) {
    config_.validate();
    
    // Initialize random number generator
    random_generator_.seed(std::chrono::steady_clock::now().time_since_epoch().count());
    
    if (config_.use_order_book) {
        std::cout << "ExecutionSimulator: Order book simulation enabled" << std::endl;
        std::cout << "  - Tick size: " << config_.tick_size << std::endl;
        std::cout << "  - Market making: " << (config_.enable_market_making ? "enabled" : "disabled") << std::endl;
        std::cout << "  - Latency simulation: " << (config_.simulate_latency ? "enabled" : "disabled") << std::endl;
    } else {
        std::cout << "ExecutionSimulator: Simple slippage-based execution enabled" << std::endl;
    }
}

ExecutionSimulator::~ExecutionSimulator() {
    if (config_.enable_order_book_statistics || config_.use_order_book) {
        std::cout << "ExecutionSimulator: Final execution statistics:" << std::endl;
        std::cout << "  - Total executions: " << statistics_.total_executions.load() << std::endl;
        std::cout << "  - Total volume: " << statistics_.total_volume_executed.load() << std::endl;
        std::cout << "  - Average execution time: " << statistics_.average_execution_time_ns.load() << " ns" << std::endl;
        
        if (config_.use_order_book) {
            std::cout << "  - Order book operations: " << statistics_.order_book_operations.load() << std::endl;
            std::cout << "  - Market maker fills: " << statistics_.market_maker_fills.load() << std::endl;
        }
    }
}

void ExecutionSimulator::update_config(const MarketSimulationConfig& new_config) {
    std::lock_guard<std::mutex> order_books_lock(order_books_mutex_);
    std::lock_guard<std::mutex> market_maker_lock(market_maker_mutex_);
    
    config_ = new_config;
    config_.validate();
    
    // Clear existing order books if switching modes
    if (!config_.use_order_book) {
        order_books_.clear();
        market_maker_states_.clear();
    }
    
    // Reset statistics
    reset_statistics();
    
    std::cout << "ExecutionSimulator: Configuration updated" << std::endl;
}

nexus::core::TradeExecutionEvent* ExecutionSimulator::simulate_order_execution(
    const nexus::core::TradingSignalEvent& signal,
    double current_market_price,
    nexus::core::EventPool& pool) {
    
    auto start_time = get_current_time();
    
    nexus::core::TradeExecutionEvent* result = nullptr;
    
    if (config_.use_order_book) [[unlikely]] {
        // Use realistic order book simulation
        result = execute_order_book_order(signal, current_market_price, pool);
    } else [[likely]] {
        // Use simple slippage-based execution (original behavior)
        result = execute_simple_order(signal, current_market_price, pool);
    }
    
    // Simulate execution latency if enabled
    if (config_.simulate_latency && result) {
        simulate_execution_latency();
    }
    
    // Update statistics
    if (result) {
        auto execution_time = calculate_time_diff_ns(start_time, get_current_time());
        double volume = result->quantity;
        double value = volume * result->price;
        bool was_partial = false; // Simple execution is always full fill
        
        update_statistics(execution_time, volume, value, result->commission, was_partial);
    }
    
    return result;
}

void ExecutionSimulator::update_market_data(const std::string& symbol, double market_price, double volume) {
    if (!config_.use_order_book) {
        return; // No order book to update
    }
    
    // Add market maker liquidity if enabled
    if (config_.enable_market_making) {
        add_market_maker_liquidity(symbol, market_price);
    }
    
    // Update market maker state
    {
        std::lock_guard<std::mutex> lock(market_maker_mutex_);
        auto& state = market_maker_states_[symbol];
        state.last_market_price = market_price;
    }
}

MarketData ExecutionSimulator::get_market_data(const std::string& symbol) const {
    if (!config_.use_order_book) {
        // Return empty market data for simple mode
        MarketData data;
        data.symbol = symbol;
        data.timestamp = std::chrono::system_clock::now();
        return data;
    }
    
    std::lock_guard<std::mutex> lock(order_books_mutex_);
    auto it = order_books_.find(symbol);
    if (it != order_books_.end() && it->second) {
        return it->second->get_market_data();
    }
    
    // Return empty market data if no order book exists
    MarketData data;
    data.symbol = symbol;
    data.timestamp = std::chrono::system_clock::now();
    return data;
}

void ExecutionSimulator::reset_statistics() {
    std::lock_guard<std::mutex> lock(statistics_mutex_);
    
    statistics_.total_executions.store(0, std::memory_order_release);
    statistics_.market_orders_executed.store(0, std::memory_order_release);
    statistics_.limit_orders_executed.store(0, std::memory_order_release);
    statistics_.partial_fills.store(0, std::memory_order_release);
    statistics_.full_fills.store(0, std::memory_order_release);
    statistics_.total_volume_executed.store(0.0, std::memory_order_release);
    statistics_.total_value_executed.store(0.0, std::memory_order_release);
    statistics_.total_commission_charged.store(0.0, std::memory_order_release);
    statistics_.average_execution_time_ns.store(0.0, std::memory_order_release);
    statistics_.max_execution_time_ns.store(0.0, std::memory_order_release);
    statistics_.total_execution_operations.store(0, std::memory_order_release);
    statistics_.order_book_operations.store(0, std::memory_order_release);
    statistics_.average_order_book_latency_ns.store(0.0, std::memory_order_release);
    statistics_.market_maker_quotes_added.store(0, std::memory_order_release);
    statistics_.market_maker_fills.store(0, std::memory_order_release);
    statistics_.market_maker_pnl.store(0.0, std::memory_order_release);
    
    std::cout << "ExecutionSimulator: Statistics reset" << std::endl;
}

size_t ExecutionSimulator::get_active_order_book_count() const {
    std::lock_guard<std::mutex> lock(order_books_mutex_);
    return order_books_.size();
}

size_t ExecutionSimulator::cleanup_order_books() {
    if (!config_.use_order_book) {
        return 0;
    }
    
    size_t total_cleaned = 0;
    std::lock_guard<std::mutex> lock(order_books_mutex_);
    
    for (auto& [symbol, order_book] : order_books_) {
        if (order_book) {
            total_cleaned += order_book->cleanup_inactive_orders();
        }
    }
    
    return total_cleaned;
}

double ExecutionSimulator::calculate_execution_price(double quoted_price, bool is_buy) const {
    double slippage = 0.0;
    
    // Apply slippage based on order direction
    if (is_buy) {
        slippage = quoted_price * config_.slippage_factor;
    } else {
        slippage = -quoted_price * config_.slippage_factor;
    }
    
    // Apply bid-ask spread
    double spread_adjustment = 0.0;
    if (config_.bid_ask_spread_bps > 0.0) {
        double half_spread = quoted_price * (config_.bid_ask_spread_bps / 10000.0) / 2.0;
        spread_adjustment = is_buy ? half_spread : -half_spread;
    }
    
    return quoted_price + slippage + spread_adjustment;
}

double ExecutionSimulator::calculate_commission(double quantity, double price) const {
    double commission = 0.0;
    
    // Per-share commission
    commission += quantity * config_.commission_per_share;
    
    // Percentage-based commission
    if (config_.commission_percentage > 0.0) {
        commission += (quantity * price) * (config_.commission_percentage / 100.0);
    }
    
    return commission;
}

nexus::core::TradeExecutionEvent* ExecutionSimulator::execute_simple_order(
    const nexus::core::TradingSignalEvent& signal,
    double market_price,
    nexus::core::EventPool& pool) {
    
    // Calculate execution price with slippage
    bool is_buy = (signal.signal == nexus::core::TradingSignalEvent::SignalType::BUY);
    double execution_price = calculate_execution_price(market_price, is_buy);
    
    // Simulate partial fills if enabled
    double executed_quantity = signal.suggested_quantity;
    bool is_partial_fill = false;
    
    if (config_.simulate_partial_fills && uniform_dist_(random_generator_) < config_.partial_fill_probability) {
        // Generate a partial fill
        double fill_ratio = config_.min_fill_ratio + 
                           (1.0 - config_.min_fill_ratio) * uniform_dist_(random_generator_);
        executed_quantity = signal.suggested_quantity * fill_ratio;
        is_partial_fill = true;
    }
    
    // Calculate commission
    double commission = calculate_commission(executed_quantity, execution_price);
    
    // Create execution event
    auto* trade_event = pool.create_trade_execution_event();
    trade_event->symbol = signal.symbol;
    trade_event->timestamp = std::chrono::system_clock::now();
    trade_event->quantity = executed_quantity;
    trade_event->price = execution_price;
    trade_event->commission = commission;
    trade_event->is_buy = is_buy;
    
    return trade_event;
}

nexus::core::TradeExecutionEvent* ExecutionSimulator::execute_order_book_order(
    const nexus::core::TradingSignalEvent& signal,
    double market_price,
    nexus::core::EventPool& pool) {
    
    auto order_book_start = get_current_time();
    
    // Get or create order book for this symbol
    LockFreeOrderBook* order_book = get_or_create_order_book(signal.symbol);
    if (!order_book) {
        // Fallback to simple execution if order book creation fails
        return execute_simple_order(signal, market_price, pool);
    }
    
    // Determine order side
    Order::Side side = (signal.signal == nexus::core::TradingSignalEvent::SignalType::BUY) ? 
                       Order::Side::BUY : Order::Side::SELL;
    
    // Execute as market order for immediate execution
    MatchResult match_result = order_book->match_market_order(side, signal.suggested_quantity);
    
    auto order_book_time = calculate_time_diff_ns(order_book_start, get_current_time());
    
    // Update order book statistics
    statistics_.order_book_operations.fetch_add(1, std::memory_order_relaxed);
    
    // Update average order book latency
    double current_avg = statistics_.average_order_book_latency_ns.load(std::memory_order_acquire);
    const double alpha = 0.1;
    double new_avg = (current_avg == 0.0) ? order_book_time : 
                    alpha * order_book_time + (1.0 - alpha) * current_avg;
    statistics_.average_order_book_latency_ns.store(new_avg, std::memory_order_release);
    
    if (match_result.matched_quantity > 0.0) {
        // Calculate commission on executed quantity
        double commission = calculate_commission(match_result.matched_quantity, match_result.average_price);
        
        // Create execution event
        auto* trade_event = pool.create_trade_execution_event();
        trade_event->symbol = signal.symbol;
        trade_event->timestamp = std::chrono::system_clock::now();
        trade_event->quantity = match_result.matched_quantity;
        trade_event->price = match_result.average_price;
        trade_event->commission = commission;
        trade_event->is_buy = (side == Order::Side::BUY);
        
        return trade_event;
    }
    
    // No execution possible - this can happen in realistic scenarios
    return nullptr;
}

LockFreeOrderBook* ExecutionSimulator::get_or_create_order_book(const std::string& symbol) {
    std::lock_guard<std::mutex> lock(order_books_mutex_);
    
    auto it = order_books_.find(symbol);
    if (it != order_books_.end()) {
        return it->second.get();
    }
    
    // Create new order book for this symbol
    LockFreeOrderBook::Config ob_config;
    ob_config.symbol = symbol;
    ob_config.tick_size = config_.tick_size;
    ob_config.market_depth_levels = config_.market_depth_levels;
    ob_config.enable_statistics = config_.enable_order_book_statistics;
    ob_config.auto_cleanup = true;
    
    auto order_book = std::make_unique<LockFreeOrderBook>(ob_config);
    LockFreeOrderBook* result = order_book.get();
    order_books_[symbol] = std::move(order_book);
    
    return result;
}

void ExecutionSimulator::add_market_maker_liquidity(const std::string& symbol, double market_price) {
    LockFreeOrderBook* order_book = get_or_create_order_book(symbol);
    if (!order_book) {
        return;
    }
    
    std::lock_guard<std::mutex> lock(market_maker_mutex_);
    auto& state = market_maker_states_[symbol];
    
    // Check if we should refresh quotes
    auto now = std::chrono::system_clock::now();
    bool should_refresh = false;
    
    if (state.last_quote_time == std::chrono::system_clock::time_point{}) {
        // First time - always add quotes
        should_refresh = true;
    } else {
        // Check refresh probability
        if (uniform_dist_(random_generator_) < config_.market_maker_refresh_rate) {
            should_refresh = true;
        }
    }
    
    if (!should_refresh) {
        return;
    }
    
    // Calculate bid and ask prices
    double half_spread = market_price * (config_.market_maker_spread_bps / 10000.0) / 2.0;
    double bid_price = market_price - half_spread;
    double ask_price = market_price + half_spread;
    
    // Round to tick size
    bid_price = std::floor(bid_price / config_.tick_size) * config_.tick_size;
    ask_price = std::ceil(ask_price / config_.tick_size) * config_.tick_size;
    
    // Add market maker orders
    for (size_t i = 0; i < config_.market_maker_order_count; ++i) {
        // Spread orders around the mid price
        double bid_offset = i * config_.tick_size;
        double ask_offset = i * config_.tick_size;
        
        // Add bid order
        uint64_t bid_order_id = state.next_order_id++;
        if (order_book->add_order(bid_order_id, Order::Side::BUY, 
                                 bid_price - bid_offset, config_.market_maker_quantity)) {
            state.active_bid_orders.push_back(bid_order_id);
            statistics_.market_maker_quotes_added.fetch_add(1, std::memory_order_relaxed);
        }
        
        // Add ask order
        uint64_t ask_order_id = state.next_order_id++;
        if (order_book->add_order(ask_order_id, Order::Side::SELL, 
                                 ask_price + ask_offset, config_.market_maker_quantity)) {
            state.active_ask_orders.push_back(ask_order_id);
            statistics_.market_maker_quotes_added.fetch_add(1, std::memory_order_relaxed);
        }
    }
    
    state.last_quote_time = now;
    state.last_market_price = market_price;
}

void ExecutionSimulator::simulate_execution_latency() const {
    if (!config_.simulate_latency) {
        return;
    }
    
    // Generate random latency between min and max
    auto min_latency = config_.min_execution_latency;
    auto max_latency = config_.max_execution_latency;
    
    if (max_latency <= min_latency) {
        std::this_thread::sleep_for(min_latency);
        return;
    }
    
    // Generate random latency
    auto latency_range = max_latency - min_latency;
    auto random_latency = min_latency + std::chrono::nanoseconds(
        static_cast<long>(uniform_dist_(random_generator_) * latency_range.count())
    );
    
    std::this_thread::sleep_for(random_latency);
}

void ExecutionSimulator::update_statistics(double execution_time_ns, double volume, 
                                          double value, double commission, bool was_partial_fill) {
    statistics_.total_executions.fetch_add(1, std::memory_order_relaxed);
    atomic_add_double(statistics_.total_volume_executed, volume);
    atomic_add_double(statistics_.total_value_executed, value);
    atomic_add_double(statistics_.total_commission_charged, commission);
    
    if (was_partial_fill) {
        statistics_.partial_fills.fetch_add(1, std::memory_order_relaxed);
    } else {
        statistics_.full_fills.fetch_add(1, std::memory_order_relaxed);
    }
    
    // Update execution timing statistics
    statistics_.total_execution_operations.fetch_add(1, std::memory_order_relaxed);
    
    // Update max execution time
    double current_max = statistics_.max_execution_time_ns.load(std::memory_order_acquire);
    while (execution_time_ns > current_max) {
        if (statistics_.max_execution_time_ns.compare_exchange_weak(
            current_max, execution_time_ns, 
            std::memory_order_acq_rel, std::memory_order_acquire)) {
            break;
        }
    }
    
    // Update average execution time using exponential moving average
    double current_avg = statistics_.average_execution_time_ns.load(std::memory_order_acquire);
    const double alpha = 0.1;
    double new_avg = (current_avg == 0.0) ? execution_time_ns : 
                    alpha * execution_time_ns + (1.0 - alpha) * current_avg;
    statistics_.average_execution_time_ns.store(new_avg, std::memory_order_release);
}

} // namespace nexus::execution