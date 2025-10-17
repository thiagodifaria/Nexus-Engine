// src/cpp/optimization/grid_search.cpp

#include "optimization/grid_search.h"
#include "strategies/abstract_strategy.h"
#include "analytics/performance_analyzer.h"
#include "core/backtest_engine.h"
#include "core/event_queue.h"
#include "data/market_data_handler.h"
#include "execution/execution_simulator.h"
#include "position/position_manager.h"
#include <iostream>
#include <functional>

namespace nexus::optimization {

std::vector<OptimizationResult> perform_grid_search(
    const nexus::strategies::AbstractStrategy& strategy_template,
    const std::unordered_map<std::string, std::vector<double>>& parameter_grid,
    double initial_capital,
    const std::string& data_filepath,
    const std::string& symbol) {
    
    std::vector<OptimizationResult> all_results;
    std::vector<std::pair<std::string, std::vector<double>>> grid_vec(
        parameter_grid.begin(), parameter_grid.end());
    
    std::function<void(int, std::unordered_map<std::string, double>)> generate_combinations =
        [&](int k, std::unordered_map<std::string, double> current_params) {
        if (k == grid_vec.size()) {
            std::cout << "\n--- Running Backtest for Parameters: ---\n";
            for(const auto& p : current_params) {
                std::cout << p.first << ": " << p.second << "\n";
            }

            auto strategy = strategy_template.clone();
            for(const auto& p : current_params) {
                strategy->set_parameter(p.first, p.second);
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

            OptimizationResult result;
            result.parameters = current_params;
            result.performance = metrics;
            result.fitness_score = metrics.sharpe_ratio;
            all_results.push_back(result);

            return;
        }

        const auto& param_name = grid_vec[k].first;
        const auto& param_values = grid_vec[k].second;
        for (double val : param_values) {
            current_params[param_name] = val;
            generate_combinations(k + 1, current_params);
        }
    };

    generate_combinations(0, {});
    return all_results;
}

} // namespace nexus::optimization