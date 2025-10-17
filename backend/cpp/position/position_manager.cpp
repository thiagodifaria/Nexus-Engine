// src/cpp/position/position_manager.cpp

#include "position/position_manager.h"
#include <numeric>
#include <stdexcept>
#include <iostream>
#include <algorithm>

namespace nexus::position {

PositionManager::PositionManager(double initial_capital)
    : initial_capital_(initial_capital) {
    // Initialize portfolio statistics
    portfolio_stats_.available_cash.store(initial_capital, std::memory_order_release);
    portfolio_stats_.total_equity.store(initial_capital, std::memory_order_release);
    cached_total_equity_.store(initial_capital, std::memory_order_release);
    equity_cache_valid_.store(true, std::memory_order_release);
    
    // Initialize equity curve with starting capital
    equity_curve_.push_back(initial_capital);
    
    std::cout << "PositionManager: Initialized with capital: $" << initial_capital << std::endl;
}

PositionManager::~PositionManager() {
    if (performance_monitoring_enabled_.load()) {
        std::cout << "PositionManager: Final statistics:" << std::endl;
        auto stats = get_portfolio_statistics();
        std::cout << "  - Total updates: " << stats.total_updates << std::endl;
        std::cout << "  - Average update time: " << stats.average_update_time_ns << " ns" << std::endl;
        std::cout << "  - Final equity: $" << stats.total_equity << std::endl;
        std::cout << "  - Total P&L: $" << stats.total_pnl << std::endl;
    }
}

void PositionManager::on_market_data(const nexus::core::MarketDataEvent& event) {
    auto start_time = performance_monitoring_enabled_.load() ? get_current_time() : 
                     std::chrono::high_resolution_clock::time_point{};

    // PERFORMANCE IMPROVEMENT: Position existence check is likely to succeed for active symbols
    bool position_updated = false;
    {
        std::shared_lock<std::shared_mutex> lock(positions_mutex_);
        auto it = positions_.find(event.symbol);
        if (it != positions_.end()) [[likely]] {
            // Get old market value before update
            double old_market_value = it->second.get_market_value();
            
            // Update position price and P&L atomically
            it->second.update_pnl(event.close);
            
            // Get new market value after update
            double new_market_value = it->second.get_market_value();
            
            // Update portfolio statistics atomically
            if (std::abs(new_market_value - old_market_value) > 1e-8) {
                double market_value_change = new_market_value - old_market_value;
                PortfolioStatistics::atomic_add_double(portfolio_stats_.total_market_value, market_value_change);
                PortfolioStatistics::atomic_add_double(portfolio_stats_.total_equity, market_value_change);
                
                // Invalidate equity cache
                equity_cache_valid_.store(false, std::memory_order_release);
            }
            
            position_updated = true;
        }
    }
    
    // Add equity snapshot to curve (done outside lock for performance)
    if (position_updated) [[likely]] {
        double current_equity = get_total_equity();
        {
            std::unique_lock<std::shared_mutex> lock(history_mutex_);
            equity_curve_.push_back(current_equity);
        }
    }

    // Update performance statistics if monitoring is enabled
    if (performance_monitoring_enabled_.load() && position_updated) {
        auto operation_time = calculate_time_diff_ns(start_time, get_current_time());
        update_performance_statistics(operation_time);
    }
}

void PositionManager::on_trade_execution(const nexus::core::TradeExecutionEvent& event) {
    auto start_time = performance_monitoring_enabled_.load() ? get_current_time() : 
                     std::chrono::high_resolution_clock::time_point{};

    // Record trade in history first
    {
        std::unique_lock<std::shared_mutex> lock(history_mutex_);
        trade_history_.push_back(event);
    }

    // Update cash position atomically
    const double direction = event.is_buy ? -1.0 : 1.0;
    const double trade_value = event.quantity * event.price;
    const double cash_change = (direction * trade_value) - event.commission;
    
    PortfolioStatistics::atomic_add_double(portfolio_stats_.available_cash, cash_change);

    // Update position using lock-free operations
    update_position_on_fill_lockfree(event);

    // Update performance statistics if monitoring is enabled
    if (performance_monitoring_enabled_.load()) {
        auto operation_time = calculate_time_diff_ns(start_time, get_current_time());
        update_performance_statistics(operation_time);
    }
}

double PositionManager::get_available_cash() const noexcept {
    return portfolio_stats_.available_cash.load(std::memory_order_acquire);
}

Position PositionManager::get_position_snapshot(const std::string& symbol) const {
    std::shared_lock<std::shared_mutex> lock(positions_mutex_);
    auto it = positions_.find(symbol);
    
    // PERFORMANCE IMPROVEMENT: Position lookup is likely to succeed for active symbols
    if (it != positions_.end()) [[likely]] {
        return it->second.get_snapshot();
    }
    
    // PERFORMANCE IMPROVEMENT: Position not found is the exceptional case
    throw std::out_of_range("Position not found for symbol: " + symbol);
}

std::vector<Position> PositionManager::get_all_positions() const {
    std::shared_lock<std::shared_mutex> lock(positions_mutex_);
    std::vector<Position> all_positions;
    all_positions.reserve(positions_.size());
    
    for (const auto& pair : positions_) {
        all_positions.push_back(pair.second.get_snapshot());
    }
    
    return all_positions;
}

std::vector<double> PositionManager::get_equity_curve() const {
    std::shared_lock<std::shared_mutex> lock(history_mutex_);
    return equity_curve_;
}

std::vector<nexus::core::TradeExecutionEvent> PositionManager::get_trade_history() const {
    std::shared_lock<std::shared_mutex> lock(history_mutex_);
    return trade_history_;
}

double PositionManager::get_total_unrealized_pnl() const noexcept {
    return portfolio_stats_.total_unrealized_pnl.load(std::memory_order_acquire);
}

double PositionManager::get_total_realized_pnl() const noexcept {
    return portfolio_stats_.total_realized_pnl.load(std::memory_order_acquire);
}

double PositionManager::get_total_pnl() const noexcept {
    return portfolio_stats_.total_pnl.load(std::memory_order_acquire);
}

double PositionManager::get_total_equity() const noexcept {
    // Check cache first for fast access
    if (equity_cache_valid_.load(std::memory_order_acquire)) [[likely]] {
        return cached_total_equity_.load(std::memory_order_acquire);
    }
    
    // Cache miss - calculate and update cache
    double total_equity = portfolio_stats_.total_equity.load(std::memory_order_acquire);
    cached_total_equity_.store(total_equity, std::memory_order_release);
    equity_cache_valid_.store(true, std::memory_order_release);
    
    return total_equity;
}

double PositionManager::get_total_market_value() const noexcept {
    return portfolio_stats_.total_market_value.load(std::memory_order_acquire);
}

size_t PositionManager::get_position_count() const noexcept {
    return portfolio_stats_.total_positions.load(std::memory_order_acquire);
}

size_t PositionManager::get_long_position_count() const noexcept {
    return portfolio_stats_.long_positions.load(std::memory_order_acquire);
}

size_t PositionManager::get_short_position_count() const noexcept {
    return portfolio_stats_.short_positions.load(std::memory_order_acquire);
}

bool PositionManager::has_position(const std::string& symbol) const {
    std::shared_lock<std::shared_mutex> lock(positions_mutex_);
    auto it = positions_.find(symbol);
    return it != positions_.end() && !it->second.is_flat();
}

PortfolioStatistics::Snapshot PositionManager::get_portfolio_statistics() const {
    // Get atomic snapshot
    auto snapshot = portfolio_stats_.get_snapshot();
    
    // Calculate derived metrics that aren't stored atomically
    snapshot.total_pnl = snapshot.total_realized_pnl + snapshot.total_unrealized_pnl;
    
    return snapshot;
}

void PositionManager::reset_statistics() {
    portfolio_stats_.total_updates.store(0, std::memory_order_release);
    portfolio_stats_.average_update_time_ns.store(0.0, std::memory_order_release);
    portfolio_stats_.max_update_time_ns.store(0.0, std::memory_order_release);
    
    std::cout << "PositionManager: Performance statistics reset" << std::endl;
}

void PositionManager::recalculate_portfolio_totals() {
    std::shared_lock<std::shared_mutex> lock(positions_mutex_);
    
    double total_market_value = 0.0;
    double total_unrealized_pnl = 0.0;
    double total_realized_pnl = 0.0;
    size_t total_positions = 0;
    size_t long_positions = 0;
    size_t short_positions = 0;
    
    for (const auto& pair : positions_) {
        const Position& pos = pair.second;
        if (!pos.is_flat()) {
            total_market_value += pos.get_market_value();
            total_unrealized_pnl += pos.get_unrealized_pnl();
            total_realized_pnl += pos.get_realized_pnl();
            total_positions++;
            
            if (pos.is_long()) {
                long_positions++;
            } else if (pos.is_short()) {
                short_positions++;
            }
        }
    }
    
    // Update atomic statistics
    portfolio_stats_.total_market_value.store(total_market_value, std::memory_order_release);
    portfolio_stats_.total_unrealized_pnl.store(total_unrealized_pnl, std::memory_order_release);
    portfolio_stats_.total_realized_pnl.store(total_realized_pnl, std::memory_order_release);
    portfolio_stats_.total_pnl.store(total_realized_pnl + total_unrealized_pnl, std::memory_order_release);
    portfolio_stats_.total_positions.store(total_positions, std::memory_order_release);
    portfolio_stats_.long_positions.store(long_positions, std::memory_order_release);
    portfolio_stats_.short_positions.store(short_positions, std::memory_order_release);
    
    // Update total equity
    double available_cash = portfolio_stats_.available_cash.load(std::memory_order_acquire);
    double total_equity = available_cash + total_market_value;
    portfolio_stats_.total_equity.store(total_equity, std::memory_order_release);
    
    // Update cache
    cached_total_equity_.store(total_equity, std::memory_order_release);
    equity_cache_valid_.store(true, std::memory_order_release);
}

void PositionManager::update_position_on_fill_lockfree(const nexus::core::TradeExecutionEvent& event) {
    const double direction = event.is_buy ? 1.0 : -1.0;
    const double trade_quantity = event.quantity * direction;
    
    // Get old position state for statistics update
    double old_market_value = 0.0;
    double old_unrealized_pnl = 0.0;
    double old_realized_pnl = 0.0;
    bool position_existed = false;
    bool was_long = false;
    bool was_short = false;
    
    {
        std::shared_lock<std::shared_mutex> lock(positions_mutex_);
        auto it = positions_.find(event.symbol);
        if (it != positions_.end()) {
            position_existed = true;
            old_market_value = it->second.get_market_value();
            old_unrealized_pnl = it->second.get_unrealized_pnl();
            old_realized_pnl = it->second.get_realized_pnl();
            was_long = it->second.is_long();
            was_short = it->second.is_short();
        }
    }
    
    // Update position atomically
    Position& position = get_or_create_position(event.symbol);
    double realized_pnl_from_trade = position.adjust_position(trade_quantity, event.price);
    
    // Get new position state
    double new_market_value = position.get_market_value();
    double new_unrealized_pnl = position.get_unrealized_pnl();
    double new_realized_pnl = position.get_realized_pnl();
    bool is_now_long = position.is_long();
    bool is_now_short = position.is_short();
    bool is_now_flat = position.is_flat();
    
    // Update portfolio statistics atomically
    update_portfolio_statistics(event.symbol, old_market_value, new_market_value, realized_pnl_from_trade);
    
    // Update position count statistics
    if (!position_existed && !is_now_flat) {
        // New position created
        portfolio_stats_.total_positions.fetch_add(1, std::memory_order_acq_rel);
        if (is_now_long) {
            portfolio_stats_.long_positions.fetch_add(1, std::memory_order_acq_rel);
        } else if (is_now_short) {
            portfolio_stats_.short_positions.fetch_add(1, std::memory_order_acq_rel);
        }
    } else if (position_existed && is_now_flat) {
        // Position closed
        portfolio_stats_.total_positions.fetch_sub(1, std::memory_order_acq_rel);
        if (was_long) {
            portfolio_stats_.long_positions.fetch_sub(1, std::memory_order_acq_rel);
        } else if (was_short) {
            portfolio_stats_.short_positions.fetch_sub(1, std::memory_order_acq_rel);
        }
        
        // Remove flat position from map
        remove_flat_position(event.symbol);
    } else if (position_existed) {
        // Position direction changed
        if (was_long && is_now_short) {
            portfolio_stats_.long_positions.fetch_sub(1, std::memory_order_acq_rel);
            portfolio_stats_.short_positions.fetch_add(1, std::memory_order_acq_rel);
        } else if (was_short && is_now_long) {
            portfolio_stats_.short_positions.fetch_sub(1, std::memory_order_acq_rel);
            portfolio_stats_.long_positions.fetch_add(1, std::memory_order_acq_rel);
        }
    }
    
    // Update P&L statistics
    double unrealized_pnl_change = new_unrealized_pnl - old_unrealized_pnl;
    double realized_pnl_change = new_realized_pnl - old_realized_pnl;
    
    if (std::abs(unrealized_pnl_change) > 1e-8) {
        PortfolioStatistics::atomic_add_double(portfolio_stats_.total_unrealized_pnl, unrealized_pnl_change);
    }
    
    if (std::abs(realized_pnl_change) > 1e-8) {
        PortfolioStatistics::atomic_add_double(portfolio_stats_.total_realized_pnl, realized_pnl_change);
    }
    
    // Update total equity
    double market_value_change = new_market_value - old_market_value;
    if (std::abs(market_value_change) > 1e-8) {
        PortfolioStatistics::atomic_add_double(portfolio_stats_.total_equity, market_value_change);
        equity_cache_valid_.store(false, std::memory_order_release);
    }
}

void PositionManager::update_portfolio_statistics(const std::string& symbol,
                                                 double old_position_value,
                                                 double new_position_value,
                                                 double realized_pnl_change) {
    // Update market value change
    double market_value_change = new_position_value - old_position_value;
    if (std::abs(market_value_change) > 1e-8) {
        PortfolioStatistics::atomic_add_double(portfolio_stats_.total_market_value, market_value_change);
    }
    
    // Update realized P&L
    if (std::abs(realized_pnl_change) > 1e-8) {
        PortfolioStatistics::atomic_add_double(portfolio_stats_.total_realized_pnl, realized_pnl_change);
    }
    
    // Invalidate equity cache for recalculation
    equity_cache_valid_.store(false, std::memory_order_release);
}

void PositionManager::update_performance_statistics(double operation_time_ns) {
    portfolio_stats_.total_updates.fetch_add(1, std::memory_order_acq_rel);
    
    // Update max operation time
    double current_max = portfolio_stats_.max_update_time_ns.load(std::memory_order_acquire);
    while (operation_time_ns > current_max) {
        if (portfolio_stats_.max_update_time_ns.compare_exchange_weak(
            current_max, operation_time_ns,
            std::memory_order_acq_rel, std::memory_order_acquire)) {
            break;
        }
    }
    
    // Update average operation time using exponential moving average
    double current_avg = portfolio_stats_.average_update_time_ns.load(std::memory_order_acquire);
    const double alpha = 0.1; // Smoothing factor
    double new_avg = (current_avg == 0.0) ? operation_time_ns :
                    alpha * operation_time_ns + (1.0 - alpha) * current_avg;
    portfolio_stats_.average_update_time_ns.store(new_avg, std::memory_order_release);
}

Position& PositionManager::get_or_create_position(const std::string& symbol) {
    // Try to find existing position with shared lock first
    {
        std::shared_lock<std::shared_mutex> lock(positions_mutex_);
        auto it = positions_.find(symbol);
        if (it != positions_.end()) [[likely]] {
            return it->second;
        }
    }
    
    // Position doesn't exist, create it with exclusive lock
    std::unique_lock<std::shared_mutex> lock(positions_mutex_);
    
    // Double-check after acquiring exclusive lock (might have been created by another thread)
    auto it = positions_.find(symbol);
    if (it != positions_.end()) [[unlikely]] {
        return it->second;
    }
    
    // Create new position
    auto [inserted_it, success] = positions_.emplace(symbol, Position(symbol, 0.0, 0.0));
    return inserted_it->second;
}

bool PositionManager::remove_flat_position(const std::string& symbol) {
    std::unique_lock<std::shared_mutex> lock(positions_mutex_);
    auto it = positions_.find(symbol);
    
    if (it != positions_.end() && it->second.is_flat()) [[likely]] {
        positions_.erase(it);
        return true;
    }
    
    return false;
}

} // namespace nexus::position