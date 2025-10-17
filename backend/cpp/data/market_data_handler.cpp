// src/cpp/data/market_data_handler.cpp

#include "data/market_data_handler.h"
#include <sstream>
#include <iostream>
#include <algorithm> // for std::sort
#include <iomanip>   // for std::get_time

namespace nexus::data {

// Helper to parse timestamp string (e.g., "2023-01-01 09:30:00")
std::chrono::system_clock::time_point parse_timestamp(const std::string& s) {
    std::tm tm = {};
    std::stringstream ss(s);
    ss >> std::get_time(&tm, "%Y-%m-%d %H:%M:%S");
    return std::chrono::system_clock::from_time_t(std::mktime(&tm));
}


CsvDataHandler::CsvDataHandler(
    nexus::core::EventQueue& event_queue,
    const std::unordered_map<std::string, std::string>& symbol_filepaths)
    : MarketDataHandler(event_queue),
      symbol_filepaths_(symbol_filepaths) {}

bool CsvDataHandler::load_data_source() {
    std::vector<OHLCV> loaded_data;

    for (const auto& pair : symbol_filepaths_) {
        const std::string& symbol = pair.first;
        const std::string& filepath = pair.second;

        std::ifstream file_stream(filepath);
        if (!file_stream.is_open()) {
            std::cerr << "Error: Could not open CSV file: " << filepath << std::endl;
            return false;
        }

        std::string line;
        std::getline(file_stream, line); // Skip header

        while (std::getline(file_stream, line)) {
            std::stringstream ss(line);
            std::string item;
            std::vector<std::string> row;
            while (std::getline(ss, item, ',')) {
                row.push_back(item);
            }
            
            if (row.size() >= 6) { // Assuming format: Timestamp,O,H,L,C,V
                try {
                    OHLCV data_point;
                    data_point.symbol = symbol;
                    data_point.timestamp = parse_timestamp(row[0]);
                    data_point.open = std::stod(row[1]);
                    data_point.high = std::stod(row[2]);
                    data_point.low = std::stod(row[3]);
                    data_point.close = std::stod(row[4]);
                    data_point.volume = std::stoll(row[5]);
                    loaded_data.push_back(data_point);
                } catch (const std::exception& e) {
                    std::cerr << "Error parsing row in " << filepath << ": " << e.what() << std::endl;
                }
            }
        }
    }

    // Sort all loaded data points chronologically by timestamp
    std::sort(loaded_data.begin(), loaded_data.end(), [](const OHLCV& a, const OHLCV& b) {
        return a.timestamp < b.timestamp;
    });

    all_data_points_ = std::move(loaded_data);
    std::cout << "Loaded and sorted " << all_data_points_.size() << " total data points." << std::endl;
    return true;
}

void CsvDataHandler::stream_next(nexus::core::EventPool& pool) {
    if (is_complete()) return;

    const auto& data_point = all_data_points_[current_data_index_];

    auto* event_ptr = pool.create_market_data_event();
    event_ptr->symbol = data_point.symbol;
    event_ptr->timestamp = data_point.timestamp;
    event_ptr->open = data_point.open;
    event_ptr->high = data_point.high;
    event_ptr->low = data_point.low;
    event_ptr->close = data_point.close;
    event_ptr->volume = data_point.volume;
    
    event_queue_.enqueue(event_ptr);
    current_data_index_++;
}

bool CsvDataHandler::is_complete() const {
    return current_data_index_ >= all_data_points_.size();
}

} // namespace nexus::data