// src/cpp/optimization/strategy_optimizer.h

#pragma once

#include <vector>
#include <string>
#include <unordered_map>
#include <memory>
#include "analytics/performance_metrics.h"

// Forward declaration for the strategy interface.
namespace nexus::strategies {
    class AbstractStrategy;
}

namespace nexus::optimization {

/**
 * @struct OptimizationResult
 * @brief Links a specific set of parameters to its backtest performance outcome.
 *
 * This struct is a container that holds the results of a single backtest run
 * within a larger optimization process. It stores the parameters used, the
* full performance report, and a single fitness score for easy ranking.
 */
struct OptimizationResult {
    /**
     * @brief The parameter set used for this specific backtest run.
     * Example: {"short_window": 10.0, "long_window": 20.0}
     */
    std::unordered_map<std::string, double> parameters;

    /**
     * @brief The complete performance metrics "report card" for this run.
     */
    nexus::analytics::PerformanceMetrics performance;

    /**
     * @brief A single, objective score used to rank this result against others.
     * This is typically a key metric from the performance report, such as the
     * Sharpe Ratio or total return, chosen as the optimization target.
     */
    double fitness_score{0.0};
};

/**
 * @class StrategyOptimizer
 * @brief An engine for automatically tuning trading strategy parameters.
 *
 * This class orchestrates the process of running a strategy through numerous
 * backtests, each with a different set of parameters, to find the optimal
 * configuration based on a specified performance metric.
 */
class StrategyOptimizer {
public:
    /**
     * @brief Constructs the optimizer with a strategy to be used as a template.
     * @param strategy_template A unique_ptr to an instance of a strategy. The
     * optimizer takes ownership and will create copies of it for each test run.
     */
    explicit StrategyOptimizer(std::unique_ptr<nexus::strategies::AbstractStrategy> strategy_template);

    /**
     * @brief Default destructor.
     */
    ~StrategyOptimizer() = default;

    /**
     * @brief Performs a grid search optimization.
     *
     * This method systematically iterates through every possible combination of
     * the provided parameter values, runs a backtest for each combination, and
     * stores the results.
     *
     * @param parameter_grid A map where each key is a parameter name and the
     * value is a vector of the parameter values to test.
     * @return A vector of OptimizationResult structs, one for each backtest run.
     */
    std::vector<OptimizationResult> grid_search(
        const std::unordered_map<std::string, std::vector<double>>& parameter_grid
    );

    /**
     * @brief Retrieves the best result from the last optimization run.
     * "Best" is determined by the highest fitness_score.
     * @return The OptimizationResult with the highest fitness score.
     */
    OptimizationResult get_best_result() const;

private:
    /**
     * @brief A template instance of the strategy to be optimized.
     * For each run, the optimizer will create a copy of this template,
     * apply a new set of parameters, and run the backtest.
     */
    std::unique_ptr<nexus::strategies::AbstractStrategy> strategy_template_;

    /**
     * @brief Stores the results of the last optimization run.
     */
    std::vector<OptimizationResult> results_;
};

} // namespace nexus::optimization