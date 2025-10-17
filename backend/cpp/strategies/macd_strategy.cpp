// src/cpp/strategies/macd_strategy.cpp

#include "strategies/macd_strategy.h"
#include <stdexcept>
#include <chrono>

namespace nexus::strategies {

MACDStrategy::MACDStrategy(int fast_period, int slow_period, int signal_period)
    : AbstractStrategy("MACDStrategy"),
      fast_period_(fast_period),
      slow_period_(slow_period),
      signal_period_(signal_period) {
    // PERFORMANCE IMPROVEMENT: Parameter validation failures are unlikely in normal operation
    if (fast_period >= slow_period || fast_period <= 0 || signal_period <= 0) [[unlikely]] {
        throw std::invalid_argument("Invalid MACD period parameters.");
    }
    fast_ema_calculator_ = std::make_unique<IncrementalEMA>(fast_period);
    slow_ema_calculator_ = std::make_unique<IncrementalEMA>(slow_period);
    signal_line_calculator_ = std::make_unique<IncrementalEMA>(signal_period);
}

// --- COPY CONSTRUCTOR IMPLEMENTATION ---
MACDStrategy::MACDStrategy(const MACDStrategy& other)
    : AbstractStrategy(other.name_),
      fast_period_(other.fast_period_),
      slow_period_(other.slow_period_),
      signal_period_(other.signal_period_),
      macd_line_(other.macd_line_),
      signal_line_(other.signal_line_),
      last_signal_(other.last_signal_),
      symbol_(other.symbol_)
{
    // Re-create the unique_ptr members for the new instance
    fast_ema_calculator_ = std::make_unique<IncrementalEMA>(other.fast_period_);
    slow_ema_calculator_ = std::make_unique<IncrementalEMA>(other.slow_period_);
    signal_line_calculator_ = std::make_unique<IncrementalEMA>(other.signal_period_);
}

std::unique_ptr<AbstractStrategy> MACDStrategy::clone() const {
    return std::make_unique<MACDStrategy>(*this);
}

void MACDStrategy::on_market_data(const nexus::core::MarketDataEvent& event) {
    // PERFORMANCE IMPROVEMENT: Symbol assignment happens only once, then updates are common
    if (symbol_.empty()) [[unlikely]] {
        symbol_ = event.symbol;
    }
    
    // EMA calculations always succeed with valid price data
    fast_ema_calculator_->update(event.close);
    slow_ema_calculator_->update(event.close);
    double current_macd_value = fast_ema_calculator_->get_value() - slow_ema_calculator_->get_value();
    signal_line_calculator_->update(current_macd_value);
    this->macd_line_ = current_macd_value;
    this->signal_line_ = signal_line_calculator_->get_value();
}

nexus::core::Event* MACDStrategy::generate_signal(nexus::core::EventPool& pool) {
    // PERFORMANCE IMPROVEMENT: Signal line initialization check is rare after warm-up period
    if (signal_line_ == 0.0) [[unlikely]] {
        return nullptr;
    }

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

    // PERFORMANCE IMPROVEMENT: Bullish crossovers (MACD > Signal) are often more common in trending markets
    if (macd_line_ > signal_line_ && last_signal_ != SignalState::BUY) [[likely]] {
        last_signal_ = SignalState::BUY;
        return create_signal(nexus::core::TradingSignalEvent::SignalType::BUY);
    }
    // PERFORMANCE IMPROVEMENT: Bearish crossovers are less frequent but still significant
    else if (macd_line_ < signal_line_ && last_signal_ != SignalState::SELL) {
        last_signal_ = SignalState::SELL;
        return create_signal(nexus::core::TradingSignalEvent::SignalType::SELL);
    }
    
    // PERFORMANCE IMPROVEMENT: No signal generation is the most common case
    return nullptr; // [[likely]] implicit for this path
}

} // namespace nexus::strategies