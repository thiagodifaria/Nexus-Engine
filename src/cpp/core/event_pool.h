// src/cpp/core/event_pool.h

#pragma once

#include "core/hpc_utils.h"
#include "core/event_types.h"
#include <utility> // for std::forward

namespace nexus::core {

/**
 * @class EventPool
 * @brief A centralized, high-performance factory for creating and recycling event objects.
 *
 * This class serves as a dedicated memory manager for all concrete event types
 * in the Nexus system. It contains three distinct memory pools, one for each
 * event type: MarketDataEvent, TradingSignalEvent, and TradeExecutionEvent.
 *
 * By replacing direct heap allocations (e.g., `std::make_unique`) with requests
 * to this pool, the system avoids the significant performance overhead of
 * frequent OS-level memory allocation, drastically improving throughput and
 * reducing latency on the critical event-processing path.
 */
class EventPool {
public:
    /**
     * @brief Constructs and returns a MarketDataEvent from the dedicated pool.
     * @tparam Args The types of arguments for the MarketDataEvent constructor.
     * @param args The arguments to forward to the event's constructor.
     * @return A raw pointer to the newly constructed MarketDataEvent.
     */
    template<typename... Args>
    MarketDataEvent* create_market_data_event(Args&&... args) {
        return market_data_pool_.allocate(std::forward<Args>(args)...);
    }

    /**
     * @brief Constructs and returns a TradingSignalEvent from the dedicated pool.
     * @tparam Args The types of arguments for the TradingSignalEvent constructor.
     * @param args The arguments to forward to the event's constructor.
     * @return A raw pointer to the newly constructed TradingSignalEvent.
     */
    template<typename... Args>
    TradingSignalEvent* create_trading_signal_event(Args&&... args) {
        return signal_pool_.allocate(std::forward<Args>(args)...);
    }

    /**
     * @brief Constructs and returns a TradeExecutionEvent from the dedicated pool.
     * @tparam Args The types of arguments for the TradeExecutionEvent constructor.
     * @param args The arguments to forward to the event's constructor.
     * @return A raw pointer to the newly constructed TradeExecutionEvent.
     */
    template<typename... Args>
    TradeExecutionEvent* create_trade_execution_event(Args&&... args) {
        return execution_pool_.allocate(std::forward<Args>(args)...);
    }

    /**
     * @brief Destroys an event and returns its memory to the appropriate pool.
     *
     * This function acts as the single point of entry for recycling any event
     * object. It inspects the event's type and dispatches it to the correct
     * memory pool for deallocation, ensuring the memory can be reused for a
     * future event of the same type.
     *
     * @param event A pointer to the base Event class to be destroyed.
     */
    void destroy_event(Event* event) {
        if (!event) {
            return;
        }

        switch (event->get_type()) {
            case EventType::MARKET_DATA: [[likely]] {
                market_data_pool_.deallocate(static_cast<MarketDataEvent*>(event));
                break;
            }
            case EventType::TRADING_SIGNAL: {
                signal_pool_.deallocate(static_cast<TradingSignalEvent*>(event));
                break;
            }
            // --- CORRECTED TYPO ---
            case EventType::TRADE_EXECUTION: {
                execution_pool_.deallocate(static_cast<TradeExecutionEvent*>(event));
                break;
            }
            default: {
                // In a production system, one might log an error here for an
                // unknown event type, but for now, we do nothing.
                break;
            }
        }
    }

private:
    // A dedicated memory pool for MarketDataEvent objects.
    MemoryPool<MarketDataEvent> market_data_pool_;

    // A dedicated memory pool for TradingSignalEvent objects.
    MemoryPool<TradingSignalEvent> signal_pool_;

    // A dedicated memory pool for TradeExecutionEvent objects.
    MemoryPool<TradeExecutionEvent> execution_pool_;
};

} // namespace nexus::core