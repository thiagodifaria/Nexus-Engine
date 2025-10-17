// tests/cpp/test_sma_strategy.cpp

#include "strategies/sma_strategy.h"
#include "core/event_types.h"
#include "core/event_pool.h" // Include the event pool
#include <iostream>
#include <cassert>
#include <vector>
#include <string>

// --- Main Test Runner ---

int main() {
    std::cout << "--- Starting SmaCrossoverStrategy Unit Test ---" << std::endl;

    // 1. Setup
    nexus::strategies::SmaCrossoverStrategy strategy(3, 5);
    nexus::core::EventPool pool; // Create an event pool for the test

    std::vector<double> prices = {
        100, 101, 102, 103, 104, // 0-4: SMAs are warming up. A BUY signal occurs at index 4.
        105,                      // 5: Trend continues up.
        106, 105, 104,            // 6-8: Trend reverses.
        101,                      // 9: A SELL signal occurs at index 9.
        100                       // 10
    };

    std::cout << "Simulating price stream and checking for signals..." << std::endl;

    // 2. Test Logic
    for (size_t i = 0; i < prices.size(); ++i) {
        nexus::core::MarketDataEvent event;
        event.symbol = "TEST_SYM";
        event.close = prices[i];

        strategy.on_market_data(event);

        // Call generate_signal with the event pool
        nexus::core::Event* base_signal = strategy.generate_signal(pool);
        
        // Cast the base pointer to the correct derived type to access members
        auto* signal = static_cast<nexus::core::TradingSignalEvent*>(base_signal);

        // d. Assert the behavior based on the current index.
        if (i == 4) {
            std::cout << "Index 4: Expecting BUY signal..." << std::endl;
            assert(signal != nullptr && signal->signal == nexus::core::TradingSignalEvent::SignalType::BUY);
        } else if (i == 9) {
            std::cout << "Index 9: Expecting SELL signal..." << std::endl;
            assert(signal != nullptr && signal->signal == nexus::core::TradingSignalEvent::SignalType::SELL);
        } else {
            assert(signal == nullptr);
        }
    }

    // 3. Conclusion
    std::cout << "\nAll SmaCrossoverStrategy tests passed!" << std::endl;

    return 0;
}