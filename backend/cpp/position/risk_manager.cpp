// src/cpp/position/risk_manager.cpp

#include "position/risk_manager.h"
#include "position/position_manager.h"
#include "core/event_types.h"
#include <algorithm>
#include <iostream>
#include <stdexcept>

namespace nexus::position {

RiskManager::RiskManager(const PositionManager& position_manager)
    : position_manager_(position_manager) {}

bool RiskManager::validate_order(
    const nexus::core::TradingSignalEvent& signal,
    double current_market_price) const {

    // --- Check 1: Portfolio Drawdown ---
    const auto& equity_curve = position_manager_.get_equity_curve();
    if (!equity_curve.empty()) {
        double peak_equity = *std::max_element(equity_curve.begin(), equity_curve.end());
        double current_equity = position_manager_.get_total_equity();
        
        if (peak_equity > 0) {
            double current_drawdown = (peak_equity - current_equity) / peak_equity;
            if (current_drawdown > max_portfolio_drawdown_) {
                std::cerr << "RISK BREACH: Order for " << signal.symbol 
                          << " rejected. Portfolio drawdown " << current_drawdown
                          << " exceeds max of " << max_portfolio_drawdown_ << std::endl;
                return false;
            }
        }
    }

    // --- Check 2: Position Exposure ---
    double total_equity = position_manager_.get_total_equity();
    if (total_equity <= 0) {
        return false; // Cannot take on new risk with no equity.
    }

    // Calculate the value of the proposed trade.
    double proposed_trade_value = signal.suggested_quantity * current_market_price;

    // Get the value of the existing position, if any.
    double existing_position_value = 0.0;
    try {
        // --- CORRECTED METHOD NAME ---
        // The method was renamed from get_position to get_position_snapshot.
        existing_position_value = position_manager_.get_position_snapshot(signal.symbol).get_market_value();
    } catch (const std::out_of_range& e) {
        // No existing position, so its value is 0. This is expected.
    }
    
    // Calculate the new total value if the trade were executed.
    double new_total_position_value = existing_position_value + proposed_trade_value;
    double new_exposure = new_total_position_value / total_equity;

    if (new_exposure > max_position_exposure_) {
        std::cerr << "RISK BREACH: Order for " << signal.symbol 
                  << " rejected. Proposed exposure " << new_exposure
                  << " exceeds max of " << max_position_exposure_ << std::endl;
        return false;
    }

    // If all checks pass, the order is valid.
    return true;
}

} // namespace nexus::position