// src/cpp/analytics/performance_analyzer.h

#pragma once

#include "analytics/performance_metrics.h"
#include "core/event_types.h"
#include "core/latency_tracker.h" // NEW: For Phase 3.2 latency tracking
#include <vector>
#include <memory>
#include <unordered_map> // NEW: For latency statistics map

namespace nexus::analytics {

/**
 * @class PerformanceAnalyzer
 * @brief Comprehensive performance analysis and reporting for trading strategies.
 *
 * This class takes the raw results of a backtest (equity curve and trade history)
 * and calculates a wide range of performance metrics. It provides both traditional
 * financial metrics (Sharpe ratio, maximum drawdown) and advanced analytics
 * (risk-adjusted returns, trade analysis) to help evaluate strategy performance.
 *
 * The analyzer is designed to be used after a backtest completes, providing
 * a complete "report card" of how the strategy performed during the simulation.
 */
class PerformanceAnalyzer {
public:
    /**
     * @brief Constructs a PerformanceAnalyzer with backtest results.
     * @param initial_capital The starting capital for the backtest.
     * @param equity_curve A time series of portfolio values throughout the backtest.
     * @param trade_history A complete record of all trades executed during the backtest.
     */
    PerformanceAnalyzer(
        double initial_capital,
        const std::vector<double>& equity_curve,
        const std::vector<nexus::core::TradeExecutionEvent>& trade_history
    );

    /**
     * @brief Default destructor.
     */
    ~PerformanceAnalyzer() = default;

    /**
     * @brief Calculates performance metrics from the provided data.
     * @return Comprehensive performance metrics.
     */
    PerformanceMetrics calculate_metrics();

    // NEW: Phase 3.2 - Latency tracking integration
    
    /**
     * @brief Enables real-time latency tracking for performance optimization.
     * @param enabled Whether to enable latency tracking.
     */
    void enable_latency_tracking(bool enabled = true);
    
    /**
     * @brief Gets the latency tracker for external measurement integration.
     * @return Reference to the internal latency tracker.
     */
    nexus::core::LatencyTracker& get_latency_tracker();
    
    /**
     * @brief Gets comprehensive latency statistics for all tracked operations.
     * @return Map of operation names to their latency statistics.
     */
    std::unordered_map<std::string, nexus::core::LatencyStatistics> get_latency_statistics() const;
    
    /**
     * @brief Adds a latency measurement for a specific operation.
     * @param operation_name Name of the operation (e.g., "signal_generation", "order_execution").
     * @param latency_ns Latency in nanoseconds.
     */
    void record_latency(const std::string& operation_name, double latency_ns);
    
    /**
     * @brief Records end-to-end latency from event timestamps.
     * @param start_event Event marking the start of the operation.
     * @param end_event Event marking the end of the operation.
     * @param operation_name Name of the operation being measured.
     */
    void record_event_latency(const nexus::core::Event& start_event,
                             const nexus::core::Event& end_event,
                             const std::string& operation_name);

private:
    double initial_capital_;
    std::vector<double> equity_curve_;
    std::vector<nexus::core::TradeExecutionEvent> trade_history_;
    
    // NEW: Phase 3.2 - Latency tracking components
    std::unique_ptr<nexus::core::LatencyTracker> latency_tracker_;
    bool latency_tracking_enabled_{false};

    /**
     * @brief Calculates the daily returns from the equity curve.
     * @return Vector of daily returns as percentages.
     */
    std::vector<double> calculate_daily_returns() const;

    /**
     * @brief Calculates the maximum drawdown from the equity curve.
     * @return The maximum peak-to-trough decline as a percentage.
     */
    double calculate_max_drawdown() const;

    /**
     * @brief Calculates trade-related statistics.
     * @param metrics The metrics object to populate with trade statistics.
     */
    void calculate_trade_statistics(PerformanceMetrics& metrics) const;
};

} // namespace nexus::analytics