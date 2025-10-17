// src/cpp/data/market_data_handler.h

#pragma once

#include "core/event_queue.h"
#include "core/event_pool.h"
#include "data/data_types.h" // For OHLCV
#include <string>
#include <vector>
#include <fstream>
#include <unordered_map>
#include <memory>

namespace nexus::data {

class MarketDataHandler {
public:
    explicit MarketDataHandler(nexus::core::EventQueue& event_queue)
        : event_queue_(event_queue) {}
    virtual ~MarketDataHandler() = default;

    virtual bool load_data_source() = 0;
    virtual void stream_next(nexus::core::EventPool& pool) = 0;
    virtual bool is_complete() const = 0;

protected:
    nexus::core::EventQueue& event_queue_;
};


class CsvDataHandler : public MarketDataHandler {
public:
    /**
     * @brief Constructs the multi-asset CSV data handler.
     * @param event_queue The central event queue.
     * @param symbol_filepaths A map where the key is the symbol and the value is the path to its CSV data file.
     */
    CsvDataHandler(
        nexus::core::EventQueue& event_queue,
        const std::unordered_map<std::string, std::string>& symbol_filepaths
    );

    /**
     * @brief Loads all CSV files, combines the data, and sorts it by timestamp.
     */
    bool load_data_source() override;

    /**
     * @brief Streams the next chronological data point from the combined data feed.
     */
    void stream_next(nexus::core::EventPool& pool) override;

    /**
     * @brief Checks if all historical data has been streamed.
     */
    bool is_complete() const override;

private:
    // Map of symbols to their corresponding CSV file paths.
    std::unordered_map<std::string, std::string> symbol_filepaths_;
    
    // A single, chronologically sorted vector holding all data points for all symbols.
    std::vector<nexus::data::OHLCV> all_data_points_;
    
    // The index of the next data point to be streamed.
    size_t current_data_index_{0};
};

} // namespace nexus::data