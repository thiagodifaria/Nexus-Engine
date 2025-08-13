// tests/cpp/test_multi_asset_integration.cpp

#include "core/backtest_engine.h"
#include "core/event_queue.h"
#include "data/market_data_handler.h"
#include "execution/execution_simulator.h"
#include "position/position_manager.h"
#include "strategies/sma_strategy.h"

#include <iostream>
#include <fstream>
#include <cassert>
#include <vector>
#include <string>
#include <memory>
#include <unordered_map>
#include <cstdio> // For std::remove

// --- Test Utilities ---
void create_dummy_csv(const std::string& filepath, const std::vector<std::string>& data) {
    std::ofstream file(filepath);
    file << "Timestamp,Open,High,Low,Close,Volume\n";
    for (const auto& line : data) {
        file << line << "\n";
    }
}

bool are_doubles_equal(double a, double b, double epsilon = 0.01) {
    return std::fabs(a - b) < epsilon;
}


// --- Main Test Runner ---
int main() {
    std::cout << "--- Starting Multi-Asset Integration Test ---" << std::endl;

    // 1. Create Dummy CSV files
    const std::string aapl_path = "test_aapl.csv";
    const std::string goog_path = "test_goog.csv";

    // AAPL data designed to trigger a BUY signal
    create_dummy_csv(aapl_path, {
        "2023-01-01 09:30:00,100,100,100,100,1000",
        "2023-01-01 09:31:00,101,101,101,101,1000",
        "2023-01-01 09:32:00,102,102,102,102,1000",
        "2023-01-01 09:33:00,103,103,103,103,1000",
        "2023-01-01 09:34:00,104,104,104,104,1000" // BUY signal should trigger here
    });

    // GOOG data designed to trigger a SELL signal
    create_dummy_csv(goog_path, {
        "2023-01-01 09:30:00,200,200,200,200,1000",
        "2023-01-01 09:31:00,199,199,199,199,1000",
        "2023-01-01 09:32:00,198,198,198,198,1000",
        "2023-01-01 09:33:00,197,197,197,197,1000",
        "2023-01-01 09:34:00,196,196,196,196,1000" // SELL signal should trigger here
    });

    // 2. Instantiate Components
    nexus::core::EventQueue event_queue;
    auto position_manager = std::make_shared<nexus::position::PositionManager>(100000.0);
    auto execution_simulator = std::make_shared<nexus::execution::ExecutionSimulator>(nexus::execution::MarketSimulationConfig{});

    std::unordered_map<std::string, std::string> symbol_filepaths = {
        {"AAPL", aapl_path},
        {"GOOG", goog_path}
    };
    auto data_handler = std::make_shared<nexus::data::CsvDataHandler>(event_queue, symbol_filepaths);

    std::unordered_map<std::string, std::shared_ptr<nexus::strategies::AbstractStrategy>> strategies = {
        {"AAPL", std::make_shared<nexus::strategies::SmaCrossoverStrategy>(2, 3)},
        {"GOOG", std::make_shared<nexus::strategies::SmaCrossoverStrategy>(2, 3)}
    };

    // 3. Instantiate and Run Engine
    std::cout << "Instantiating and running the multi-asset backtest engine..." << std::endl;
    nexus::core::BacktestEngine engine(event_queue, data_handler, strategies, position_manager, execution_simulator);
    engine.run();
    std::cout << "Engine run complete." << std::endl;

    // 4. Assert Final State
    std::cout << "Asserting final portfolio state..." << std::endl;

    // Manually calculate expected cash after trades
    // Default config: commission_per_share=0.005, slippage_factor=0.0001
    // AAPL BUY: 100 shares @ ~104. Price with slippage = 104 * (1 + 0.0001) = 104.0104
    //           Cost = 100 * 104.0104 = 10401.04. Commission = 100 * 0.005 = 0.5. Total = 10401.54
    // GOOG SELL: 100 shares @ ~196. Price with slippage = 196 * (1 - 0.0001) = 195.9804
    //            Credit = 100 * 195.9804 = 19598.04. Commission = 100 * 0.005 = 0.5. Total = 19597.54
    double expected_cash = 100000.0 - 10401.54 + 19597.54; // ~109196.0

    double final_cash = position_manager->get_available_cash();
    std::cout << "Final cash: " << final_cash << " (Expected: ~" << expected_cash << ")" << std::endl;
    assert(are_doubles_equal(final_cash, expected_cash));

    auto final_positions = position_manager->get_all_positions();
    assert(final_positions.size() == 2);

    bool found_aapl = false;
    bool found_goog = false;
    for (const auto& pos : final_positions) {
        if (pos.symbol_ == "AAPL") {
            found_aapl = true;
            assert(are_doubles_equal(pos.quantity_, 100.0));
        }
        if (pos.symbol_ == "GOOG") {
            found_goog = true;
            assert(are_doubles_equal(pos.quantity_, -100.0));
        }
    }
    assert(found_aapl && found_goog);

    // 5. Cleanup
    std::remove(aapl_path.c_str());
    std::remove(goog_path.c_str());

    std::cout << "\nAll Multi-Asset Integration tests passed!" << std::endl;
    return 0;
}