// src/cpp/data/database_manager.cpp

#include "data/database_manager.h"
#include "sqlite3.h" // The actual SQLite3 library header
#include <iostream>
#include <stdexcept>

namespace nexus::data {

// --- Constructor & Destructor ---

DatabaseManager::DatabaseManager(std::string path)
    : db_path_(std::move(path)) {}

DatabaseManager::~DatabaseManager() {
    // Ensure the database connection is closed when the object is destroyed.
    close();
}

// --- Connection Management ---

bool DatabaseManager::open() {
    // If a connection is already open, close it first.
    if (db_) {
        close();
    }
    int rc = sqlite3_open(db_path_.c_str(), &db_);
    if (rc != SQLITE_OK) {
        std::cerr << "Database Error: Cannot open database: " << sqlite3_errmsg(db_) << std::endl;
        return false;
    }
    std::cout << "Database opened successfully: " << db_path_ << std::endl;
    return true;
}

void DatabaseManager::close() {
    if (db_) {
        sqlite3_close(db_);
        db_ = nullptr;
    }
}

// --- Schema and Storage ---

bool DatabaseManager::create_market_data_table() {
    const char* sql = R"(
        CREATE TABLE IF NOT EXISTS market_data (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol    TEXT    NOT NULL,
            timestamp INTEGER NOT NULL,
            open      REAL    NOT NULL,
            high      REAL    NOT NULL,
            low       REAL    NOT NULL,
            close     REAL    NOT NULL,
            volume    INTEGER NOT NULL,
            UNIQUE(symbol, timestamp)
        );
    )";
    char* err_msg = nullptr;
    int rc = sqlite3_exec(db_, sql, 0, 0, &err_msg);
    if (rc != SQLITE_OK) {
        std::cerr << "SQL Error: " << err_msg << std::endl;
        sqlite3_free(err_msg);
        return false;
    }
    return true;
}

bool DatabaseManager::store_market_data(const std::string& symbol, const std::vector<OHLCV>& data) {
    if (data.empty()) return true;

    sqlite3_exec(db_, "BEGIN TRANSACTION;", 0, 0, 0);

    const char* sql = "INSERT INTO market_data (symbol, timestamp, open, high, low, close, volume) VALUES (?, ?, ?, ?, ?, ?, ?);";
    sqlite3_stmt* stmt;
    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, 0) != SQLITE_OK) {
        std::cerr << "SQL Error: Failed to prepare statement: " << sqlite3_errmsg(db_) << std::endl;
        return false;
    }

    for (const auto& bar : data) {
        sqlite3_bind_text(stmt, 1, symbol.c_str(), -1, SQLITE_STATIC);
        auto timestamp_t = std::chrono::system_clock::to_time_t(bar.timestamp);
        sqlite3_bind_int64(stmt, 2, timestamp_t);
        sqlite3_bind_double(stmt, 3, bar.open);
        sqlite3_bind_double(stmt, 4, bar.high);
        sqlite3_bind_double(stmt, 5, bar.low);
        sqlite3_bind_double(stmt, 6, bar.close);
        sqlite3_bind_int64(stmt, 7, bar.volume);

        if (sqlite3_step(stmt) != SQLITE_DONE) {
            std::cerr << "SQL Error: Failed to insert row: " << sqlite3_errmsg(db_) << std::endl;
        }
        sqlite3_reset(stmt);
    }

    sqlite3_finalize(stmt);
    sqlite3_exec(db_, "COMMIT;", 0, 0, 0);
    return true;
}

// --- Data Fetching ---

std::vector<OHLCV> DatabaseManager::fetch_market_data(
    const std::string& symbol,
    const std::chrono::system_clock::time_point& start,
    const std::chrono::system_clock::time_point& end) {
    
    std::vector<OHLCV> results;
    const char* sql = "SELECT timestamp, open, high, low, close, volume FROM market_data WHERE symbol = ? AND timestamp BETWEEN ? AND ? ORDER BY timestamp ASC;";
    sqlite3_stmt* stmt;

    if (sqlite3_prepare_v2(db_, sql, -1, &stmt, 0) != SQLITE_OK) {
        std::cerr << "SQL Error: Failed to prepare select statement: " << sqlite3_errmsg(db_) << std::endl;
        return results;
    }

    sqlite3_bind_text(stmt, 1, symbol.c_str(), -1, SQLITE_STATIC);
    sqlite3_bind_int64(stmt, 2, std::chrono::system_clock::to_time_t(start));
    sqlite3_bind_int64(stmt, 3, std::chrono::system_clock::to_time_t(end));

    while (sqlite3_step(stmt) == SQLITE_ROW) {
        OHLCV bar;
        bar.symbol = symbol;
        bar.timestamp = std::chrono::system_clock::from_time_t(sqlite3_column_int64(stmt, 0));
        bar.open = sqlite3_column_double(stmt, 1);
        bar.high = sqlite3_column_double(stmt, 2);
        bar.low = sqlite3_column_double(stmt, 3);
        bar.close = sqlite3_column_double(stmt, 4);
        bar.volume = static_cast<long>(sqlite3_column_int64(stmt, 5));
        results.push_back(bar);
    }

    sqlite3_finalize(stmt);
    return results;
}

} // namespace nexus::data