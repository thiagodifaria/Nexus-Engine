// src/cpp/strategies/signal_types.h

#pragma once

#include <cstdint>

namespace nexus::strategies {

/**
 * @enum SignalState
 * @brief Enumeration representing the current signal state of a trading strategy.
 *
 * This enum replaces string-based signal state tracking for performance optimization.
 * Using uint8_t as underlying type provides optimal memory usage and comparison speed.
 * Each strategy maintains its last signal state to prevent duplicate signal generation.
 */
enum class SignalState : uint8_t {
    HOLD = 0,       //!< No active signal - maintain current position
    BUY = 1,        //!< Bullish signal - enter or increase long position
    SELL = 2,       //!< Bearish signal - enter or increase short position
    EXIT = 3,       //!< Close any open position regardless of direction
    OVERBOUGHT = 4, //!< RSI/momentum indicates overbought conditions
    OVERSOLD = 5,   //!< RSI/momentum indicates oversold conditions
    FLAT = 6        //!< Neutral state - no directional bias
};

/**
 * @brief Converts a SignalState enum to its string representation.
 * @param state The SignalState to convert.
 * @return A const char* representing the signal state name.
 *
 * This function is constexpr for compile-time evaluation when possible,
 * and noexcept for guaranteed no-throw behavior in performance-critical paths.
 */
constexpr const char* signal_state_to_string(SignalState state) noexcept {
    switch (state) {
        case SignalState::HOLD:       return "HOLD";
        case SignalState::BUY:        return "BUY";
        case SignalState::SELL:       return "SELL";
        case SignalState::EXIT:       return "EXIT";
        case SignalState::OVERBOUGHT: return "OVERBOUGHT";
        case SignalState::OVERSOLD:   return "OVERSOLD";
        case SignalState::FLAT:       return "FLAT";
        default:                      return "UNKNOWN";
    }
}

/**
 * @brief Converts a TradingSignalEvent::SignalType to SignalState.
 * @param signal_type The TradingSignalEvent::SignalType to convert.
 * @return The corresponding SignalState.
 *
 * This utility function bridges the gap between the event system's signal types
 * and the strategy's internal state tracking.
 */
constexpr SignalState trading_signal_to_state(const nexus::core::TradingSignalEvent::SignalType& signal_type) noexcept {
    using SignalType = nexus::core::TradingSignalEvent::SignalType;
    switch (signal_type) {
        case SignalType::BUY:  return SignalState::BUY;
        case SignalType::SELL: return SignalState::SELL;
        case SignalType::HOLD: return SignalState::HOLD;
        case SignalType::EXIT: return SignalState::EXIT;
        default:               return SignalState::HOLD;
    }
}

} // namespace nexus::strategies