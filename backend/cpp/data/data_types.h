// src/cpp/data/data_types.h

#pragma once

#include <string>
#include <chrono>

namespace nexus::data {

/**
 * @struct OHLCV
 * @brief Represents a single bar of Open, High, Low, Close, and Volume data.
 *
 * This is a plain data structure used as a common, intermediate representation
 * for market data, whether it comes from a CSV file, a database, or a live feed,
 * before it is converted into a system-wide MarketDataEvent.
 */
struct OHLCV {
    std::chrono::system_clock::time_point timestamp;
    std::string symbol;
    double open;
    double high;
    double low;
    double close;
    long volume;
};

} // namespace nexus::data