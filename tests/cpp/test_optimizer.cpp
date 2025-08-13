// tests/cpp/test_optimizer.cpp

#include "optimization/strategy_optimizer.h"
#include "strategies/sma_strategy.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <string>
#include <unordered_map>
#include <memory>
#include <fstream> // For creating dummy data file

// --- Test Cases ---

void test_grid_search_orchestration() {
    std::cout << "Running test: test_grid_search_orchestration..." << std::endl;

    // Setup: Create a dummy data file for the optimizer to use.
    // The optimizer's backtest runs need this file to exist.
    const std::string csv_filename = "test_integration_data.csv";
    {
        std::ofstream csv_file(csv_filename);
        csv_file << "Timestamp,Open,High,Low,Close,Volume\n"
                 << "2025-01-01 09:30:00,100,100,100,100,1000\n"
                 << "2025-01-02 09:30:00,101,101,101,101,1000\n";
    }

    // 1. Create a strategy template
    auto strategy_template = std::make_unique<nexus::strategies::SmaCrossoverStrategy>(10, 20);

    // 2. Create the optimizer
    nexus::optimization::StrategyOptimizer optimizer(std::move(strategy_template));

    // 3. Define a parameter grid
    // This grid should result in 2 (short windows) * 1 (long window) = 2 total runs.
    std::unordered_map<std::string, std::vector<double>> parameter_grid = {
        {"short_window", {10.0, 20.0}},
        {"long_window", {50.0}}
    };

    // 4. Action: Run the grid search
    // Note: This will print the backtest output to the console.
    std::vector<nexus::optimization::OptimizationResult> results = optimizer.grid_search(parameter_grid);

    // 5. Assert: Check that the correct number of backtests were run.
    assert(results.size() == 2);
    std::cout << "Grid search correctly ran " << results.size() << " backtests." << std::endl;

    // Cleanup
    std::remove(csv_filename.c_str());

    std::cout << "PASSED" << std::endl;
}


// --- Main Test Runner ---
int main() {
    std::cout << "--- Starting Optimizer Module Unit Tests ---" << std::endl;
    test_grid_search_orchestration();
    std::cout << "\nAll Optimizer tests passed!" << std::endl;
    return 0;
}