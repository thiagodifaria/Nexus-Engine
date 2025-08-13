// src/cpp/core/exporter.cpp

#include "core/exporter.h"
#include "analytics/performance_metrics.h"
#include "core/event_types.h"
#include <fstream>
#include <iomanip>
#include <iostream>
#include <ctime>

namespace nexus::core {

// --- export_performance_metrics_to_csv Implementation ---
bool Exporter::export_performance_metrics_to_csv(
    const nexus::analytics::PerformanceMetrics& metrics,
    const std::string& filepath) {
    
    std::ofstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file for writing at " << filepath << std::endl;
        return false;
    }

    file << std::fixed << std::setprecision(4); // Set consistent floating point precision

    file << "Metric,Value\n";
    file << "Total Return," << metrics.total_return << "\n";
    file << "Annualized Return," << metrics.annualized_return << "\n";
    file << "Volatility," << metrics.volatility << "\n";
    file << "Sharpe Ratio," << metrics.sharpe_ratio << "\n";
    file << "Max Drawdown," << metrics.max_drawdown << "\n";
    file << "Max Drawdown Duration (days)," << metrics.max_drawdown_duration << "\n";
    file << "Total Trades," << metrics.total_trades << "\n";
    file << "Winning Trades," << metrics.winning_trades << "\n";
    file << "Losing Trades," << metrics.losing_trades << "\n";
    file << "Win Rate," << metrics.win_rate << "\n";
    file << "Profit Factor," << metrics.profit_factor << "\n";

    file.close();
    return true;
}

// --- export_equity_curve_to_csv Implementation ---
bool Exporter::export_equity_curve_to_csv(
    const std::vector<double>& equity_curve,
    const std::string& filepath) {

    std::ofstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file for writing at " << filepath << std::endl;
        return false;
    }

    file << std::fixed << std::setprecision(2);

    file << "Period,Equity\n";
    for (size_t i = 0; i < equity_curve.size(); ++i) {
        file << i << "," << equity_curve[i] << "\n";
    }

    file.close();
    return true;
}

// --- export_trade_history_to_csv Implementation ---
bool Exporter::export_trade_history_to_csv(
    const std::vector<TradeExecutionEvent>& trade_history,
    const std::string& filepath) {

    std::ofstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file for writing at " << filepath << std::endl;
        return false;
    }

    // Set precision for price and commission
    file << std::fixed << std::setprecision(4);

    file << "Timestamp,Symbol,Action,Quantity,Price,Commission\n";
    for (const auto& trade : trade_history) {
        // Format the timestamp
        auto time_t_val = std::chrono::system_clock::to_time_t(trade.timestamp);
        std::tm tm_val;
        // Use gmtime_s on Windows for thread safety, gmtime on other platforms
        #ifdef _WIN32
            gmtime_s(&tm_val, &time_t_val);
        #else
            tm_val = *gmtime(&time_t_val);
        #endif

        file << std::put_time(&tm_val, "%Y-%m-%d %H:%M:%S") << ","
             << trade.symbol << ","
             << (trade.is_buy ? "BUY" : "SELL") << ","
             << trade.quantity << ","
             << trade.price << ","
             << trade.commission << "\n";
    }

    file.close();
    return true;
}

} // namespace nexus::core