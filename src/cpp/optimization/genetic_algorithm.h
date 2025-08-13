// src/cpp/optimization/genetic_algorithm.h

#pragma once

#include "optimization/strategy_optimizer.h" // For OptimizationResult
#include <vector>
#include <string>
#include <unordered_map>
#include <utility> // For std::pair
#include <memory>

// Forward declarations
namespace nexus::strategies {
    class AbstractStrategy;
}

namespace nexus::optimization {

/**
 * @brief Performs a genetic algorithm optimization to find optimal strategy parameters.
 *
 * This function uses an evolutionary approach to search the parameter space. It
 * starts with a random population of parameter sets, evaluates their fitness
 * through backtesting, and iteratively evolves the population over several
 * generations using selection, crossover, and mutation to find high-performing
 * parameter configurations.
 *
 * @param strategy_template A const reference to the strategy to be cloned for each run.
 * @param parameter_bounds A map where each key is a parameter name and the value
 * is a std::pair<double, double> representing the min and
 * max bounds for that parameter.
 * @param population_size The number of individuals (parameter sets) in each generation.
 * @param generations The total number of generations to evolve the population.
 * @param mutation_rate The probability (0.0 to 1.0) that a parameter will be
 * randomly mutated.
 * @param crossover_rate The probability (0.0 to 1.0) that two parent individuals
 * will combine to create offspring.
 * @param initial_capital The starting capital for each backtest.
 * @param data_filepath The path to the historical data CSV file.
 * @param symbol The symbol for the historical data.
 * @return A vector of OptimizationResult structs for all individuals in the final,
 * most evolved generation.
 */
std::vector<OptimizationResult> perform_genetic_algorithm(
    const nexus::strategies::AbstractStrategy& strategy_template,
    const std::unordered_map<std::string, std::pair<double, double>>& parameter_bounds,
    int population_size,
    int generations,
    double mutation_rate,
    double crossover_rate,
    double initial_capital,
    const std::string& data_filepath,
    const std::string& symbol
);

} // namespace nexus::optimization