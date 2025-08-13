// tests/cpp/test_monte_carlo.cpp

#include "analytics/monte_carlo_simulator.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <string>
#include <unordered_map>
#include <cmath>
#include <numeric>
#include <random>

// --- Test Utilities ---
bool are_doubles_equal(double a, double b, double epsilon = 0.0001) {
    return std::fabs(a - b) < epsilon;
}

// --- Test Cases ---

void test_basic_configuration() {
    std::cout << "Running test: test_basic_configuration..." << std::endl;

    // Setup: Create configuration
    nexus::analytics::MonteCarloSimulator::Config config;
    config.num_simulations = 100;
    config.num_threads = 2;
    config.enable_simd = false; // Keep simple for testing
    config.enable_statistics = true;

    // Action: Create simulator
    nexus::analytics::MonteCarloSimulator simulator(config);

    // Assert: Check configuration was applied
    const auto& stored_config = simulator.get_config();
    assert(stored_config.num_simulations == 100);
    assert(stored_config.num_threads == 2);
    assert(stored_config.enable_statistics == true);

    std::cout << "PASSED" << std::endl;
}

void test_simple_simulation() {
    std::cout << "Running test: test_simple_simulation..." << std::endl;

    // Setup: Create configuration
    nexus::analytics::MonteCarloSimulator::Config config;
    config.num_simulations = 10;
    config.num_threads = 1;
    config.enable_statistics = true;

    nexus::analytics::MonteCarloSimulator simulator(config);

    // Create a simple simulation function that adds random noise
    auto simple_simulation = [](const std::vector<double>& params, std::mt19937& rng) -> std::vector<double> {
        std::normal_distribution<double> dist(0.0, 1.0);
        double result = params.empty() ? 0.0 : params[0];
        result += dist(rng) * 0.1; // Add small random noise
        return {result};
    };

    std::vector<double> initial_params = {100.0}; // Starting value

    // Action: Run simulation
    auto results = simulator.run_simulation(simple_simulation, initial_params);

    // Assert: Check results
    assert(results.size() == 10);
    assert(!results.empty());
    assert(!results[0].empty()); // Each result should have at least one value

    // Check that results are reasonable (around 100 with small variations)
    for (const auto& result : results) {
        assert(!result.empty());
        assert(result[0] > 90.0 && result[0] < 110.0); // Should be close to 100
    }

    std::cout << "PASSED" << std::endl;
}

void test_portfolio_simulation() {
    std::cout << "Running test: test_portfolio_simulation..." << std::endl;

    // Setup
    nexus::analytics::MonteCarloSimulator::Config config;
    config.num_simulations = 50;
    config.num_threads = 1;
    config.enable_statistics = true;

    nexus::analytics::MonteCarloSimulator simulator(config);

    // Create simple portfolio parameters
    std::vector<double> returns = {0.08, 0.06, 0.10}; // 8%, 6%, 10% annual returns
    std::vector<double> volatilities = {0.15, 0.12, 0.20}; // Volatilities
    std::vector<std::vector<double>> correlation_matrix = {
        {1.0, 0.3, 0.2},
        {0.3, 1.0, 0.4},
        {0.2, 0.4, 1.0}
    };
    double time_horizon = 1.0; // 1 year

    // Action: Run portfolio simulation
    auto portfolio_values = simulator.simulate_portfolio(returns, volatilities, correlation_matrix, time_horizon);

    // Assert: Check results
    assert(portfolio_values.size() == 50);

    // All values should be reasonable (portfolio returns)
    for (double value : portfolio_values) {
        assert(value > -1.0 && value < 2.0); // Returns between -100% and +200%
    }

    std::cout << "PASSED" << std::endl;
}

void test_var_calculation() {
    std::cout << "Running test: test_var_calculation..." << std::endl;

    // Setup: Create a simple set of portfolio returns
    std::vector<double> returns = {-0.05, -0.03, -0.01, 0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.08};

    nexus::analytics::MonteCarloSimulator::Config config;
    nexus::analytics::MonteCarloSimulator simulator(config);

    // Action: Calculate VaR
    double var_95 = simulator.calculate_var(returns, 0.95);

    // Assert: VaR should be reasonable
    // With 95% confidence, the worst 5% of outcomes
    // For 10 samples, 5% = 0.5, so we expect around the worst return
    assert(var_95 > 0.04); // Should be positive (loss)
    assert(var_95 < 0.06); // Should be reasonable

    std::cout << "PASSED" << std::endl;
}

void test_statistics_collection() {
    std::cout << "Running test: test_statistics_collection..." << std::endl;

    // Setup
    nexus::analytics::MonteCarloSimulator::Config config;
    config.num_simulations = 20;
    config.enable_statistics = true;

    nexus::analytics::MonteCarloSimulator simulator(config);

    // Simple simulation function
    auto test_simulation = [](const std::vector<double>& params, std::mt19937& rng) -> std::vector<double> {
        std::uniform_real_distribution<double> dist(0.0, 1.0);
        return {dist(rng)};
    };

    // Action: Run simulation and get statistics
    auto results = simulator.run_simulation(test_simulation, {});
    auto stats = simulator.get_statistics();

    // Assert: Statistics should be collected
    assert(stats.total_simulations == 20);
    assert(stats.throughput_per_second > 0.0);

    std::cout << "PASSED" << std::endl;
}

// --- Main Test Runner ---
int main() {
    std::cout << "--- Starting Monte Carlo Simulator Unit Tests ---" << std::endl;
    
    try {
        test_basic_configuration();
        test_simple_simulation();
        test_portfolio_simulation();
        test_var_calculation();
        test_statistics_collection();
    } catch (const std::exception& e) {
        std::cerr << "Test failed with exception: " << e.what() << std::endl;
        return 1;
    }
    
    std::cout << "\nAll Monte Carlo Simulator tests passed!" << std::endl;
    return 0;
}