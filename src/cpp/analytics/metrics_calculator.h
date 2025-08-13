// src/cpp/analytics/metrics_calculator.h

#pragma once

#include <vector>
#include <string>

namespace nexus::analytics {

/**
 * @class MetricsCalculator
 * @brief A utility class providing specialized, stateless metric calculations.
 *
 * This class serves as a toolbox of static functions for performing focused
 * quantitative calculations. Unlike the PerformanceAnalyzer, which generates a
 * full report from a completed backtest, the MetricsCalculator can be used for
 * on-demand or streaming calculations, such as plotting a drawdown series or
 * calculating a metric over a rolling window.
 */
class MetricsCalculator {
public:
    /**
     * @brief Calculates the Sharpe Ratio over a rolling window of returns.
     * @param daily_returns A vector of daily percentage returns.
     * @param window_size The number of periods in the rolling window.
     * @return A vector containing the rolling Sharpe Ratio at each point in time.
     */
    static std::vector<double> calculate_rolling_sharpe(
        const std::vector<double>& daily_returns,
        int window_size
    );

    /**
     * @brief Calculates a time series of portfolio drawdown values.
     * @param equity_curve A vector of the portfolio's total equity values.
     * @return A vector of the same size as the equity curve, where each value
     * represents the percentage drawdown from the most recent peak at that point.
     */
    static std::vector<double> calculate_drawdown_series(
        const std::vector<double>& equity_curve
    );
};

} // namespace nexus::analytics