// src/cpp/optimization/grid_search.h

#pragma once

#include "optimization/strategy_optimizer.h" // For OptimizationResult
#include <vector>
#include <string>
#include <unordered_map>
#include <memory>

// Forward declarations
namespace nexus::strategies {
    class AbstractStrategy;
}

namespace nexus::optimization {

/**
 * @brief Performs a grid search optimization for a given strategy template.
 * @param strategy_template A const reference to the strategy to be cloned for each run.
 * @param parameter_grid A map defining the parameter values to test.
 * @param initial_capital The starting capital for each backtest.
 * @param data_filepath The path to the historical data CSV file.
 * @param symbol The symbol for the historical data.
 * @return A vector of OptimizationResult structs containing the outcome of each run.
 */
std::vector<OptimizationResult> perform_grid_search(
    const nexus::strategies::AbstractStrategy& strategy_template,
    const std::unordered_map<std::string, std::vector<double>>& parameter_grid,
    double initial_capital,
    const std::string& data_filepath,
    const std::string& symbol
);

} // namespace nexus::optimization