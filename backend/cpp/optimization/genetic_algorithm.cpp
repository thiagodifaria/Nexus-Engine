// src/cpp/optimization/genetic_algorithm.cpp

#include "optimization/genetic_algorithm.h"
#include "strategies/abstract_strategy.h"
#include "analytics/performance_analyzer.h"
#include "core/backtest_engine.h"
#include "core/event_queue.h"
#include "data/market_data_handler.h"
#include "execution/execution_simulator.h"
#include "position/position_manager.h"

#include <iostream>
#include <random>
#include <algorithm>
#include <vector>
#include <chrono>

namespace nexus::optimization {

namespace { // Anonymous namespace for helper functions

    struct Individual {
        std::unordered_map<std::string, double> parameters;
        double fitness = -1.0;
    };

    void evaluate_fitness(
        Individual& individual,
        const nexus::strategies::AbstractStrategy& strategy_template,
        double initial_capital,
        const std::string& data_filepath,
        const std::string& symbol) {

        if (individual.fitness != -1.0) return;

        auto strategy = strategy_template.clone();
        for (const auto& param : individual.parameters) {
            strategy->set_parameter(param.first, param.second);
        }

        nexus::core::EventQueue event_queue;
        auto position_manager = std::make_shared<nexus::position::PositionManager>(initial_capital);
        auto execution_simulator = std::make_shared<nexus::execution::ExecutionSimulator>(nexus::execution::MarketSimulationConfig{});
        
        // --- CORRECTED for multi-asset ---
        std::unordered_map<std::string, std::string> symbol_filepaths = {{symbol, data_filepath}};
        auto data_handler = std::make_shared<nexus::data::CsvDataHandler>(event_queue, symbol_filepaths);
        
        std::unordered_map<std::string, std::shared_ptr<nexus::strategies::AbstractStrategy>> strategies = {{symbol, std::move(strategy)}};

        nexus::core::BacktestEngine engine(event_queue, data_handler, strategies, position_manager, execution_simulator);
        engine.run();

        nexus::analytics::PerformanceAnalyzer analyzer(
            initial_capital,
            position_manager->get_equity_curve(),
            position_manager->get_trade_history()
        );
        auto metrics = analyzer.calculate_metrics();
        individual.fitness = metrics.sharpe_ratio;
    }
    
    // other helpers (initialize_population, select_parent, crossover, mutate) remain the same...

    std::vector<Individual> initialize_population(
        int population_size,
        const std::unordered_map<std::string, std::pair<double, double>>& parameter_bounds,
        std::mt19937& rng) {
        
        std::vector<Individual> population;
        population.reserve(population_size);

        for (int i = 0; i < population_size; ++i) {
            Individual individual;
            for (const auto& pair : parameter_bounds) {
                const std::string& name = pair.first;
                const double min_val = pair.second.first;
                const double max_val = pair.second.second;
                std::uniform_real_distribution<double> dist(min_val, max_val);
                individual.parameters[name] = dist(rng);
            }
            population.push_back(individual);
        }
        return population;
    }

    const Individual& select_parent(const std::vector<Individual>& population, std::mt19937& rng) {
        const int tournament_size = 5;
        std::uniform_int_distribution<int> dist(0, population.size() - 1);
        
        const Individual* best = &population[dist(rng)];
        for (int i = 1; i < tournament_size; ++i) {
            const Individual& contender = population[dist(rng)];
            if (contender.fitness > best->fitness) {
                best = &contender;
            }
        }
        return *best;
    }

    Individual crossover(const Individual& parent1, const Individual& parent2, std::mt19937& rng) {
        Individual child;
        std::uniform_real_distribution<double> dist(0.0, 1.0);
        for (const auto& param_pair : parent1.parameters) {
            const std::string& name = param_pair.first;
            child.parameters[name] = (dist(rng) < 0.5) ? parent1.parameters.at(name) : parent2.parameters.at(name);
        }
        return child;
    }

    void mutate(Individual& individual, double mutation_rate,
                const std::unordered_map<std::string, std::pair<double, double>>& parameter_bounds,
                std::mt19937& rng) {
        std::uniform_real_distribution<double> rate_dist(0.0, 1.0);
        for (auto& param_pair : individual.parameters) {
            if (rate_dist(rng) < mutation_rate) {
                const auto& bounds = parameter_bounds.at(param_pair.first);
                std::uniform_real_distribution<double> value_dist(bounds.first, bounds.second);
                param_pair.second = value_dist(rng);
            }
        }
    }

} // end anonymous namespace

std::vector<OptimizationResult> perform_genetic_algorithm(
    const nexus::strategies::AbstractStrategy& strategy_template,
    const std::unordered_map<std::string, std::pair<double, double>>& parameter_bounds,
    int population_size,
    int generations,
    double mutation_rate,
    double crossover_rate,
    double initial_capital,
    const std::string& data_filepath,
    const std::string& symbol) {

    std::mt19937 rng(std::chrono::steady_clock::now().time_since_epoch().count());
    std::vector<Individual> population = initialize_population(population_size, parameter_bounds, rng);

    for (int g = 0; g < generations; ++g) {
        std::cout << "\n--- Evolving Generation " << g + 1 << "/" << generations << " ---" << std::endl;
        for (auto& individual : population) {
            evaluate_fitness(individual, strategy_template, initial_capital, data_filepath, symbol);
        }

        std::sort(population.begin(), population.end(), [](const auto& a, const auto& b) {
            return a.fitness > b.fitness;
        });
        
        std::cout << "Best fitness in generation " << g + 1 << ": " << population.front().fitness << std::endl;

        std::vector<Individual> next_generation;
        next_generation.reserve(population_size);

        int elitism_count = std::max(1, static_cast<int>(population_size * 0.1));
        for (int i = 0; i < elitism_count; ++i) {
            next_generation.push_back(population[i]);
        }
        
        std::uniform_real_distribution<double> cross_dist(0.0, 1.0);
        while (next_generation.size() < population_size) {
            const Individual& parent1 = select_parent(population, rng);
            const Individual& parent2 = select_parent(population, rng);
            
            Individual child = (cross_dist(rng) < crossover_rate) ? crossover(parent1, parent2, rng) : parent1;
            mutate(child, mutation_rate, parameter_bounds, rng);
            next_generation.push_back(child);
        }
        population = next_generation;
    }

    for (auto& individual : population) {
        evaluate_fitness(individual, strategy_template, initial_capital, data_filepath, symbol);
    }

    std::vector<OptimizationResult> final_results;
    for (const auto& individual : population) {
        OptimizationResult res;
        res.parameters = individual.parameters;
        res.fitness_score = individual.fitness;
        final_results.push_back(res);
    }
    
    return final_results;
}

} // namespace nexus::optimization