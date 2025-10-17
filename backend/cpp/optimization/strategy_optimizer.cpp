// src/cpp/optimization/strategy_optimizer.cpp

#include "optimization/strategy_optimizer.h"
#include "optimization/grid_search.h" // Include the new component
#include "strategies/abstract_strategy.h"
#include <algorithm>
#include <stdexcept>

namespace nexus::optimization {

StrategyOptimizer::StrategyOptimizer(std::unique_ptr<nexus::strategies::AbstractStrategy> strategy_template)
    : strategy_template_(std::move(strategy_template)) {}

std::vector<OptimizationResult> StrategyOptimizer::grid_search(
    const std::unordered_map<std::string, std::vector<double>>& parameter_grid) {
    
    // The optimizer now delegates the complex grid search logic to the
    // standalone function, passing its strategy template.
    // For this example, we hardcode the backtest settings. In a real application,
    // these would be passed in as arguments.
    const double initial_capital = 100000.0;
    const std::string data_filepath = "test_integration_data.csv";
    const std::string symbol = "TEST";

    this->results_ = perform_grid_search(
        *strategy_template_,
        parameter_grid,
        initial_capital,
        data_filepath,
        symbol
    );

    return this->results_;
}

OptimizationResult StrategyOptimizer::get_best_result() const {
    if (results_.empty()) {
        throw std::runtime_error("No optimization results available to determine the best.");
    }

    auto best_it = std::max_element(results_.begin(), results_.end(),
        [](const OptimizationResult& a, const OptimizationResult& b) {
            return a.fitness_score < b.fitness_score;
        });

    return *best_it;
}

} // namespace nexus::optimization