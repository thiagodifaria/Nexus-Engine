// src/cpp/execution/execution_simulator.h

#pragma once

#include "core/event_types.h"
#include "core/event_pool.h"
#include "execution/lock_free_order_book.h"
#include <random>
#include <memory>
#include <unordered_map>
#include <string>
#include <atomic>
#include <chrono>
#include <mutex>

namespace nexus::execution {

/**
 * @struct MarketSimulationConfig
 * @brief Configuration for realistic market simulation with order book support.
 */
struct MarketSimulationConfig {
    // Traditional execution parameters
    double commission_per_share{0.005};
    double commission_percentage{0.0};
    double bid_ask_spread_bps{1.0};
    double slippage_factor{0.0001};
    
    // Lock-free order book configuration
    bool use_order_book{false};                    // Enable realistic order book simulation
    double tick_size{0.01};                        // Minimum price increment
    size_t market_depth_levels{5};                 // Depth levels for market data
    bool enable_order_book_statistics{false};     // Enable detailed order book statistics
    
    // Market making simulation
    bool enable_market_making{false};              // Add liquidity via market makers
    double market_maker_spread_bps{2.0};           // Market maker spread
    size_t market_maker_order_count{10};           // Orders per side from market makers
    double market_maker_quantity{100.0};           // Quantity per market maker order
    double market_maker_refresh_rate{0.1};         // Probability of refreshing quotes per event
    
    // Latency simulation
    bool simulate_latency{false};                  // Add realistic execution latency
    std::chrono::nanoseconds min_execution_latency{100};    // Minimum execution time
    std::chrono::nanoseconds max_execution_latency{1000};   // Maximum execution time
    
    // Advanced market simulation
    bool simulate_partial_fills{false};           // Enable partial fill simulation
    double partial_fill_probability{0.1};         // Probability of partial fills
    double min_fill_ratio{0.3};                   // Minimum fill ratio for partial fills
    
    /**
     * @brief Validates and adjusts configuration parameters.
     */
    void validate() {
        if (commission_per_share < 0.0) commission_per_share = 0.0;
        if (commission_percentage < 0.0) commission_percentage = 0.0;
        if (bid_ask_spread_bps < 0.0) bid_ask_spread_bps = 0.0;
        if (slippage_factor < 0.0) slippage_factor = 0.0;
        if (tick_size <= 0.0) tick_size = 0.01;
        if (market_depth_levels == 0) market_depth_levels = 5;
        if (market_maker_spread_bps < bid_ask_spread_bps) market_maker_spread_bps = bid_ask_spread_bps * 2.0;
        if (market_maker_quantity <= 0.0) market_maker_quantity = 100.0;
        if (market_maker_refresh_rate < 0.0) market_maker_refresh_rate = 0.0;
        if (market_maker_refresh_rate > 1.0) market_maker_refresh_rate = 1.0;
        if (partial_fill_probability < 0.0) partial_fill_probability = 0.0;
        if (partial_fill_probability > 1.0) partial_fill_probability = 1.0;
        if (min_fill_ratio <= 0.0 || min_fill_ratio > 1.0) min_fill_ratio = 0.3;
    }
};

/**
 * @struct ExecutionStatistics
 * @brief Performance and execution statistics for the simulator.
 */
struct ExecutionStatistics {
    // Execution counts
    std::atomic<uint64_t> total_executions{0};
    std::atomic<uint64_t> market_orders_executed{0};
    std::atomic<uint64_t> limit_orders_executed{0};
    std::atomic<uint64_t> partial_fills{0};
    std::atomic<uint64_t> full_fills{0};
    
    // Volume and value
    std::atomic<double> total_volume_executed{0.0};
    std::atomic<double> total_value_executed{0.0};
    std::atomic<double> total_commission_charged{0.0};
    
    // Timing statistics
    std::atomic<double> average_execution_time_ns{0.0};
    std::atomic<double> max_execution_time_ns{0.0};
    std::atomic<uint64_t> total_execution_operations{0};
    
    // Order book statistics (when enabled)
    std::atomic<uint64_t> order_book_operations{0};
    std::atomic<double> average_order_book_latency_ns{0.0};
    
    // Market making statistics
    std::atomic<uint64_t> market_maker_quotes_added{0};
    std::atomic<uint64_t> market_maker_fills{0};
    std::atomic<double> market_maker_pnl{0.0};
};

/**
 * @class ExecutionSimulator
 * @brief Advanced execution simulator with realistic order book simulation.
 *
 * This execution simulator provides multiple execution models:
 * 1. Simple slippage-based execution (original behavior)
 * 2. Realistic order book simulation with market makers
 * 3. Partial fill simulation
 * 4. Latency simulation for realistic timing
 *
 * The simulator maintains backward compatibility while offering advanced
 * features for realistic backtesting scenarios.
 *
 * Key features:
 * - Lock-free order book integration for realistic market simulation
 * - Configurable market making to provide liquidity
 * - Partial fill simulation for realistic execution
 * - Latency simulation for timing accuracy
 * - Comprehensive execution statistics
 * - Thread-safe operation for concurrent access
 *
 * Performance characteristics:
 * - Simple mode: 1M+ executions/second
 * - Order book mode: 100K+ executions/second with realistic market dynamics
 * - Latency simulation: Configurable execution delays
 */
class ExecutionSimulator {
public:
    /**
     * @brief Constructs an execution simulator with default configuration.
     */
    ExecutionSimulator() : ExecutionSimulator(MarketSimulationConfig{}) {}

    /**
     * @brief Constructs an execution simulator with custom configuration.
     * @param config Configuration parameters for execution simulation.
     */
    explicit ExecutionSimulator(const MarketSimulationConfig& config);

    /**
     * @brief Destructor - ensures proper cleanup and statistics reporting.
     */
    ~ExecutionSimulator();

    /**
     * @brief Updates the simulation configuration.
     * @param new_config New configuration parameters.
     * @note This will reset order books and statistics.
     */
    void update_config(const MarketSimulationConfig& new_config);

    /**
     * @brief Simulates the execution of a trading signal.
     * @param signal The trading signal to execute.
     * @param current_market_price The current market price for the symbol.
     * @param pool Event pool for creating execution events.
     * @return Pointer to the trade execution event, or nullptr if execution failed.
     */
    nexus::core::TradeExecutionEvent* simulate_order_execution(
        const nexus::core::TradingSignalEvent& signal,
        double current_market_price,
        nexus::core::EventPool& pool
    );

    /**
     * @brief Updates market data for order book simulation.
     * @param symbol The symbol to update.
     * @param market_price The current market price.
     * @param volume Recent trading volume (for market making decisions).
     */
    void update_market_data(const std::string& symbol, double market_price, double volume = 0.0);

    /**
     * @brief Gets current market data for a symbol.
     * @param symbol The symbol to query.
     * @return MarketData structure with current order book state.
     * @note Only available when order book simulation is enabled.
     */
    MarketData get_market_data(const std::string& symbol) const;

    /**
     * @brief Gets execution statistics.
     * @return Statistics structure with performance metrics.
     */
    const ExecutionStatistics& get_statistics() const noexcept {
        return statistics_;
    }

    /**
     * @brief Resets all execution statistics.
     */
    void reset_statistics();

    /**
     * @brief Gets the current configuration.
     * @return The configuration used by this simulator.
     */
    const MarketSimulationConfig& get_config() const noexcept {
        return config_;
    }

    /**
     * @brief Checks if order book simulation is enabled.
     * @return True if using realistic order book simulation.
     */
    bool is_using_order_book() const noexcept {
        return config_.use_order_book;
    }

    /**
     * @brief Gets the number of active order books.
     * @return Count of symbols with active order books.
     */
    size_t get_active_order_book_count() const;

    /**
     * @brief Performs cleanup of inactive orders across all order books.
     * @return Total number of orders cleaned up.
     */
    size_t cleanup_order_books();

private:
    /**
     * @brief Calculates execution price using simple slippage model.
     * @param quoted_price The current market price.
     * @param is_buy True for buy orders, false for sell orders.
     * @return The execution price including slippage.
     */
    double calculate_execution_price(double quoted_price, bool is_buy) const;

    /**
     * @brief Calculates commission for a trade.
     * @param quantity The trade quantity.
     * @param price The execution price.
     * @return The total commission amount.
     */
    double calculate_commission(double quantity, double price) const;

    /**
     * @brief Executes an order using simple slippage model.
     * @param signal The trading signal.
     * @param market_price The current market price.
     * @param pool Event pool for creating events.
     * @return Execution event or nullptr.
     */
    nexus::core::TradeExecutionEvent* execute_simple_order(
        const nexus::core::TradingSignalEvent& signal,
        double market_price,
        nexus::core::EventPool& pool
    );

    /**
     * @brief Executes an order using order book simulation.
     * @param signal The trading signal.
     * @param market_price The current market price.
     * @param pool Event pool for creating events.
     * @return Execution event or nullptr.
     */
    nexus::core::TradeExecutionEvent* execute_order_book_order(
        const nexus::core::TradingSignalEvent& signal,
        double market_price,
        nexus::core::EventPool& pool
    );

    /**
     * @brief Gets or creates an order book for a symbol.
     * @param symbol The symbol to get/create order book for.
     * @return Pointer to the order book, or nullptr if creation failed.
     */
    LockFreeOrderBook* get_or_create_order_book(const std::string& symbol);

    /**
     * @brief Adds market maker liquidity to an order book.
     * @param symbol The symbol to add liquidity for.
     * @param market_price The current market price.
     */
    void add_market_maker_liquidity(const std::string& symbol, double market_price);

    /**
     * @brief Simulates execution latency if enabled.
     */
    void simulate_execution_latency() const;

    /**
     * @brief Updates execution statistics.
     * @param execution_time_ns Time taken for execution in nanoseconds.
     * @param volume Volume executed.
     * @param value Value executed.
     * @param commission Commission charged.
     * @param was_partial_fill Whether this was a partial fill.
     */
    void update_statistics(double execution_time_ns, double volume, double value, 
                          double commission, bool was_partial_fill);

    /**
     * @brief High-resolution timing for performance measurement.
     */
    std::chrono::high_resolution_clock::time_point get_current_time() const noexcept {
        return std::chrono::high_resolution_clock::now();
    }

    /**
     * @brief Calculates time difference in nanoseconds.
     */
    double calculate_time_diff_ns(
        const std::chrono::high_resolution_clock::time_point& start,
        const std::chrono::high_resolution_clock::time_point& end) const noexcept {
        auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end - start);
        return static_cast<double>(duration.count());
    }

    // Configuration
    MarketSimulationConfig config_;

    // Order books for realistic simulation (symbol -> order book)
    mutable std::mutex order_books_mutex_;
    std::unordered_map<std::string, std::unique_ptr<LockFreeOrderBook>> order_books_;

    // Random number generation for various simulation aspects
    mutable std::mt19937 random_generator_;
    mutable std::uniform_real_distribution<double> uniform_dist_{0.0, 1.0};

    // Market maker state tracking
    struct MarketMakerState {
        uint64_t next_order_id{1};
        std::chrono::system_clock::time_point last_quote_time;
        double last_market_price{0.0};
        std::vector<uint64_t> active_bid_orders;
        std::vector<uint64_t> active_ask_orders;
    };
    
    mutable std::mutex market_maker_mutex_;
    std::unordered_map<std::string, MarketMakerState> market_maker_states_;

    // Performance statistics
    mutable ExecutionStatistics statistics_;
    mutable std::mutex statistics_mutex_;
};

} // namespace nexus::execution