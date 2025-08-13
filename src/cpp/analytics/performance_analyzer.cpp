// src/cpp/analytics/performance_analyzer.cpp

#include "analytics/performance_analyzer.h"
#include "core/high_resolution_clock.h" // NEW: For Phase 3.2 high-resolution timing
#include <cmath>
#include <algorithm>
#include <numeric>
#include <iostream>

namespace nexus::analytics {

PerformanceAnalyzer::PerformanceAnalyzer(
    double initial_capital,
    const std::vector<double>& equity_curve,
    const std::vector<nexus::core::TradeExecutionEvent>& trade_history)
    : initial_capital_(initial_capital), equity_curve_(equity_curve), trade_history_(trade_history) {
    
    // NEW: Phase 3.2 - Initialize latency tracker
    nexus::core::LatencyTracker::Config latency_config;
    latency_config.max_measurements_per_operation = 50000; // Higher capacity for trading systems
    latency_config.statistics_update_interval = std::chrono::seconds(1);
    latency_config.enable_percentile_calculation = true;
    latency_config.enable_real_time_stats = true;
    latency_config.measurement_retention_time = std::chrono::minutes(10);
    
    latency_tracker_ = std::make_unique<nexus::core::LatencyTracker>(latency_config);
}

PerformanceMetrics PerformanceAnalyzer::calculate_metrics() {
    PerformanceMetrics metrics;

    if (equity_curve_.empty()) {
        std::cerr << "Warning: Empty equity curve provided to PerformanceAnalyzer" << std::endl;
        return metrics;
    }

    // Basic performance metrics
    double final_capital = equity_curve_.back();
    metrics.total_return = (final_capital - initial_capital_) / initial_capital_;
    metrics.total_return_percentage = metrics.total_return * 100.0;

    // Calculate daily returns for risk metrics
    std::vector<double> daily_returns = calculate_daily_returns();
    
    if (!daily_returns.empty()) {
        // Calculate average daily return
        double sum = std::accumulate(daily_returns.begin(), daily_returns.end(), 0.0);
        double mean_daily_return = sum / daily_returns.size();
        
        // Calculate standard deviation of daily returns
        double variance = 0.0;
        for (double ret : daily_returns) {
            variance += std::pow(ret - mean_daily_return, 2);
        }
        variance /= daily_returns.size();
        double std_dev = std::sqrt(variance);
        
        // Annualized metrics (assuming 252 trading days per year)
        metrics.annualized_return = mean_daily_return * 252.0;
        metrics.annualized_volatility = std_dev * std::sqrt(252.0);
        
        // Sharpe ratio (assuming risk-free rate of 0 for simplicity)
        if (std_dev > 0) {
            metrics.sharpe_ratio = (mean_daily_return / std_dev) * std::sqrt(252.0);
        }
    }

    // Maximum drawdown
    metrics.max_drawdown = calculate_max_drawdown();

    // Trade statistics
    calculate_trade_statistics(metrics);

    return metrics;
}

// NEW: Phase 3.2 - Latency tracking implementation

void PerformanceAnalyzer::enable_latency_tracking(bool enabled) {
    latency_tracking_enabled_ = enabled;
    if (latency_tracker_) {
        latency_tracker_->set_enabled(enabled);
    }
    
    if (enabled) {
        std::cout << "PerformanceAnalyzer: Real-time latency tracking enabled" << std::endl;
    }
}

nexus::core::LatencyTracker& PerformanceAnalyzer::get_latency_tracker() {
    return *latency_tracker_;
}

std::unordered_map<std::string, nexus::core::LatencyStatistics> 
PerformanceAnalyzer::get_latency_statistics() const {
    if (!latency_tracker_ || !latency_tracking_enabled_) {
        return {};
    }
    
    return latency_tracker_->get_all_statistics();
}

void PerformanceAnalyzer::record_latency(const std::string& operation_name, double latency_ns) {
    if (!latency_tracker_ || !latency_tracking_enabled_) [[unlikely]] {
        return;
    }
    
    nexus::core::LatencyMeasurement measurement;
    measurement.operation_name = operation_name;
    measurement.latency_ns = latency_ns;
    measurement.timestamp = std::chrono::system_clock::now();
    
    latency_tracker_->add_measurement(measurement);
}

void PerformanceAnalyzer::record_event_latency(const nexus::core::Event& start_event,
                                              const nexus::core::Event& end_event,
                                              const std::string& operation_name) {
    if (!latency_tracker_ || !latency_tracking_enabled_) [[unlikely]] {
        return;
    }
    
    double latency_ns = 0.0;
    
    // Use hardware timestamps if available for maximum precision
    if (start_event.hardware_timestamp_tsc != 0 && end_event.hardware_timestamp_tsc != 0) {
        latency_ns = nexus::core::HighResolutionClock::calculate_tsc_diff_ns(
            start_event.hardware_timestamp_tsc, end_event.hardware_timestamp_tsc);
    }
    // Fallback to nanosecond timestamps
    else if (start_event.creation_time_ns.count() != 0 && end_event.creation_time_ns.count() != 0) {
        latency_ns = static_cast<double>((end_event.creation_time_ns - start_event.creation_time_ns).count());
    }
    // Final fallback to system timestamps
    else {
        auto duration = end_event.timestamp - start_event.timestamp;
        latency_ns = static_cast<double>(
            std::chrono::duration_cast<std::chrono::nanoseconds>(duration).count());
    }
    
    if (latency_ns > 0.0) {
        record_latency(operation_name, latency_ns);
    }
}

std::vector<double> PerformanceAnalyzer::calculate_daily_returns() const {
    std::vector<double> returns;
    
    if (equity_curve_.size() < 2) {
        return returns;
    }
    
    returns.reserve(equity_curve_.size() - 1);
    
    for (size_t i = 1; i < equity_curve_.size(); ++i) {
        if (equity_curve_[i-1] != 0) {
            double daily_return = (equity_curve_[i] - equity_curve_[i-1]) / equity_curve_[i-1];
            returns.push_back(daily_return);
        }
    }
    
    return returns;
}

double PerformanceAnalyzer::calculate_max_drawdown() const {
    if (equity_curve_.empty()) {
        return 0.0;
    }

    double max_drawdown = 0.0;
    double peak = equity_curve_[0];

    for (double value : equity_curve_) {
        if (value > peak) {
            peak = value;
        }
        
        double drawdown = (peak - value) / peak;
        if (drawdown > max_drawdown) {
            max_drawdown = drawdown;
        }
    }

    return max_drawdown;
}

void PerformanceAnalyzer::calculate_trade_statistics(PerformanceMetrics& metrics) const {
    if (trade_history_.empty()) {
        return;
    }

    metrics.total_trades = trade_history_.size();
    
    // Count winning and losing trades
    int winning_trades = 0;
    int losing_trades = 0;
    double total_profit = 0.0;
    double total_loss = 0.0;
    
    // For simplicity, we'll assume each trade's P&L can be calculated
    // In a real implementation, this would require more sophisticated position tracking
    for (const auto& trade : trade_history_) {
        // This is a simplified calculation - in reality you'd need to track
        // the full position lifecycle to calculate actual P&L per trade
        double trade_value = trade.quantity * trade.price;
        
        // Placeholder logic - in practice this would be more complex
        if (trade.is_buy) {
            // Buy trades contribute to position building
            total_profit += trade_value * 0.01; // Simplified assumption
        } else {
            // Sell trades realize profits/losses
            total_loss += trade_value * 0.005; // Simplified assumption
        }
    }
    
    // Calculate win rate (simplified)
    winning_trades = static_cast<int>(trade_history_.size() * 0.6); // Placeholder
    losing_trades = static_cast<int>(trade_history_.size() - winning_trades);
    
    if (metrics.total_trades > 0) {
        metrics.win_rate = static_cast<double>(winning_trades) / metrics.total_trades;
    }
}

} // namespace nexus::analytics