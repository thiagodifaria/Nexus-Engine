// src/cpp/strategies/technical_indicators.h

#pragma once

#include "data/data_types.h" // For potential future use with OHLCV data
#include <vector>
#include <utility> // For std::pair
#include <deque>   // For incremental calculations

namespace nexus::strategies {

/**
 * @class IncrementalSMA
 * @brief A stateful, O(1) calculator for the Simple Moving Average (SMA).
 *
 * This class maintains a rolling window of prices to calculate the SMA
 * incrementally, providing constant-time updates for each new price.
 */
class IncrementalSMA {
public:
    /**
     * @brief Constructs the incremental SMA calculator.
     * @param period The lookback window for the moving average.
     */
    explicit IncrementalSMA(int period);

    /**
     * @brief Adds a new price to the series and updates the SMA.
     * @param new_price The latest price to include in the calculation.
     * @return The newly calculated SMA value.
     */
    double update(double new_price);

    /**
     * @brief Gets the current SMA value without adding a new price.
     * @return The current SMA.
     */
    double get_value() const;

private:
    int period_;
    std::deque<double> prices_; // Holds the current window of prices.
    double current_sum_{0.0};   // The running sum of prices in the window.
};

/**
 * @class IncrementalEMA
 * @brief A stateful, O(1) calculator for the Exponential Moving Average (EMA).
 *
 * This class calculates the EMA incrementally, giving more weight to recent
 * prices without needing to re-scan a historical price series.
 */
class IncrementalEMA {
public:
    /**
     * @brief Constructs the incremental EMA calculator.
     * @param period The lookback period for the moving average.
     */
    explicit IncrementalEMA(int period);

    /**
     * @brief Adds a new price to the series and updates the EMA.
     * @param new_price The latest price to include in the calculation.
     * @return The newly calculated EMA value.
     */
    double update(double new_price);

    /**
     * @brief Gets the current EMA value.
     * @return The current EMA.
     */
    double get_value() const;

private:
    double alpha_; // The smoothing factor for the EMA.
    double current_ema_{0.0};
    bool initialized_{false}; // Tracks if the first EMA value has been set.
};

/**
 * @class IncrementalRSI
 * @brief A stateful, O(1) calculator for the Relative Strength Index (RSI).
 *
 * This class calculates the RSI incrementally after an initial warm-up period,
 * avoiding the need to rescan a full price history on every update.
 */
class IncrementalRSI {
public:
    /**
     * @brief Constructs the incremental RSI calculator.
     * @param period The lookback period for the RSI, typically 14.
     */
    explicit IncrementalRSI(int period = 14);

    /**
     * @brief Adds a new price to the series and updates the RSI.
     * @param new_price The latest price to include in the calculation.
     * @return The newly calculated RSI value.
     */
    double update(double new_price);

    /**
     * @brief Gets the current RSI value.
     * @return The current RSI, or 50.0 if not fully warmed up.
     */
    double get_value() const;

private:
    int period_;
    double avg_gain_{0.0};
    double avg_loss_{0.0};
    double last_price_{0.0};
    int update_count_{0};
    bool initialized_{false};
};


/**
 * @class TechnicalIndicators
 * @brief A static utility library for calculating common technical indicators.
 *
 * This class provides a centralized, verified toolbox of static methods for
 * performing time-series calculations like SMA, EMA, RSI, and MACD. Strategies
 * can use these functions to avoid code duplication and ensure calculations
 * are consistent and correct.
 */
class TechnicalIndicators {
public:
    /**
     * @brief Calculates the Relative Strength Index (RSI).
     * RSI is a momentum oscillator that measures the speed and change of price movements.
     * It oscillates between 0 and 100 and is often used to identify overbought or oversold conditions.
     * @param prices A vector of closing prices.
     * @param period The lookback period, typically 14.
     * @return The calculated RSI value.
     */
    static double calculate_rsi(const std::vector<double>& prices, int period = 14);

    /**
     * @brief Calculates the Moving Average Convergence Divergence (MACD).
     * MACD is a trend-following momentum indicator that shows the relationship
     * between two exponential moving averages of a security’s price.
     * @param prices A vector of closing prices.
     * @param fast_period The period for the shorter-term EMA.
     * @param slow_period The period for the longer-term EMA.
     * @param signal_period The period for the EMA of the MACD line itself.
     * @return A std::pair containing the MACD line (first) and the signal line (second).
     */
    static std::pair<double, double> calculate_macd(
        const std::vector<double>& prices,
        int fast_period = 12,
        int slow_period = 26,
        int signal_period = 9
    );
};

} // namespace nexus::strategies