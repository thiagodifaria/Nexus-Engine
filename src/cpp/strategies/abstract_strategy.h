// src/cpp/strategies/abstract_strategy.h

#pragma once

#include "core/event_types.h"
#include "core/event_pool.h"
#include "strategies/signal_types.h" // NEW: Include for SignalState enum
#include <memory>
#include <string>
#include <unordered_map> // For parameters

namespace nexus::strategies {

class AbstractStrategy {
public:
    explicit AbstractStrategy(std::string name) : name_(std::move(name)) {}
    virtual ~AbstractStrategy() = default;

    virtual void on_market_data(const nexus::core::MarketDataEvent& event) = 0;
    virtual nexus::core::Event* generate_signal(nexus::core::EventPool& pool) = 0;
    virtual std::unique_ptr<AbstractStrategy> clone() const = 0;

    const std::string& get_name() const { return name_; }

    /**
     * @brief Sets a numerical parameter for the strategy.
     * @param key The name of the parameter.
     * @param value The value to set.
     */
    virtual void set_parameter(const std::string& key, double value) {
        parameters_[key] = value;
    }

    /**
     * @brief Gets a numerical parameter of the strategy.
     * @param key The name of the parameter.
     * @return The value of the parameter.
     */
    virtual double get_parameter(const std::string& key) const {
        return parameters_.at(key); // Using .at() provides bounds checking
    }

protected:
    std::string name_;
    std::unordered_map<std::string, double> parameters_;
    
    /**
     * @brief Gets the string representation of the current signal state.
     * @param state The SignalState to convert.
     * @return A const char* for logging and debugging purposes.
     *
     * This helper method is provided for derived classes that need to log
     * or serialize their signal states while maintaining performance.
     */
    constexpr const char* get_signal_state_name(SignalState state) const noexcept {
        return signal_state_to_string(state);
    }
};

} // namespace nexus::strategies