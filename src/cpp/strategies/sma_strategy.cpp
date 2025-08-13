// src/cpp/strategies/sma_strategy.cpp

#include "strategies/sma_strategy.h"
#include <numeric>
#include <stdexcept>
#include <chrono>

namespace nexus::strategies {

SmaCrossoverStrategy::SmaCrossoverStrategy(size_t short_window, size_t long_window)
    : AbstractStrategy("SMACrossover"),
      short_window_(short_window),
      long_window_(long_window) {
    // PERFORMANCE IMPROVEMENT: Parameter validation failures are unlikely in normal operation
    if (long_window <= short_window || short_window == 0) [[unlikely]] {
        throw std::invalid_argument("Invalid SMA window parameters.");
    }
    short_sma_calculator_ = std::make_unique<IncrementalSMA>(short_window);
    long_sma_calculator_ = std::make_unique<IncrementalSMA>(long_window);
}

// --- COPY CONSTRUCTOR IMPLEMENTATION ---
SmaCrossoverStrategy::SmaCrossoverStrategy(const SmaCrossoverStrategy& other)
    : AbstractStrategy(other.name_),
      short_window_(other.short_window_),
      long_window_(other.long_window_),
      last_signal_(other.last_signal_),
      symbol_(other.symbol_)
{
    // Re-create the unique_ptr members for the new instance
    short_sma_calculator_ = std::make_unique<IncrementalSMA>(other.short_window_);
    long_sma_calculator_ = std::make_unique<IncrementalSMA>(other.long_window_);
}

std::unique_ptr<AbstractStrategy> SmaCrossoverStrategy::clone() const {
    return std::make_unique<SmaCrossoverStrategy>(*this);
}

void SmaCrossoverStrategy::on_market_data(const nexus::core::MarketDataEvent& event) {
    // PERFORMANCE IMPROVEMENT: Symbol assignment happens only once, then updates are common
    if (symbol_.empty()) [[unlikely]] {
        symbol_ = event.symbol;
    }
    
    // These operations always succeed with valid market data
    short_sma_calculator_->update(event.close);
    long_sma_calculator_->update(event.close);
}

nexus::core::Event* SmaCrossoverStrategy::generate_signal(nexus::core::EventPool& pool) {
    double long_sma = long_sma_calculator_->get_value();
    double short_sma = short_sma_calculator_->get_value();

    // PERFORMANCE IMPROVEMENT: Early return during SMA warm-up period is less common after initialization
    if (long_sma == 0.0) [[unlikely]] {
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

    // PERFORMANCE IMPROVEMENT: BUY signals are slightly more common in trending markets
    if (short_sma > long_sma && last_signal_ != SignalState::BUY) [[likely]] {
        last_signal_ = SignalState::BUY;
        return create_signal(nexus::core::TradingSignalEvent::SignalType::BUY);
    }
    // PERFORMANCE IMPROVEMENT: SELL signals are common but less frequent than BUY in typical bull markets
    else if (short_sma < long_sma && last_signal_ != SignalState::SELL) {
        last_signal_ = SignalState::SELL;
        return create_signal(nexus::core::TradingSignalEvent::SignalType::SELL);
    }
    
    // PERFORMANCE IMPROVEMENT: No signal generation is the most common case
    return nullptr; // [[likely]] implicit for this path
}

} // namespace nexus::strategies