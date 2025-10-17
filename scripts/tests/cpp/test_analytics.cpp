// tests/cpp/test_analytics.cpp

#include "analytics/performance_analyzer.h"
#include "analytics/risk_metrics.h"
#include "core/event_types.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <cmath>

// --- Test Utilities ---
bool are_doubles_equal(double a, double b, double epsilon = 0.0001) {
    return std::fabs(a - b) < epsilon;
}

// --- Test Cases ---

void test_risk_metrics() {
    std::cout << "Running test: test_risk_metrics..." << std::endl;

    // Setup
    std::vector<double> returns = { -0.03, -0.02, -0.01, 0.01, 0.02 }; // Already sorted for clarity

    // Action & Assert: VaR
    // With 80% confidence, we expect the loss not to exceed the 20th percentile value.
    // For 5 elements, the 20th percentile is the first element (index 0).
    double var = nexus::analytics::RiskMetrics::calculate_var(returns, 0.80);
    assert(are_doubles_equal(var, 0.03));

    // Action & Assert: CVaR
    // CVaR is the average of the losses in the tail. The tail here is just {-0.03}.
    double cvar = nexus::analytics::RiskMetrics::calculate_cvar(returns, 0.80);
    assert(are_doubles_equal(cvar, 0.03));

    std::cout << "PASSED" << std::endl;
}

void test_performance_analyzer() {
    std::cout << "Running test: test_performance_analyzer..." << std::endl;

    // Setup
    double initial_capital = 100000.0;
    std::vector<double> equity_curve = {100000, 110000, 105000, 120000};
    std::vector<nexus::core::TradeExecutionEvent> trade_history; // Empty for this test

    nexus::analytics::PerformanceAnalyzer analyzer(initial_capital, equity_curve, trade_history);

    // Action
    auto metrics = analyzer.calculate_metrics();

    // Assert
    // Total return = (120000 / 100000) - 1 = 0.20
    assert(are_doubles_equal(metrics.total_return, 0.20));

    // Max Drawdown: Peak is 110000, subsequent trough is 105000.
    // Drawdown = (110000 - 105000) / 110000 = 0.04545
    double expected_max_dd = (110000.0 - 105000.0) / 110000.0;
    assert(are_doubles_equal(metrics.max_drawdown, expected_max_dd));

    std::cout << "PASSED" << std::endl;
}

// --- Main Test Runner ---
int main() {
    std::cout << "--- Starting Analytics Module Unit Tests ---" << std::endl;
    test_risk_metrics();
    test_performance_analyzer();
    std::cout << "\nAll Analytics tests passed!" << std::endl;
    return 0;
}