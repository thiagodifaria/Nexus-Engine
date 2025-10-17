// tests/cpp/test_advanced_modules.cpp

#include "strategies/technical_indicators.h"
#include "strategies/macd_strategy.h"
#include "strategies/rsi_strategy.h"
#include "core/event_types.h"
#include "core/event_pool.h" // Include the event pool

#include <iostream>
#include <cassert>
#include <vector>
#include <cmath>

// --- Test Utilities ---
bool are_doubles_equal(double a, double b, double epsilon = 0.0001) {
    return std::fabs(a - b) < epsilon;
}

// --- Test Cases ---

void test_technical_indicators() {
    std::cout << "Running test: test_technical_indicators..." << std::endl;

    // The static calculate_sma was removed, so this part of the test is obsolete.
    // The functionality is now tested via the strategy integration tests.

    // Test RSI edge case (all gains)
    std::vector<double> prices_rsi;
    for (int i = 0; i < 20; ++i) prices_rsi.push_back(100.0 + i);
    double rsi = nexus::strategies::TechnicalIndicators::calculate_rsi(prices_rsi, 14);
    assert(are_doubles_equal(rsi, 100.0)); // Should be 100 as there are no losses

    std::cout << "PASSED" << std::endl;
}

void test_macd_strategy() {
    std::cout << "Running test: test_macd_strategy..." << std::endl;

    // Setup
    nexus::strategies::MACDStrategy strategy(5, 10, 4);
    nexus::core::EventPool pool; // Create an event pool for the test
    std::vector<double> prices = {
        50, 50, 50, 50, 50, 50, 50, 50, 50, 50, // Warm-up period
        51, 52, 53, 54, 55, 56, 58, 60          // Accelerating trend to force crossover
    };

    bool buy_signal_fired = false;
    for (size_t i = 0; i < prices.size(); ++i) {
        nexus::core::MarketDataEvent event;
        event.symbol = "TEST";
        event.close = prices[i];
        strategy.on_market_data(event);
        
        // Call generate_signal with the event pool
        nexus::core::Event* base_signal = strategy.generate_signal(pool);

        if (base_signal) {
            // Cast the base pointer to the correct derived type
            auto* signal = static_cast<nexus::core::TradingSignalEvent*>(base_signal);
            if (signal->signal == nexus::core::TradingSignalEvent::SignalType::BUY) {
                buy_signal_fired = true;
                std::cout << "MACD BUY signal fired at index " << i << std::endl;
            }
            // In a real scenario, we would destroy the event, but for this test, it's okay.
        }
    }
    assert(buy_signal_fired);

    std::cout << "PASSED" << std::endl;
}

void test_rsi_strategy() {
    std::cout << "Running test: test_rsi_strategy..." << std::endl;

    // Setup
    nexus::strategies::RSIStrategy strategy(5, 70.0, 30.0);
    nexus::core::EventPool pool; // Create an event pool for the test
    std::vector<double> prices = {
        50, 51, 52, 53, 54, 55, 56, 57, // Strong uptrend to trigger overbought
        56, 55, 54, 53, 52, 51, 50, 49, // Strong downtrend to trigger oversold
        50
    };

    bool sell_signal_fired = false;
    bool buy_signal_fired = false;

    for (size_t i = 0; i < prices.size(); ++i) {
        nexus::core::MarketDataEvent event;
        event.symbol = "TEST";
        event.close = prices[i];
        strategy.on_market_data(event);
        
        // Call generate_signal with the event pool
        nexus::core::Event* base_signal = strategy.generate_signal(pool);

        if (base_signal) {
            // Cast the base pointer to the correct derived type
            auto* signal = static_cast<nexus::core::TradingSignalEvent*>(base_signal);
            if (signal->signal == nexus::core::TradingSignalEvent::SignalType::SELL) {
                sell_signal_fired = true;
                std::cout << "RSI SELL (Overbought) signal fired at index " << i << std::endl;
            }
            if (signal->signal == nexus::core::TradingSignalEvent::SignalType::BUY) {
                buy_signal_fired = true;
                std::cout << "RSI BUY (Oversold) signal fired at index " << i << std::endl;
            }
        }
    }
    assert(sell_signal_fired && buy_signal_fired);

    std::cout << "PASSED" << std::endl;
}

// --- Main Test Runner ---
int main() {
    std::cout << "--- Starting Advanced Modules Unit Tests ---" << std::endl;
    test_technical_indicators();
    test_macd_strategy();
    test_rsi_strategy();
    std::cout << "\nAll Advanced Modules tests passed!" << std::endl;
    return 0;
}