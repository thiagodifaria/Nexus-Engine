// src/cpp/analytics/risk_metrics.cpp

#include "analytics/risk_metrics.h"
#include <algorithm>
#include <vector>
#include <numeric>
#include <cmath>

namespace nexus::analytics {

double RiskMetrics::calculate_var(
    const std::vector<double>& daily_returns,
    double confidence_level) {
    
    if (daily_returns.empty()) {
        return 0.0;
    }

    // Create a mutable copy to sort.
    std::vector<double> sorted_returns = daily_returns;
    std::sort(sorted_returns.begin(), sorted_returns.end());

    // Calculate the index corresponding to the confidence level.
    // For a 95% confidence level, we are interested in the 5th percentile loss.
    double percentile = 1.0 - confidence_level;
    size_t index = static_cast<size_t>(percentile * sorted_returns.size());

    // Ensure the index is within bounds.
    if (index >= sorted_returns.size()) {
        index = sorted_returns.size() - 1;
    }

    // VaR is the loss at the specified percentile.
    // We return its absolute value by convention.
    return std::fabs(sorted_returns[index]);
}

double RiskMetrics::calculate_cvar(
    const std::vector<double>& daily_returns,
    double confidence_level) {

    if (daily_returns.empty()) {
        return 0.0;
    }

    // Create a mutable copy to sort.
    std::vector<double> sorted_returns = daily_returns;
    std::sort(sorted_returns.begin(), sorted_returns.end());

    // Find the VaR index first.
    double percentile = 1.0 - confidence_level;
    size_t var_index = static_cast<size_t>(percentile * sorted_returns.size());
    
    // Ensure the index is within bounds.
    if (var_index >= sorted_returns.size()) {
        var_index = sorted_returns.size() - 1;
    }

    // CVaR is the average of the returns in the tail of the distribution,
    // from the beginning up to and including the VaR index.
    size_t tail_count = var_index + 1;
    
    // Sum the returns in the tail.
    double tail_sum = std::accumulate(
        sorted_returns.begin(),
        sorted_returns.begin() + tail_count,
        0.0
    );

    double average_tail_loss = tail_sum / tail_count;

    // Return the absolute value of the average loss.
    return std::fabs(average_tail_loss);
}

} // namespace nexus::analytics