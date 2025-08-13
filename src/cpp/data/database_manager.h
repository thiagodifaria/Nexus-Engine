// src/cpp/data/database_manager.h

#pragma once

#include "data/data_types.h"
#include <string>
#include <vector>
#include <chrono>

// Forward-declare the C-style struct from the sqlite3 library.
// This avoids having to include the full sqlite3.h in our header.
struct sqlite3;

namespace nexus::data {

/**
 * @class DatabaseManager
 * @brief Manages all interactions with the SQLite database for data persistence.
 *
 * This class is responsible for opening/closing the database connection,
 * creating the necessary table schemas, and storing and retrieving historical
 * market data. It provides a high-level interface over the low-level C-style
 * SQLite3 API.
 */
class DatabaseManager {
public:
    /**
     * @brief Constructs the DatabaseManager with a path to the DB file.
     * @param path The filesystem path to the SQLite database file.
     */
    explicit DatabaseManager(std::string path);

    /**
     * @brief Destructor. Ensures the database connection is closed properly.
     */
    ~DatabaseManager();

    /**
     * @brief Opens the connection to the SQLite database file.
     * @return True if the connection was successful, false otherwise.
     */
    bool open();

    /**
     * @brief Closes the database connection.
     */
    void close();

    /**
     * @brief Creates the necessary table(s) for storing market data if they
     * don't already exist.
     * @return True if the table was created successfully or already exists.
     */
    bool create_market_data_table();

    /**
     * @brief Stores a batch of OHLCV data for a given symbol in the database.
     * @param symbol The symbol the data belongs to.
     * @param data A vector of OHLCV structs to be inserted.
     * @return True if the data was stored successfully, false otherwise.
     */
    bool store_market_data(const std::string& symbol, const std::vector<OHLCV>& data);

    /**
     * @brief Fetches historical market data for a symbol within a date range.
     * @param symbol The symbol to fetch data for.
     * @param start The start of the time range (inclusive).
     * @param end The end of the time range (inclusive).
     * @return A vector of OHLCV structs containing the fetched data.
     */
    std::vector<OHLCV> fetch_market_data(
        const std::string& symbol,
        const std::chrono::system_clock::time_point& start,
        const std::chrono::system_clock::time_point& end
    );

private:
    /**
     * @brief The filesystem path to the SQLite database.
     */
    std::string db_path_;

    /**
     * @brief A raw pointer to the SQLite database connection object.
     * Managed by the open() and close() methods.
     */
    sqlite3* db_{nullptr};
};

} // namespace nexus::data