// src/cpp/data/data_validator.cpp

#include "data/data_validator.h"
#include <numeric>
#include <cmath>
#include <algorithm>
#include <vector>

namespace nexus::data {

std::vector<std::chrono::system_clock::time_point> DataValidator::find_missing_timestamps(
    const std::vector<OHLCV>& data) {
    
    std::vector<std::chrono::system_clock::time_point> missing_timestamps;
    if (data.size() < 2) {
        return missing_timestamps;
    }

    // Assuming daily data, a gap is anything significantly larger than 24 hours.
    const auto daily_threshold = std::chrono::hours(25);

    for (size_t i = 1; i < data.size(); ++i) {
        auto duration = data[i].timestamp - data[i - 1].timestamp;
        if (duration > daily_threshold) {
            // A gap is found after the previous timestamp.
            missing_timestamps.push_back(data[i - 1].timestamp);
        }
    }

    return missing_timestamps;
}

std::vector<OHLCV> DataValidator::find_outliers(
    const std::vector<OHLCV>& data,
    double std_dev_threshold) {
    
    std::vector<OHLCV> outliers;
    if (data.size() < 2) {
        return outliers;
    }

    // 1. Calculate daily returns
    std::vector<double> daily_returns;
    daily_returns.reserve(data.size() - 1);
    for (size_t i = 1; i < data.size(); ++i) {
        if (data[i - 1].close > 0) {
            daily_returns.push_back((data[i].close / data[i - 1].close) - 1.0);
        } else {
            daily_returns.push_back(0.0);
        }
    }

    if (daily_returns.empty()) {
        return outliers;
    }

    // 2. Calculate mean and standard deviation of returns
    double sum = std::accumulate(daily_returns.begin(), daily_returns.end(), 0.0);
    double mean = sum / daily_returns.size();

    double sq_sum = std::accumulate(daily_returns.begin(), daily_returns.end(), 0.0,
        [mean](double acc, double r) { return acc + std::pow(r - mean, 2); });
    
    double std_dev = std::sqrt(sq_sum / daily_returns.size());

    if (std_dev == 0.0) {
        return outliers; // No volatility, no outliers
    }

    // 3. Find outliers
    for (size_t i = 0; i < daily_returns.size(); ++i) {
        if (std::abs(daily_returns[i] - mean) > (std_dev_threshold * std_dev)) {
            // The outlier is the bar at i+1, which corresponds to the return at i
            outliers.push_back(data[i + 1]);
        }
    }

    return outliers;
}

std::vector<OHLCV> DataValidator::find_invalid_bars(
    const std::vector<OHLCV>& data) {
    
    std::vector<OHLCV> invalid_bars;

    for (const auto& bar : data) {
        bool is_invalid = false;
        // Check for logical price inconsistencies
        if (bar.low > bar.high) {
            is_invalid = true;
        } else if (bar.open > bar.high || bar.open < bar.low) {
            is_invalid = true;
        } else if (bar.close > bar.high || bar.close < bar.low) {
            is_invalid = true;
        }
        // Check for non-positive prices or negative volume
        else if (bar.open <= 0 || bar.high <= 0 || bar.low <= 0 || bar.close <= 0 || bar.volume < 0) {
            is_invalid = true;
        }

        if (is_invalid) {
            invalid_bars.push_back(bar);
        }
    }

    return invalid_bars;
}

} // namespace nexus::data