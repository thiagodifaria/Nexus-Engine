// src/cpp/analytics/risk_metrics.h

#pragma once

#include <vector>
#include <string>

namespace nexus::analytics {

/**
 * @class RiskMetrics
 * @brief A utility class providing specialized, stateless financial risk calculations.
 *
 * This class serves as a toolbox of static functions for performing advanced
 * risk assessments that are essential for understanding a strategy's potential
 * downside. These calculations are distinct from the general performance
 * metrics and provide a deeper view into tail risk.
 */
class RiskMetrics {
public:
    /**
     * @brief Calculates the historical Value at Risk (VaR).
     *
     * VaR is a statistical measure that estimates the potential financial loss
     * of a portfolio over a specific time frame for a given confidence level.
     * A VaR of $100 at 95% confidence means there is a 5% chance of losing
     * at least $100 on any given day.
     *
     * @param daily_returns A vector of daily percentage returns.
     * @param confidence_level The confidence level for the calculation (e.g., 0.95 for 95%).
     * @return The Value at Risk as a positive number representing a loss.
     */
    static double calculate_var(
        const std::vector<double>& daily_returns,
        double confidence_level
    );

    /**
     * @brief Calculates the historical Conditional Value at Risk (CVaR) or Expected Shortfall.
     *
     * CVaR is a more sensitive risk measure than VaR. It answers the question:
     * "If things do go bad (i.e., we exceed the VaR loss), what is our expected
     * average loss?" It is calculated by taking the average of all losses in
     * the tail of the distribution beyond the VaR cutoff point.
     *
     * @param daily_returns A vector of daily percentage returns.
     * @param confidence_level The confidence level for the calculation (e.g., 0.95 for 95%).
     * @return The Conditional Value at Risk as a positive number representing a loss.
     */
    static double calculate_cvar(
        const std::vector<double>& daily_returns,
        double confidence_level
    );
};

} // namespace nexus::analytics