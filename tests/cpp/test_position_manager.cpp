// tests/cpp/test_position_manager.cpp

#include "position/position_manager.h"
#include "core/event_types.h"
#include <iostream>
#include <cassert>
#include <vector>
#include <cmath>
#include <stdexcept>

// --- Test Utilities ---
bool are_doubles_equal(double a, double b, double epsilon = 0.0001) {
    return std::fabs(a - b) < epsilon;
}


// --- Test Cases ---
void test_buy_and_open_position() {
    std::cout << "Running test: test_buy_and_open_position..." << std::endl;

    // Setup
    nexus::position::PositionManager pm(100000.0);
    nexus::core::TradeExecutionEvent buy_event;
    buy_event.symbol = "AAPL";
    buy_event.quantity = 100.0;
    buy_event.price = 150.00;
    buy_event.commission = 5.00;
    buy_event.is_buy = true;

    // Action
    pm.on_trade_execution(buy_event);

    // Assert
    const double expected_cash = 100000.0 - (100.0 * 150.0) - 5.0;
    assert(are_doubles_equal(pm.get_available_cash(), expected_cash));

    // --- CORRECTED METHOD NAME ---
    auto position = pm.get_position_snapshot("AAPL");
    assert(are_doubles_equal(position.quantity_, 100.0));
    assert(are_doubles_equal(position.entry_price_, 150.0));

    std::cout << "PASSED" << std::endl;
}

void test_sell_to_close_position() {
    std::cout << "Running test: test_sell_to_close_position..." << std::endl;

    // Setup
    nexus::position::PositionManager pm(100000.0);
    nexus::core::TradeExecutionEvent buy_event;
    buy_event.symbol = "AAPL";
    buy_event.quantity = 100.0;
    buy_event.price = 150.00;
    buy_event.commission = 5.00;
    buy_event.is_buy = true;
    pm.on_trade_execution(buy_event);

    nexus::core::TradeExecutionEvent sell_event;
    sell_event.symbol = "AAPL";
    sell_event.quantity = 100.0;
    sell_event.price = 160.00;
    sell_event.commission = 5.00;
    sell_event.is_buy = false;

    // Action
    pm.on_trade_execution(sell_event);

    // Assert
    const double expected_cash = 84995.0 + (100.0 * 160.0) - 5.0;
    assert(are_doubles_equal(pm.get_available_cash(), expected_cash));

    bool exception_caught = false;
    try {
        // --- CORRECTED METHOD NAME ---
        pm.get_position_snapshot("AAPL");
    } catch (const std::out_of_range& e) {
        exception_caught = true;
    }
    assert(exception_caught);

    std::cout << "PASSED" << std::endl;
}

void test_pnl_and_equity_calculation() {
    std::cout << "Running test: test_pnl_and_equity_calculation..." << std::endl;

    // Setup
    nexus::position::PositionManager pm(100000.0);
    nexus::core::TradeExecutionEvent buy_event;
    buy_event.symbol = "AAPL";
    buy_event.quantity = 100.0;
    buy_event.price = 150.00;
    buy_event.commission = 5.00;
    buy_event.is_buy = true;
    pm.on_trade_execution(buy_event);

    // Action
    nexus::core::MarketDataEvent market_event;
    market_event.symbol = "AAPL";
    market_event.close = 155.00;
    pm.on_market_data(market_event);

    // Assert
    const double expected_unrealized_pnl = (155.0 - 150.0) * 100.0;
    assert(are_doubles_equal(pm.get_total_unrealized_pnl(), expected_unrealized_pnl));

    const double market_value = 100.0 * 155.0;
    const double expected_equity = 84995.0 + market_value;
    assert(are_doubles_equal(pm.get_total_equity(), expected_equity));

    std::cout << "PASSED" << std::endl;
}


// --- Main Test Runner ---
int main() {
    std::cout << "--- Starting PositionManager Unit Tests ---" << std::endl;
    test_buy_and_open_position();
    test_sell_to_close_position();
    test_pnl_and_equity_calculation();
    std::cout << "\nAll PositionManager tests passed!" << std::endl;
    return 0;
}