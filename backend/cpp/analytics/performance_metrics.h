// src/cpp/analytics/performance_metrics.h

#pragma once

namespace nexus::analytics {

/**
 * @struct PerformanceMetrics
 * @brief Comprehensive performance metrics for trading strategy evaluation.
 *
 * This structure contains all the key performance indicators used to evaluate
 * the effectiveness of a trading strategy. It includes both return-based metrics
 * (total return, Sharpe ratio) and risk-based metrics (maximum drawdown, volatility).
 */
struct PerformanceMetrics {
    // Return metrics
    double total_return{0.0};              // Total return as a decimal (e.g., 0.15 for 15%)
    double total_return_percentage{0.0};   // Total return as percentage (e.g., 15.0 for 15%)
    double annualized_return{0.0};         // Annualized return
    
    // Risk metrics
    double volatility{0.0};                // Volatility (required by exporter.cpp)
    double annualized_volatility{0.0};     // Annualized volatility
    double max_drawdown{0.0};              // Maximum peak-to-trough decline
    double max_drawdown_duration{0.0};     // Duration of max drawdown (required by exporter.cpp)
    double sharpe_ratio{0.0};              // Risk-adjusted return metric
    
    // Trade statistics
    int total_trades{0};                   // Total number of trades executed
    int winning_trades{0};                 // Number of winning trades (required by exporter.cpp)
    int losing_trades{0};                  // Number of losing trades (required by exporter.cpp)
    double win_rate{0.0};                  // Percentage of winning trades
    double profit_factor{0.0};             // Profit factor (required by exporter.cpp)
    double average_trade_return{0.0};      // Average return per trade
    double best_trade{0.0};                // Best single trade return
    double worst_trade{0.0};               // Worst single trade return
    
    // Additional risk metrics
    double sortino_ratio{0.0};             // Downside deviation-adjusted return
    double calmar_ratio{0.0};              // Return to max drawdown ratio
    double value_at_risk{0.0};             // Value at Risk (VaR) metric
    
    // Performance consistency metrics
    double information_ratio{0.0};         // Risk-adjusted active return
    double treynor_ratio{0.0};             // Market risk-adjusted return
    double beta{0.0};                      // Market sensitivity coefficient
    double alpha{0.0};                     // Excess return over market
    
    // Time-based metrics
    double monthly_volatility{0.0};        // Monthly return volatility
    double weekly_volatility{0.0};         // Weekly return volatility
    int profitable_months{0};              // Number of profitable months
    int total_months{0};                   // Total number of months
};

} // namespace nexus::analytics