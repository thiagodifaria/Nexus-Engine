// src/cpp/analytics/metrics_calculator.cpp

#include "analytics/metrics_calculator.h"
#include <numeric>
#include <cmath>
#include <algorithm>
#include <stdexcept>

namespace nexus::analytics {

std::vector<double> MetricsCalculator::calculate_rolling_sharpe(
    const std::vector<double>& daily_returns,
    int window_size) {
    
    if (daily_returns.size() < window_size || window_size <= 1) {
        // Not enough data to calculate a rolling metric, return empty.
        return {};
    }

    std::vector<double> rolling_sharpe_ratios;
    rolling_sharpe_ratios.reserve(daily_returns.size() - window_size + 1);

    // Iterate through the daily returns, calculating the metric for each window.
    for (size_t i = window_size; i <= daily_returns.size(); ++i) {
        // Get the current window of returns.
        auto window_start = daily_returns.begin() + i - window_size;
        auto window_end = daily_returns.begin() + i;

        // 1. Calculate the mean return for the window.
        double sum = std::accumulate(window_start, window_end, 0.0);
        double mean = sum / window_size;

        // 2. Calculate the standard deviation for the window.
        double sq_sum = std::accumulate(window_start, window_end, 0.0,
            [mean](double acc, double r) { return acc + std::pow(r - mean, 2); });
        
        double variance = sq_sum / (window_size - 1);
        double std_dev = std::sqrt(variance);

        // 3. Calculate and annualize the Sharpe Ratio.
        // Assuming risk-free rate is 0.
        if (std_dev > 0) {
            // Annualized Sharpe = (MeanDailyReturn / StdDevDailyReturn) * sqrt(252)
            double sharpe = (mean / std_dev) * std::sqrt(252.0);
            rolling_sharpe_ratios.push_back(sharpe);
        } else {
            // If there is no volatility, Sharpe Ratio is undefined or can be considered 0.
            rolling_sharpe_ratios.push_back(0.0);
        }
    }

    return rolling_sharpe_ratios;
}

std::vector<double> MetricsCalculator::calculate_drawdown_series(
    const std::vector<double>& equity_curve) {

    if (equity_curve.empty()) {
        return {};
    }

    std::vector<double> drawdown_series;
    drawdown_series.reserve(equity_curve.size());

    double peak = -1.0; // Initialize peak to a value that will be immediately replaced.

    for (const double& equity : equity_curve) {
        // Update the peak if a new high is reached.
        if (equity > peak) {
            peak = equity;
        }

        // Calculate drawdown from the current peak.
        if (peak > 0) {
            double drawdown = (peak - equity) / peak;
            drawdown_series.push_back(drawdown);
        } else {
            // Handle case where peak is zero or negative.
            drawdown_series.push_back(0.0);
        }
    }

    return drawdown_series;
}

} // namespace nexus::analytics