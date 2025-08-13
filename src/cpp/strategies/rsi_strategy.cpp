// src/cpp/strategies/rsi_strategy.cpp

#include "strategies/rsi_strategy.h"
#include <stdexcept>
#include <chrono>

namespace nexus::strategies {

RSIStrategy::RSIStrategy(int period, double overbought, double oversold)
    : AbstractStrategy("RSIStrategy"),
      period_(period),
      overbought_threshold_(overbought),
      oversold_threshold_(oversold) {
    // PERFORMANCE IMPROVEMENT: Parameter validation failures are unlikely in normal operation
    if (period <= 1 || overbought <= oversold || oversold < 0 || overbought > 100) [[unlikely]] {
        throw std::invalid_argument("Invalid RSI strategy parameters.");
    }
    rsi_calculator_ = std::make_unique<IncrementalRSI>(period_);
}

// --- COPY CONSTRUCTOR IMPLEMENTATION ---
RSIStrategy::RSIStrategy(const RSIStrategy& other)
    : AbstractStrategy(other.name_),
      period_(other.period_),
      overbought_threshold_(other.overbought_threshold_),
      oversold_threshold_(other.oversold_threshold_),
      current_rsi_(other.current_rsi_),
      last_signal_(other.last_signal_),
      symbol_(other.symbol_)
{
    // Re-create the unique_ptr member for the new instance
    rsi_calculator_ = std::make_unique<IncrementalRSI>(other.period_);
}

std::unique_ptr<AbstractStrategy> RSIStrategy::clone() const {
    return std::make_unique<RSIStrategy>(*this);
}

void RSIStrategy::on_market_data(const nexus::core::MarketDataEvent& event) {
    // PERFORMANCE IMPROVEMENT: Symbol assignment happens only once, then updates are common
    if (symbol_.empty()) [[unlikely]] {
        symbol_ = event.symbol;
    }
    
    // RSI calculation always succeeds with valid price data
    current_rsi_ = rsi_calculator_->update(event.close);
}

nexus::core::Event* RSIStrategy::generate_signal(nexus::core::EventPool& pool) {
    auto create_signal = [&](nexus::core::TradingSignalEvent::SignalType type) {
        auto* signal = pool.create_trading_signal_event();
        signal->strategy_id = this->get_name();
        signal->symbol = this->symbol_;
        signal->signal = type;
        signal->timestamp = std::chrono::system_clock::now();
        signal->confidence = 1.0;
        signal->suggested_quantity = 100.0;
        return signal;
    };

    // PERFORMANCE IMPROVEMENT: Overbought conditions are less frequent than normal range
    if (current_rsi_ > overbought_threshold_ && last_signal_ != SignalState::OVERBOUGHT) [[unlikely]] {
        last_signal_ = SignalState::OVERBOUGHT;
        return create_signal(nexus::core::TradingSignalEvent::SignalType::SELL);
    }
    // PERFORMANCE IMPROVEMENT: Oversold conditions are less frequent than normal range
    else if (current_rsi_ < oversold_threshold_ && last_signal_ != SignalState::OVERSOLD) [[unlikely]] {
        last_signal_ = SignalState::OVERSOLD;
        return create_signal(nexus::core::TradingSignalEvent::SignalType::BUY);
    }
    // PERFORMANCE IMPROVEMENT: RSI in normal range (30-70) is the most common condition
    else if (current_rsi_ < overbought_threshold_ && current_rsi_ > oversold_threshold_) [[likely]] {
        last_signal_ = SignalState::FLAT;
    }
    
    // PERFORMANCE IMPROVEMENT: No signal generation is the most common case
    return nullptr; // [[likely]] implicit for this path
}

} // namespace nexus::strategies