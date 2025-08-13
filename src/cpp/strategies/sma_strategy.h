// src/cpp/strategies/sma_strategy.h

#pragma once

#include "strategies/abstract_strategy.h"
#include "strategies/technical_indicators.h"
#include "strategies/signal_types.h" // NEW: Include for SignalState
#include <vector>
#include <deque>
#include <string>
#include <memory>

namespace nexus::strategies {

class SmaCrossoverStrategy : public AbstractStrategy {
public:
    SmaCrossoverStrategy(size_t short_window, size_t long_window);
    SmaCrossoverStrategy(const SmaCrossoverStrategy& other); // Copy constructor declaration

    // --- Overridden Interface Functions ---
    void on_market_data(const nexus::core::MarketDataEvent& event) override;
    nexus::core::Event* generate_signal(nexus::core::EventPool& pool) override;
    
    std::unique_ptr<AbstractStrategy> clone() const override;

private:
    size_t short_window_;
    size_t long_window_;
    
    std::unique_ptr<IncrementalSMA> short_sma_calculator_;
    std::unique_ptr<IncrementalSMA> long_sma_calculator_;

    // PERFORMANCE IMPROVEMENT: Use enum instead of string for signal state tracking
    SignalState last_signal_{SignalState::HOLD};
    std::string symbol_;
};

} // namespace nexus::strategies