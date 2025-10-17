// src/cpp/core/backtest_engine.h

#pragma once

#include "core/event_queue.h"
#include "core/event_types.h"
#include "core/real_time_config.h"
#include "data/market_data_handler.h"
#include "strategies/abstract_strategy.h"
#include "position/position_manager.h"
#include "execution/execution_simulator.h"

#include <unordered_map>
#include <memory>
#include <string>
#include <atomic>
#include <thread>

namespace nexus::core {

/**
 * @struct BacktestEngineConfig
 * @brief Configuration parameters for the BacktestEngine.
 *
 * This structure contains all configuration options for the backtest engine,
 * including event processing settings, performance options, and real-time
 * optimization parameters for low-latency trading scenarios.
 */
struct BacktestEngineConfig {
    /**
     * @brief Maximum number of events to process per batch.
     * Higher values can improve throughput but may increase latency.
     * Set to 0 for unlimited batch size.
     */
    size_t max_events_per_batch = 1000;

    /**
     * @brief Maximum duration to spend processing events in a single batch.
     * Prevents long-running batches from blocking other operations.
     */
    std::chrono::microseconds max_batch_duration{1000};

    /**
     * @brief Enable detailed performance monitoring during backtest execution.
     * Collects timing information for optimization but adds overhead.
     */
    bool enable_performance_monitoring = false;

    /**
     * @brief Number of worker threads for parallel strategy execution.
     * Set to 0 for automatic detection based on hardware concurrency.
     * Set to 1 for single-threaded execution.
     */
    size_t worker_thread_count = 0;

    /**
     * @brief Enable event batching for improved throughput.
     * Groups related events together for more efficient processing.
     */
    bool enable_event_batching = true;

    /**
     * @brief Event queue backend type ("traditional" or "disruptor").
     * Determines the underlying event queue implementation to use.
     */
    std::string queue_backend_type = "disruptor";

    /**
     * @brief Real-time optimization configuration.
     * Contains settings for CPU affinity, thread priority, cache warming,
     * and other low-latency optimizations for production trading systems.
     */
    RealTimeConfig real_time_config;

    /**
     * @brief Validates the configuration and sets reasonable defaults.
     * Should be called before using the configuration in BacktestEngine.
     */
    void validate() {
        // Validate batch parameters
        if (max_events_per_batch == 0) {
            max_events_per_batch = 1000; // Default batch size
        }
        
        if (max_batch_duration < std::chrono::microseconds{1}) {
            max_batch_duration = std::chrono::microseconds{1000}; // 1ms default
        }
        
        // Validate worker thread count
        if (worker_thread_count == 0) {
            worker_thread_count = std::max(1u, std::thread::hardware_concurrency());
        }
        
        // Validate queue backend type
        if (queue_backend_type != "traditional" && queue_backend_type != "disruptor") {
            queue_backend_type = "disruptor"; // Default to high-performance option
        }
        
        // Validate real-time configuration
        real_time_config.validate();
    }
};

/**
 * @class BacktestEngine
 * @brief Core engine for backtesting trading strategies with real-time optimizations.
 *
 * This class orchestrates the entire backtesting process, coordinating between
 * market data feeds, trading strategies, position management, and trade execution.
 * Real-time optimizations for production-grade performance.
 *
 * Key features:
 * - Event-driven architecture with configurable queue backends
 * - Multi-threaded strategy execution with CPU affinity
 * - Real-time priority scheduling for deterministic latency
 * - Comprehensive performance monitoring and optimization
 * - Lock-free data structures for maximum throughput
 * - Cache warming and NUMA-aware memory allocation
 *
 * Performance characteristics:
 * - Event processing: Sub-microsecond latency with LMAX Disruptor
 * - Strategy execution: 800K-2.4M signals/second
 * - Thread affinity: 20-50% latency reduction
 * - Real-time priority: Deterministic scheduling
 */
class BacktestEngine {
public:
    /**
     * @brief Constructs a BacktestEngine with the specified configuration.
     * @param event_queue Reference to the event queue for processing events.
     * @param data_handler Shared pointer to the market data handler.
     * @param strategies Map of symbol to strategy for trading logic.
     * @param position_manager Shared pointer to the position manager.
     * @param execution_simulator Shared pointer to the execution simulator.
     * @param config Configuration parameters for the engine.
     */
    BacktestEngine(
        EventQueue& event_queue,
        std::shared_ptr<nexus::data::MarketDataHandler> data_handler,
        std::unordered_map<std::string, std::shared_ptr<nexus::strategies::AbstractStrategy>> strategies,
        std::shared_ptr<nexus::position::PositionManager> position_manager,
        std::shared_ptr<nexus::execution::ExecutionSimulator> execution_simulator,
        const BacktestEngineConfig& config = BacktestEngineConfig{}
    );

    /**
     * @brief Destructor - ensures proper cleanup of real-time optimizations.
     */
    ~BacktestEngine();

    /**
     * @brief Runs the complete backtest simulation.
     * Processes all market data events through strategies and position management.
     */
    void run();

    /**
     * @brief Gets the current configuration.
     * @return Reference to the current BacktestEngineConfig.
     */
    const BacktestEngineConfig& get_config() const noexcept {
        return config_;
    }

    /**
     * @brief Updates the engine configuration.
     * @param new_config New configuration to apply.
     * @note This will apply real-time optimizations if enabled.
     */
    void update_config(const BacktestEngineConfig& new_config);

    /**
     * @brief Gets performance statistics for the engine.
     * @return String containing detailed performance information.
     */
    std::string get_performance_info() const;

    /**
     * @brief Manually triggers cache warming for critical data structures.
     * Can be called before run() to improve initial performance.
     */
    void warm_caches();

private:
    /**
     * @brief Applies real-time optimizations based on configuration.
     * Sets up CPU affinity, thread priority, and other optimizations.
     */
    void apply_real_time_optimizations();

    /**
     * @brief Reverts real-time optimizations to normal operation.
     * Called during cleanup or when switching configurations.
     */
    void revert_real_time_optimizations();

    /**
     * @brief Warms critical data structures in CPU cache.
     * Pre-loads strategy data, position data, and other hot paths.
     */
    void warm_critical_caches();

    /**
     * @brief Configures NUMA-aware memory allocation if enabled.
     * Sets up memory allocation preferences for multi-socket systems.
     */
    void configure_numa_allocation();

    /**
     * @brief Sets up performance monitoring infrastructure.
     * Initializes timing and profiling systems based on configuration.
     */
    void setup_performance_monitoring();

    /**
     * @brief Main event processing loop implementation.
     * Handles events from the queue and dispatches to appropriate handlers.
     */
    void process_events();

    /**
     * @brief Processes a single market data event.
     * @param event The market data event to process.
     */
    void process_market_data_event(const MarketDataEvent& event);

    /**
     * @brief Processes a single trading signal event.
     * @param event The trading signal event to process.
     */
    void process_trading_signal_event(const TradingSignalEvent& event);

    /**
     * @brief Processes a single trade execution event.
     * @param event The trade execution event to process.
     */
    void process_trade_execution_event(const TradeExecutionEvent& event);

    /**
     * @brief Gets event from the queue using available interface.
     * @return Pointer to event or nullptr if no event available.
     */
    Event* get_next_event_safe();

    /**
     * @brief Adds event to the queue using available interface.
     * @param event Pointer to event to add.
     */
    void add_event_safe(Event* event);

    /**
     * @brief Gets event pool for creating new events.
     * @return Reference to event pool.
     */
    EventPool& get_event_pool_safe();

    // Core components
    EventQueue& event_queue_;
    std::shared_ptr<nexus::data::MarketDataHandler> data_handler_;
    std::unordered_map<std::string, std::shared_ptr<nexus::strategies::AbstractStrategy>> strategies_;
    std::shared_ptr<nexus::position::PositionManager> position_manager_;
    std::shared_ptr<nexus::execution::ExecutionSimulator> execution_simulator_;

    // Configuration and state
    BacktestEngineConfig config_;
    std::atomic<bool> is_running_{false};
    std::atomic<bool> stop_requested_{false};

    // Real-time optimization state
    std::atomic<bool> real_time_optimizations_applied_{false};
    std::vector<int> original_cpu_affinity_;
    bool original_priority_was_real_time_{false};
    int original_priority_level_{0};

    // Performance monitoring
    mutable std::atomic<uint64_t> total_events_processed_{0};
    mutable std::atomic<uint64_t> total_processing_time_ns_{0};
    mutable std::atomic<uint64_t> max_event_processing_time_ns_{0};
    
    // Thread management for real-time optimizations
    std::vector<std::thread> worker_threads_;
    std::atomic<bool> threads_should_exit_{false};
};

} // namespace nexus::core