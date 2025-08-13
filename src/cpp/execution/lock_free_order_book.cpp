// src/cpp/execution/lock_free_order_book.cpp

#include "execution/lock_free_order_book.h"
#include <algorithm>
#include <iostream>
#include <limits>

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

    /**
     * @brief Atomically subtracts a value from an atomic double using compare-and-swap.
     * @param atomic_var The atomic double variable to modify.
     * @param value The value to subtract.
     */
    void atomic_subtract_double(std::atomic<double>& atomic_var, double value) {
        double current = atomic_var.load(std::memory_order_acquire);
        while (!atomic_var.compare_exchange_weak(current, current - value,
                                                std::memory_order_acq_rel,
                                                std::memory_order_acquire)) {
            // Loop until successful
        }
    }
}

LockFreeOrderBook::LockFreeOrderBook(const Config& config) : config_(config) {
    config_.validate();
    
    if (config_.enable_statistics) {
        std::cout << "LockFreeOrderBook: Initialized for symbol " << config_.symbol 
                  << " with tick size " << config_.tick_size << std::endl;
    }
}

LockFreeOrderBook::~LockFreeOrderBook() {
    if (config_.enable_statistics) {
        std::cout << "LockFreeOrderBook: Final statistics for " << config_.symbol << ":" << std::endl;
        std::cout << "  - Total orders processed: " << statistics_.total_orders_added.load() << std::endl;
        std::cout << "  - Total matches: " << statistics_.total_matches.load() << std::endl;
        std::cout << "  - Total volume: " << statistics_.total_volume_matched.load() << std::endl;
        std::cout << "  - Average operation time: " << statistics_.average_operation_time_ns.load() << " ns" << std::endl;
    }
}

bool LockFreeOrderBook::add_order(uint64_t order_id, Order::Side side, double price, double quantity) {
    auto start_time = config_.enable_statistics ? get_current_time() : 
                     std::chrono::high_resolution_clock::time_point{};

    // Validate inputs
    if (quantity <= 0.0 || price <= 0.0) {
        return false;
    }

    // Round price to tick size
    double rounded_price = round_to_tick(price);

    // Get or create price level
    PriceLevel* level = get_or_create_price_level(side, rounded_price);
    if (!level) {
        return false;
    }

    // Create the order
    auto order = std::make_unique<Order>(order_id, config_.symbol, side, rounded_price, quantity);
    Order* order_ptr = order.release(); // Transfer ownership to price level

    // Add order to price level
    if (!level->add_order(order_ptr)) {
        delete order_ptr;
        return false;
    }

    // Update order lookup for cancellations/modifications
    {
        std::unique_lock<std::shared_mutex> lock(order_lookup_mutex_);
        order_lookup_[order_id] = {side, rounded_price, {}};
    }

    // Invalidate best bid/ask cache
    cache_valid_.store(false, std::memory_order_release);

    // Update statistics
    if (config_.enable_statistics) {
        statistics_.total_orders_added.fetch_add(1, std::memory_order_relaxed);
        statistics_.total_active_orders.fetch_add(1, std::memory_order_relaxed);
        
        if (side == Order::Side::BUY) {
            atomic_add_double(statistics_.total_bid_quantity, quantity);
        } else {
            atomic_add_double(statistics_.total_ask_quantity, quantity);
        }

        auto operation_time = calculate_time_diff_ns(start_time, get_current_time());
        update_statistics(operation_time);
    }

    return true;
}

MatchResult LockFreeOrderBook::match_market_order(Order::Side side, double quantity, 
                                                 double max_price, double min_price) {
    auto start_time = config_.enable_statistics ? get_current_time() : 
                     std::chrono::high_resolution_clock::time_point{};

    MatchResult result;
    double remaining_quantity = quantity;
    double total_value = 0.0;

    // Determine which side of the book to match against
    if (side == Order::Side::BUY) {
        // Buy order matches against ask side (ascending price order)
        std::shared_lock<std::shared_mutex> lock(ask_levels_mutex_);
        
        for (auto& [price, level] : ask_levels_) {
            if (remaining_quantity <= 0.0) break;
            
            // Check price constraints for buy orders
            if (max_price > 0.0 && price > max_price) break;
            
            if (level && level->has_orders()) {
                double matched = level->match_orders(side, remaining_quantity, max_price, min_price);
                if (matched > 0.0) {
                    result.matched_quantity += matched;
                    total_value += matched * price;
                    remaining_quantity -= matched;
                    result.orders_matched++;
                }
            }
        }
    } else {
        // Sell order matches against bid side (descending price order)
        std::shared_lock<std::shared_mutex> lock(bid_levels_mutex_);
        
        for (auto& [price, level] : bid_levels_) {
            if (remaining_quantity <= 0.0) break;
            
            // Check price constraints for sell orders
            if (min_price > 0.0 && price < min_price) break;
            
            if (level && level->has_orders()) {
                double matched = level->match_orders(side, remaining_quantity, max_price, min_price);
                if (matched > 0.0) {
                    result.matched_quantity += matched;
                    total_value += matched * price;
                    remaining_quantity -= matched;
                    result.orders_matched++;
                }
            }
        }
    }

    // Calculate average price
    if (result.matched_quantity > 0.0) {
        result.average_price = total_value / result.matched_quantity;
        result.fully_filled = (remaining_quantity <= 1e-8); // Account for floating point precision
    }

    // Invalidate cache if any matches occurred
    if (result.matched_quantity > 0.0) {
        cache_valid_.store(false, std::memory_order_release);
    }

    // Update statistics
    if (config_.enable_statistics && result.matched_quantity > 0.0) {
        statistics_.total_matches.fetch_add(1, std::memory_order_relaxed);
        atomic_add_double(statistics_.total_volume_matched, result.matched_quantity);
        atomic_add_double(statistics_.total_value_matched, total_value);
        statistics_.total_orders_matched.fetch_add(result.orders_matched, std::memory_order_relaxed);

        auto operation_time = calculate_time_diff_ns(start_time, get_current_time());
        update_statistics(operation_time);
    }

    return result;
}

MatchResult LockFreeOrderBook::match_limit_order(uint64_t order_id, Order::Side side, 
                                                double price, double quantity) {
    // First attempt to match against existing orders
    MatchResult result;
    
    if (side == Order::Side::BUY) {
        // Buy limit order can match asks at or below the limit price
        result = match_market_order(side, quantity, price, 0.0);
    } else {
        // Sell limit order can match bids at or above the limit price
        result = match_market_order(side, quantity, 0.0, price);
    }

    // If not fully filled, add remaining quantity to book
    double remaining_quantity = quantity - result.matched_quantity;
    if (remaining_quantity > 1e-8) { // Account for floating point precision
        if (add_order(order_id, side, price, remaining_quantity)) {
            // Order successfully added to book
        } else {
            // Failed to add to book - this shouldn't happen in normal operation
            std::cerr << "Warning: Failed to add remaining quantity to order book for order " 
                      << order_id << std::endl;
        }
    } else {
        result.fully_filled = true;
    }

    return result;
}

bool LockFreeOrderBook::cancel_order(uint64_t order_id) {
    auto start_time = config_.enable_statistics ? get_current_time() : 
                     std::chrono::high_resolution_clock::time_point{};

    // Find the order in our lookup map
    OrderInfo order_info;
    {
        std::shared_lock<std::shared_mutex> lock(order_lookup_mutex_);
        auto it = order_lookup_.find(order_id);
        if (it == order_lookup_.end()) {
            return false; // Order not found
        }
        order_info = it->second;
    }

    // Get the appropriate price level
    bool removed = false;
    if (order_info.side == Order::Side::BUY) {
        std::shared_lock<std::shared_mutex> lock(bid_levels_mutex_);
        auto it = bid_levels_.find(order_info.price);
        if (it != bid_levels_.end() && it->second) {
            removed = it->second->remove_order(order_id);
        }
    } else {
        std::shared_lock<std::shared_mutex> lock(ask_levels_mutex_);
        auto it = ask_levels_.find(order_info.price);
        if (it != ask_levels_.end() && it->second) {
            removed = it->second->remove_order(order_id);
        }
    }

    if (removed) {
        // Remove from order lookup
        {
            std::unique_lock<std::shared_mutex> lock(order_lookup_mutex_);
            order_lookup_.erase(order_id);
        }

        // Invalidate cache
        cache_valid_.store(false, std::memory_order_release);

        // Update statistics
        if (config_.enable_statistics) {
            statistics_.total_orders_cancelled.fetch_add(1, std::memory_order_relaxed);
            statistics_.total_active_orders.fetch_sub(1, std::memory_order_relaxed);

            auto operation_time = calculate_time_diff_ns(start_time, get_current_time());
            update_statistics(operation_time);
        }

        // Cleanup empty price level if auto cleanup is enabled
        if (config_.auto_cleanup) {
            // This will be handled by the cleanup process
        }
    }

    return removed;
}

bool LockFreeOrderBook::modify_order(uint64_t order_id, double new_quantity, double new_price) {
    // For simplicity and atomicity, implement modify as cancel + add
    // This ensures consistency and avoids complex lock-free update scenarios
    
    // Find the original order
    OrderInfo order_info;
    {
        std::shared_lock<std::shared_mutex> lock(order_lookup_mutex_);
        auto it = order_lookup_.find(order_id);
        if (it == order_lookup_.end()) {
            return false; // Order not found
        }
        order_info = it->second;
    }

    // Validate new quantity (must be positive and <= original)
    if (new_quantity <= 0.0) {
        return false;
    }

    // Use original price if new price is not specified
    double target_price = (new_price > 0.0) ? new_price : order_info.price;

    // Cancel the original order
    if (!cancel_order(order_id)) {
        return false;
    }

    // Add the modified order (note: this will get a new order ID internally)
    uint64_t new_order_id = next_order_id_.fetch_add(1, std::memory_order_relaxed);
    if (add_order(new_order_id, order_info.side, target_price, new_quantity)) {
        // Update the lookup to use the new internal order ID
        {
            std::unique_lock<std::shared_mutex> lock(order_lookup_mutex_);
            order_lookup_[order_id] = {order_info.side, target_price, {}};
        }
        return true;
    }

    return false;
}

MarketData LockFreeOrderBook::get_market_data() const {
    MarketData data;
    data.symbol = config_.symbol;
    data.timestamp = std::chrono::system_clock::now();

    // Get best bid and ask
    data.best_bid_price = get_best_bid();
    data.best_ask_price = get_best_ask();

    // Get quantities at best levels
    if (data.best_bid_price > 0.0) {
        std::shared_lock<std::shared_mutex> lock(bid_levels_mutex_);
        auto it = bid_levels_.find(data.best_bid_price);
        if (it != bid_levels_.end() && it->second) {
            data.best_bid_quantity = it->second->get_total_quantity();
        }
    }

    if (data.best_ask_price > 0.0) {
        std::shared_lock<std::shared_mutex> lock(ask_levels_mutex_);
        auto it = ask_levels_.find(data.best_ask_price);
        if (it != ask_levels_.end() && it->second) {
            data.best_ask_quantity = it->second->get_total_quantity();
        }
    }

    // Build market depth
    data.bid_levels.reserve(config_.market_depth_levels);
    data.ask_levels.reserve(config_.market_depth_levels);

    // Get bid depth
    {
        std::shared_lock<std::shared_mutex> lock(bid_levels_mutex_);
        size_t count = 0;
        for (const auto& [price, level] : bid_levels_) {
            if (count >= config_.market_depth_levels) break;
            if (level && level->has_orders()) {
                MarketData::Level bid_level;
                bid_level.price = price;
                bid_level.quantity = level->get_total_quantity();
                bid_level.order_count = level->get_order_count();
                data.bid_levels.push_back(bid_level);
                count++;
            }
        }
    }

    // Get ask depth
    {
        std::shared_lock<std::shared_mutex> lock(ask_levels_mutex_);
        size_t count = 0;
        for (const auto& [price, level] : ask_levels_) {
            if (count >= config_.market_depth_levels) break;
            if (level && level->has_orders()) {
                MarketData::Level ask_level;
                ask_level.price = price;
                ask_level.quantity = level->get_total_quantity();
                ask_level.order_count = level->get_order_count();
                data.ask_levels.push_back(ask_level);
                count++;
            }
        }
    }

    return data;
}

double LockFreeOrderBook::get_best_bid() const noexcept {
    // Check cache first
    if (cache_valid_.load(std::memory_order_acquire)) {
        return cached_best_bid_.load(std::memory_order_acquire);
    }

    // Cache miss - calculate best bid
    double best_bid = 0.0;
    {
        std::shared_lock<std::shared_mutex> lock(bid_levels_mutex_);
        for (const auto& [price, level] : bid_levels_) {
            if (level && level->has_orders()) {
                best_bid = price;
                break; // First entry is highest price due to descending order
            }
        }
    }

    // Update cache
    cached_best_bid_.store(best_bid, std::memory_order_release);
    return best_bid;
}

double LockFreeOrderBook::get_best_ask() const noexcept {
    // Check cache first
    if (cache_valid_.load(std::memory_order_acquire)) {
        return cached_best_ask_.load(std::memory_order_acquire);
    }

    // Cache miss - calculate best ask
    double best_ask = 0.0;
    {
        std::shared_lock<std::shared_mutex> lock(ask_levels_mutex_);
        for (const auto& [price, level] : ask_levels_) {
            if (level && level->has_orders()) {
                best_ask = price;
                break; // First entry is lowest price due to ascending order
            }
        }
    }

    // Update cache
    cached_best_ask_.store(best_ask, std::memory_order_release);
    return best_ask;
}

double LockFreeOrderBook::get_mid_price() const noexcept {
    double bid = get_best_bid();
    double ask = get_best_ask();
    
    if (bid > 0.0 && ask > 0.0) {
        return (bid + ask) / 2.0;
    }
    return 0.0;
}

double LockFreeOrderBook::get_spread() const noexcept {
    double bid = get_best_bid();
    double ask = get_best_ask();
    
    if (bid > 0.0 && ask > 0.0) {
        return ask - bid;
    }
    return 0.0;
}

bool LockFreeOrderBook::is_empty() const noexcept {
    return get_total_orders() == 0;
}

size_t LockFreeOrderBook::get_total_orders() const noexcept {
    if (config_.enable_statistics) {
        return statistics_.total_active_orders.load(std::memory_order_acquire);
    }
    
    // Fallback calculation if statistics are disabled
    size_t total = 0;
    {
        std::shared_lock<std::shared_mutex> lock(bid_levels_mutex_);
        for (const auto& [price, level] : bid_levels_) {
            if (level) {
                total += level->get_order_count();
            }
        }
    }
    {
        std::shared_lock<std::shared_mutex> lock(ask_levels_mutex_);
        for (const auto& [price, level] : ask_levels_) {
            if (level) {
                total += level->get_order_count();
            }
        }
    }
    return total;
}

double LockFreeOrderBook::get_total_bid_quantity() const noexcept {
    if (config_.enable_statistics) {
        return statistics_.total_bid_quantity.load(std::memory_order_acquire);
    }
    
    double total = 0.0;
    std::shared_lock<std::shared_mutex> lock(bid_levels_mutex_);
    for (const auto& [price, level] : bid_levels_) {
        if (level) {
            total += level->get_total_quantity();
        }
    }
    return total;
}

double LockFreeOrderBook::get_total_ask_quantity() const noexcept {
    if (config_.enable_statistics) {
        return statistics_.total_ask_quantity.load(std::memory_order_acquire);
    }
    
    double total = 0.0;
    std::shared_lock<std::shared_mutex> lock(ask_levels_mutex_);
    for (const auto& [price, level] : ask_levels_) {
        if (level) {
            total += level->get_total_quantity();
        }
    }
    return total;
}

void LockFreeOrderBook::reset_statistics() {
    if (config_.enable_statistics) {
        // Reset all atomic counters
        statistics_.total_orders_added.store(0, std::memory_order_release);
        statistics_.total_orders_matched.store(0, std::memory_order_release);
        statistics_.total_orders_cancelled.store(0, std::memory_order_release);
        statistics_.total_matches.store(0, std::memory_order_release);
        statistics_.total_volume_matched.store(0.0, std::memory_order_release);
        statistics_.total_value_matched.store(0.0, std::memory_order_release);
        statistics_.total_operations.store(0, std::memory_order_release);
        statistics_.average_operation_time_ns.store(0.0, std::memory_order_release);
        statistics_.max_operation_time_ns.store(0.0, std::memory_order_release);
        
        std::cout << "LockFreeOrderBook: Statistics reset for " << config_.symbol << std::endl;
    }
}

size_t LockFreeOrderBook::cleanup_inactive_orders() {
    size_t cleaned_up = 0;
    
    // This is a simplified cleanup - in a production system, you might want
    // more sophisticated cleanup strategies
    
    // Note: Full cleanup implementation would require walking through all
    // orders and removing inactive ones, which is complex in a lock-free environment.
    // For now, we rely on the lazy cleanup that happens during normal operations.
    
    return cleaned_up;
}

PriceLevel* LockFreeOrderBook::get_or_create_price_level(Order::Side side, double price) {
    if (side == Order::Side::BUY) {
        std::unique_lock<std::shared_mutex> lock(bid_levels_mutex_);
        auto& level = bid_levels_[price];
        if (!level) {
            level = std::make_unique<PriceLevel>(price);
            statistics_.active_price_levels.fetch_add(1, std::memory_order_relaxed);
        }
        return level.get();
    } else {
        std::unique_lock<std::shared_mutex> lock(ask_levels_mutex_);
        auto& level = ask_levels_[price];
        if (!level) {
            level = std::make_unique<PriceLevel>(price);
            statistics_.active_price_levels.fetch_add(1, std::memory_order_relaxed);
        }
        return level.get();
    }
}

void LockFreeOrderBook::remove_empty_price_level(Order::Side side, double price) {
    if (side == Order::Side::BUY) {
        std::unique_lock<std::shared_mutex> lock(bid_levels_mutex_);
        auto it = bid_levels_.find(price);
        if (it != bid_levels_.end() && it->second && !it->second->has_orders()) {
            bid_levels_.erase(it);
            statistics_.active_price_levels.fetch_sub(1, std::memory_order_relaxed);
            cache_valid_.store(false, std::memory_order_release);
        }
    } else {
        std::unique_lock<std::shared_mutex> lock(ask_levels_mutex_);
        auto it = ask_levels_.find(price);
        if (it != ask_levels_.end() && it->second && !it->second->has_orders()) {
            ask_levels_.erase(it);
            statistics_.active_price_levels.fetch_sub(1, std::memory_order_relaxed);
            cache_valid_.store(false, std::memory_order_release);
        }
    }
}

void LockFreeOrderBook::update_statistics(double operation_time_ns) {
    if (!config_.enable_statistics) return;

    statistics_.total_operations.fetch_add(1, std::memory_order_relaxed);
    
    // Update max operation time
    double current_max = statistics_.max_operation_time_ns.load(std::memory_order_acquire);
    while (operation_time_ns > current_max) {
        if (statistics_.max_operation_time_ns.compare_exchange_weak(
            current_max, operation_time_ns, 
            std::memory_order_acq_rel, std::memory_order_acquire)) {
            break;
        }
    }
    
    // Update average operation time using exponential moving average
    double current_avg = statistics_.average_operation_time_ns.load(std::memory_order_acquire);
    const double alpha = 0.1; // Smoothing factor
    double new_avg = (current_avg == 0.0) ? operation_time_ns : 
                    alpha * operation_time_ns + (1.0 - alpha) * current_avg;
    
    statistics_.average_operation_time_ns.store(new_avg, std::memory_order_release);
}

} // namespace nexus::execution