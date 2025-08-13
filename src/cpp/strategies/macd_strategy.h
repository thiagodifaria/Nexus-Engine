// src/cpp/strategies/macd_strategy.h

#pragma once

#include "strategies/abstract_strategy.h"
#include "strategies/technical_indicators.h"
#include "strategies/signal_types.h" // NEW: Include for SignalState
#include <vector>
#include <string>
#include <memory>

namespace nexus::strategies {

class MACDStrategy : public AbstractStrategy {
public:
    explicit MACDStrategy(int fast_period = 12, int slow_period = 26, int signal_period = 9);
    MACDStrategy(const MACDStrategy& other); // Copy constructor declaration

    // --- Overridden Interface Functions ---
    void on_market_data(const nexus::core::MarketDataEvent& event) override;
    nexus::core::Event* generate_signal(nexus::core::EventPool& pool) override;

    std::unique_ptr<AbstractStrategy> clone() const override;

private:
    int fast_period_;
    int slow_period_;
    int signal_period_;

    std::unique_ptr<IncrementalEMA> fast_ema_calculator_;
    std::unique_ptr<IncrementalEMA> slow_ema_calculator_;
    std::unique_ptr<IncrementalEMA> signal_line_calculator_;

    double macd_line_{0.0};
    double signal_line_{0.0};
    
    // PERFORMANCE IMPROVEMENT: Use enum instead of string for signal state tracking
    SignalState last_signal_{SignalState::HOLD};
    std::string symbol_;
};

} // namespace nexus::strategies