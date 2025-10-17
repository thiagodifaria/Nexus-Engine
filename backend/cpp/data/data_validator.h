// src/cpp/data/data_validator.h

#pragma once

#include "data/data_types.h"
#include <vector>
#include <chrono>

namespace nexus::data {

/**
 * @class DataValidator
 * @brief A utility class providing static methods for data quality assurance.
 *
 * This class serves as a toolbox for identifying common issues in historical
 * market data, such as gaps, outliers, and internal inconsistencies. Running
 * these checks before a backtest ensures that the simulation is based on
 * clean, reliable data.
 */
class DataValidator {
public:
    /**
     * @brief Identifies missing timestamps in a data series assuming a daily frequency.
     *
     * This method iterates through the data and checks for gaps larger than
     * one day between consecutive timestamps.
     *
     * @param data A sorted vector of OHLCV data.
     * @return A vector of the timestamps where a gap was detected.
     */
    static std::vector<std::chrono::system_clock::time_point> find_missing_timestamps(
        const std::vector<OHLCV>& data
    );

    /**
     * @brief Finds data points where the price movement is a statistical outlier.
     *
     * This method calculates the mean and standard deviation of daily returns
     * and flags any day where the return exceeds a given number of standard
     * deviations from the mean.
     *
     * @param data A vector of OHLCV data.
     * @param std_dev_threshold The number of standard deviations to use as the outlier threshold.
     * @return A vector of the OHLCV bars that were identified as outliers.
     */
    static std::vector<OHLCV> find_outliers(
        const std::vector<OHLCV>& data,
        double std_dev_threshold
    );

    /**
     * @brief Finds any OHLCV bars with internal inconsistencies.
     *
     * This method checks for logical errors within a single data bar, such as
     * the low price being greater than the high price, or the open/close
     * prices being outside the low-high range.
     *
     * @param data A vector of OHLCV data.
     * @return A vector of the OHLCV bars that were identified as invalid.
     */
    static std::vector<OHLCV> find_invalid_bars(
        const std::vector<OHLCV>& data
    );
};

} // namespace nexus::data