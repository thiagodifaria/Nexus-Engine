// src/cpp/core/event_system.h

#pragma once

#include "core/event_types.h"  // Import EventType from the production system
#include <memory>
#include <queue>
#include <string>
#include <chrono>

namespace nexus::core {

/**
 * @class AbstractEvent
 * @brief Abstract interface for event serialization and introspection.
 *
 * This class provides an alternative event interface focused on serialization
 * and runtime introspection capabilities. It uses the same EventType enum
 * as the production event system for consistency.
 *
 * Note: This is currently unused by the main event processing pipeline,
 * which uses the high-performance Event struct from event_types.h.
 * This interface is preserved for potential future features requiring
 * serialization or dynamic event handling.
 */
class AbstractEvent {
public:
    /**
     * @brief Virtual destructor.
     *
     * Ensures that derived event classes are correctly destroyed when handled
     * through a base class pointer (e.g., when stored in containers of
     * std::unique_ptr<AbstractEvent>). Defaulted for efficiency.
     */
    virtual ~AbstractEvent() = default;

    /**
     * @brief Retrieves the specific type of the event.
     * @return The EventType enumerator corresponding to the concrete event class.
     *
     * This function is essential for event routing and handling, allowing
     * different parts of the system to identify and react to specific event
     * categories. It must be implemented by all derived classes.
     * 
     * Uses the same EventType enum as the production event system for consistency.
     */
    virtual EventType get_type() const = 0;

    /**
     * @brief Retrieves the exact time the event was created.
     * @return A std::chrono::system_clock::time_point representing the
     * moment of the event's instantiation.
     *
     * Timestamps are critical for sequencing, performance measurement (latency),
     * and accurate backtesting. This function provides high-precision timing
     * for all events.
     */
    virtual std::chrono::system_clock::time_point get_timestamp() const = 0;

    /**
     * @brief Provides a string representation of the event's data.
     * @return A std::string containing the serialized state of the event.
     *
     * Serialization is used for logging, debugging, and potentially for
     * inter-process communication (e.g., sending event data to the Python UI).
     * The format of the string is defined by each concrete event class.
     */
    virtual std::string serialize() const = 0;
};

} // namespace nexus::core