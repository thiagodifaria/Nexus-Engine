// src/cpp/strategies/rsi_strategy.h

#pragma once

#include "strategies/abstract_strategy.h"
#include "strategies/technical_indicators.h"
#include "strategies/signal_types.h" // NEW: Include for SignalState
#include <vector>
#include <string>
#include <memory>

namespace nexus::strategies {

class RSIStrategy : public AbstractStrategy {
public:
    explicit RSIStrategy(int period = 14, double overbought = 70.0, double oversold = 30.0);
    RSIStrategy(const RSIStrategy& other); // Copy constructor declaration

    // --- Overridden Interface Functions ---
    void on_market_data(const nexus::core::MarketDataEvent& event) override;
    nexus::core::Event* generate_signal(nexus::core::EventPool& pool) override;

    std::unique_ptr<AbstractStrategy> clone() const override;

private:
    int period_;
    double overbought_threshold_;
    double oversold_threshold_;

    std::unique_ptr<IncrementalRSI> rsi_calculator_;

    double current_rsi_{50.0};
    
    // PERFORMANCE IMPROVEMENT: Use enum instead of string for signal state tracking
    SignalState last_signal_{SignalState::FLAT};
    std::string symbol_;
};

} // namespace nexus::strategies