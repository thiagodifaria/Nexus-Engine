// src/cpp/strategies/technical_indicators.cpp

#include "strategies/technical_indicators.h"
#include <numeric>
#include <cmath>
#include <stdexcept>
#include <algorithm>

namespace nexus::strategies {

// --- IncrementalSMA Implementation ---

IncrementalSMA::IncrementalSMA(int period) : period_(period) {
    if (period <= 0) {
        throw std::invalid_argument("SMA period must be positive.");
    }
}

double IncrementalSMA::update(double new_price) {
    // Add the new price to the running sum and the deque.
    current_sum_ += new_price;
    prices_.push_back(new_price);

    // If the window is now too large, remove the oldest price.
    if (prices_.size() > period_) {
        current_sum_ -= prices_.front();
        prices_.pop_front();
    }
    
    // Return the new average, handling the warm-up period correctly.
    if (!prices_.empty()) {
        return current_sum_ / prices_.size();
    }
    return 0.0;
}

double IncrementalSMA::get_value() const {
    if (!prices_.empty()) {
        return current_sum_ / prices_.size();
    }
    return 0.0;
}


// --- IncrementalEMA Implementation ---

IncrementalEMA::IncrementalEMA(int period) {
    if (period <= 0) {
        throw std::invalid_argument("EMA period must be positive.");
    }
    alpha_ = 2.0 / (static_cast<double>(period) + 1.0);
}

double IncrementalEMA::update(double new_price) {
    if (!initialized_) {
        // The first value is its own EMA.
        current_ema_ = new_price;
        initialized_ = true;
    } else {
        // Incremental update formula.
        current_ema_ = (new_price - current_ema_) * alpha_ + current_ema_;
    }
    return current_ema_;
}

double IncrementalEMA::get_value() const {
    return current_ema_;
}

// --- IncrementalRSI Implementation ---

IncrementalRSI::IncrementalRSI(int period) : period_(period) {
    if (period_ <= 0) {
        throw std::invalid_argument("RSI period must be positive.");
    }
}

double IncrementalRSI::update(double new_price) {
    if (!initialized_) {
        last_price_ = new_price;
        initialized_ = true;
        return 50.0; // Return neutral RSI until warmed up
    }

    double change = new_price - last_price_;
    double gain = (change > 0) ? change : 0.0;
    double loss = (change < 0) ? -change : 0.0;

    update_count_++;

    if (update_count_ < period_) {
        // Accumulate gains and losses during the initial warm-up period.
        avg_gain_ += gain;
        avg_loss_ += loss;
    } else if (update_count_ == period_) {
        // First calculation: simple average.
        avg_gain_ = (avg_gain_ + gain) / period_;
        avg_loss_ = (avg_loss_ + loss) / period_;
    } else {
        // Subsequent calculations: Wilder's smoothing.
        avg_gain_ = (avg_gain_ * (period_ - 1) + gain) / period_;
        avg_loss_ = (avg_loss_ * (period_ - 1) + loss) / period_;
    }

    last_price_ = new_price;

    if (update_count_ < period_) {
        return 50.0; // Still in warm-up
    }

    if (avg_loss_ == 0.0) {
        return 100.0; // All gains, max RSI
    }

    double rs = avg_gain_ / avg_loss_;
    return 100.0 - (100.0 / (1.0 + rs));
}

double IncrementalRSI::get_value() const {
    if (update_count_ < period_) {
        return 50.0;
    }
    if (avg_loss_ == 0.0) {
        return 100.0;
    }
    double rs = avg_gain_ / avg_loss_;
    return 100.0 - (100.0 / (1.0 + rs));
}


// --- RSI Implementation ---
double TechnicalIndicators::calculate_rsi(const std::vector<double>& prices, int period) {
    if (period <= 0 || prices.size() < period + 1) {
        return 50.0; // Return a neutral value if not enough data
    }

    std::vector<double> gains;
    std::vector<double> losses;

    for (size_t i = 1; i < prices.size(); ++i) {
        double change = prices[i] - prices[i - 1];
        if (change > 0) {
            gains.push_back(change);
            losses.push_back(0);
        } else {
            gains.push_back(0);
            losses.push_back(std::abs(change));
        }
    }

    if (gains.size() < period) {
        return 50.0;
    }

    // Calculate initial average gain and loss
    double avg_gain = std::accumulate(gains.begin(), gains.begin() + period, 0.0) / period;
    double avg_loss = std::accumulate(losses.begin(), losses.begin() + period, 0.0) / period;

    // Smooth the averages for the rest of the series
    for (size_t i = period; i < gains.size(); ++i) {
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period;
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period;
    }

    if (avg_loss == 0) {
        return 100.0; // All gains, max RSI
    }

    double rs = avg_gain / avg_loss;
    double rsi = 100.0 - (100.0 / (1.0 + rs));

    return rsi;
}


// --- MACD Implementation ---
// This is a helper function as EMA calculation is iterative over a series
namespace {
    std::vector<double> calculate_ema_series(const std::vector<double>& prices, int period) {
        if (period <= 0 || prices.size() < period) {
            return {};
        }
        std::vector<double> ema_values;
        ema_values.reserve(prices.size());

        // Start with an SMA for the first value
        double first_sma = std::accumulate(prices.begin(), prices.begin() + period, 0.0) / period;
        ema_values.push_back(first_sma);

        double multiplier = 2.0 / (static_cast<double>(period) + 1.0);

        // Calculate subsequent EMA values
        for (size_t i = period; i < prices.size(); ++i) {
            double ema = (prices[i] - ema_values.back()) * multiplier + ema_values.back();
            ema_values.push_back(ema);
        }
        return ema_values;
    }
}
std::pair<double, double> TechnicalIndicators::calculate_macd(
    const std::vector<double>& prices, int fast_period, int slow_period, int signal_period) {
    
    if (prices.size() < slow_period + signal_period) {
        return {0.0, 0.0};
    }

    // 1. Calculate Fast and Slow EMAs
    auto ema_fast_series = calculate_ema_series(prices, fast_period);
    auto ema_slow_series = calculate_ema_series(prices, slow_period);

    // Ensure we have enough values to calculate MACD
    if (ema_fast_series.empty() || ema_slow_series.empty()) {
        return {0.0, 0.0};
    }

    // 2. Calculate the MACD line
    // The MACD line is the difference between the two EMAs. We need a series of these.
    std::vector<double> macd_line_series;
    // Align the series before calculating the difference
    size_t fast_offset = prices.size() - ema_fast_series.size();
    size_t slow_offset = prices.size() - ema_slow_series.size();
    size_t common_size = std::min(ema_fast_series.size(), ema_slow_series.size());

    for(size_t i = 0; i < common_size; ++i) {
        macd_line_series.push_back(
            ema_fast_series[i + (ema_fast_series.size() - common_size)] - 
            ema_slow_series[i + (ema_slow_series.size() - common_size)]
        );
    }
    
    if (macd_line_series.size() < signal_period) {
        return {0.0, 0.0};
    }

    // 3. Calculate the Signal Line (EMA of the MACD line)
    auto signal_line_series = calculate_ema_series(macd_line_series, signal_period);

    if (signal_line_series.empty()) {
        return {0.0, 0.0};
    }

    // 4. Return the latest values
    return {macd_line_series.back(), signal_line_series.back()};
}

} // namespace nexus::strategies