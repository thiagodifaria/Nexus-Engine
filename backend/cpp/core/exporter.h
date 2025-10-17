// src/cpp/core/exporter.h

#pragma once

#include <string>
#include <vector>

// Forward declaration for PerformanceMetrics in its own, correct namespace.
namespace nexus::analytics {
    struct PerformanceMetrics;
}

// All definitions for this module belong in the core namespace.
namespace nexus::core {

// Forward declaration for the TradeExecutionEvent struct, which is in this namespace.
struct TradeExecutionEvent;

/**
 * @class Exporter
 * @brief A stateless utility class for serializing analysis results to CSV files.
 *
 * This class provides a set of static methods to write the output of the
 * backtesting and analysis engines to disk in a simple, universally readable
 * format. This decouples the C++ core from any specific visualization tool.
 */
class Exporter {
public:
    /**
     * @brief Exports a summary of performance metrics to a CSV file.
     * @param metrics A const reference to the PerformanceMetrics struct to be exported.
     * @param filepath The destination file path for the CSV output.
     * @return True on successful export, false otherwise.
     */
    static bool export_performance_metrics_to_csv(
        const nexus::analytics::PerformanceMetrics& metrics,
        const std::string& filepath
    );

    /**
     * @brief Exports a portfolio's equity curve time series to a CSV file.
     * @param equity_curve A const reference to a vector of equity values.
     * @param filepath The destination file path for the CSV output.
     * @return True on successful export, false otherwise.
     */
    static bool export_equity_curve_to_csv(
        const std::vector<double>& equity_curve,
        const std::string& filepath
    );

    /**
     * @brief Exports a detailed history of all executed trades to a CSV file.
     * @param trade_history A const reference to a vector of TradeExecutionEvent objects.
     * @param filepath The destination file path for the CSV output.
     * @return True on successful export, false otherwise.
     */
    static bool export_trade_history_to_csv(
        const std::vector<TradeExecutionEvent>& trade_history,
        const std::string& filepath
    );
};

} // namespace nexus::core