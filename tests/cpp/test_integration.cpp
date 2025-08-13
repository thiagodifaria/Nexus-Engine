// tests/cpp/test_integration.cpp

#include "core/backtest_engine.h"
#include "core/event_queue.h"
#include "data/market_data_handler.h"
#include "strategies/sma_strategy.h"
#include "execution/execution_simulator.h"
#include "position/position_manager.h"

#include <iostream>
#include <fstream>
#include <cassert>
#include <memory>
#include <vector>
#include <string>
#include <cmath>
#include <cstdio> // For std::remove
#include <unordered_map>

// --- Test Utilities ---
bool are_doubles_equal(double a, double b, double epsilon = 0.001) {
    return std::fabs(a - b) < epsilon;
}

// --- Main Test Runner ---
int main() {
    std::cout << "--- Starting Full System Integration Test ---" << std::endl;

    // 1. Setup Phase
    const std::string csv_filename = "test_integration_data.csv";
    const std::string symbol = "TEST";
    
    // a. Create Dummy CSV File
    {
        std::ofstream csv_file(csv_filename);
        csv_file << "Timestamp,Open,High,Low,Close,Volume\n"
                 << "2025-01-01 09:30:00,100,100,100,100,1000\n"
                 << "2025-01-02 09:30:00,101,101,101,101,1000\n"
                 << "2025-01-03 09:30:00,102,102,102,102,1000\n"
                 << "2025-01-04 09:30:00,103,103,103,103,1000\n"
                 << "2025-01-05 09:30:00,104,104,104,104,1000\n" // BUY signal generated here
                 << "2025-01-06 09:30:00,105,105,105,105,1000\n"
                 << "2025-01-07 09:30:00,106,106,106,106,1000\n"
                 << "2025-01-08 09:30:00,105,105,105,105,1000\n"
                 << "2025-01-09 09:30:00,104,104,104,104,1000\n"
                 << "2025-01-10 09:30:00,101,101,101,101,1000\n" // SELL signal generated here
                 << "2025-01-11 09:30:00,100,100,100,100,1000\n";
    }

    // b. Instantiate Components
    nexus::core::EventQueue event_queue;
    auto position_manager = std::make_shared<nexus::position::PositionManager>(100000.0);
    
    nexus::execution::MarketSimulationConfig test_config;
    test_config.slippage_factor = 0.0;
    auto execution_simulator = std::make_shared<nexus::execution::ExecutionSimulator>(test_config);
    
    // --- CORRECTED for multi-asset engine ---
    auto strategy = std::make_shared<nexus::strategies::SmaCrossoverStrategy>(3, 5);
    std::unordered_map<std::string, std::shared_ptr<nexus::strategies::AbstractStrategy>> strategies = {{symbol, strategy}};
    
    std::unordered_map<std::string, std::string> symbol_filepaths = {{symbol, csv_filename}};
    auto data_handler = std::make_shared<nexus::data::CsvDataHandler>(event_queue, symbol_filepaths);

    // c. Instantiate Engine
    nexus::core::BacktestEngine engine(event_queue, data_handler, strategies, position_manager, execution_simulator);

    // 2. Action Phase
    std::cout << "Running full integration backtest..." << std::endl;
    engine.run();

    // 3. Assert Phase
    std::cout << "Asserting final portfolio state..." << std::endl;
    
    double commission_per_trade = 100.0 * test_config.commission_per_share;
    double buy_price = 104.0 * (1.0 + (test_config.bid_ask_spread_bps / 10000.0));
    double buy_cost = (100.0 * buy_price) + commission_per_trade;
    double cash_after_buy = 100000.0 - buy_cost;

    double sell_price = 101.0 * (1.0 - (test_config.bid_ask_spread_bps / 10000.0));
    double sell_revenue = (100.0 * sell_price) - commission_per_trade;
    double expected_final_cash = cash_after_buy + sell_revenue;

    assert(are_doubles_equal(position_manager->get_available_cash(), expected_final_cash));
    
    bool exception_caught = false;
    try {
        // --- CORRECTED METHOD NAME ---
        position_manager->get_position_snapshot("TEST");
    } catch (const std::out_of_range& e) {
        exception_caught = true;
    }
    assert(exception_caught);

    // 4. Cleanup Phase
    std::remove(csv_filename.c_str());
    
    std::cout << "\nFull system integration test passed!" << std::endl;
    
    return 0;
}