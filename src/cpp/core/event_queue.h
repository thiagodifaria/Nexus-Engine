// src/cpp/core/event_queue.h

#pragma once

#include "core/disruptor_queue.h"
#include "core/event_system.h"
#include <memory>
#include <mutex>
#include <condition_variable>

namespace nexus::core {

/**
 * @struct EventQueueConfig
 * @brief Configuration options for EventQueue performance tuning.
 */
struct EventQueueConfig {
    /**
     * @brief Whether to use the high-performance disruptor implementation.
     * 
     * When true, uses the lock-free LMAX Disruptor pattern for maximum performance.
     * When false, falls back to traditional mutex-based queue for compatibility.
     * Default: true for maximum performance.
     */
    bool use_disruptor = true;

    /**
     * @brief Ring buffer size for the disruptor (must be power of 2).
     * 
     * Larger buffers provide better throughput but use more memory.
     * Recommended values:
     * - 64K-256K for low-latency scenarios
     * - 1M-4M for high-throughput scenarios
     * Default: 1M entries.
     */
    size_t buffer_size = 1024 * 1024;

    /**
     * @brief Wait strategy for consumer threads.
     * 
     * Trade-offs:
     * - BUSY_SPIN: Lowest latency, highest CPU usage
     * - YIELDING: Balanced latency and CPU usage (recommended)
     * - SLEEPING: Lower CPU usage, higher latency
     * - BLOCKING: Traditional blocking, good for bursty workloads
     */
    WaitStrategyType wait_strategy = WaitStrategyType::YIELDING;

    /**
     * @brief Enable multi-producer support.
     * 
     * Set to false if only one thread will ever call enqueue() for better performance.
     * Default: true for general compatibility.
     */
    bool multi_producer = true;

    /**
     * @brief Enable multi-consumer support.
     * 
     * Set to false if only one thread will ever call dequeue() for better performance.
     * Default: true for general compatibility.
     */
    bool multi_consumer = true;
};

/**
 * @class EventQueue
 * @brief High-performance, thread-safe event queue with configurable backend.
 *
 * This class provides a thread-safe, FIFO queue for managing Event objects.
 * It maintains the original EventQueue interface for backward compatibility
 * while optionally using the high-performance LMAX Disruptor pattern internally.
 *
 * Key features:
 * - Backward compatible with existing EventQueue interface
 * - Configurable backend (disruptor or traditional mutex-based)
 * - Thread-safe for multiple producers and consumers
 * - Lock-free operation when using disruptor backend
 * - Performance monitoring and statistics
 *
 * Performance with disruptor backend:
 * - Throughput: 10-100M+ events/second
 * - Latency: 10ns-10μs depending on wait strategy
 * - Memory overhead: Fixed allocation, no dynamic allocation during operation
 */
class EventQueue {
public:
    /**
     * @brief Constructs an EventQueue with default configuration.
     */
    EventQueue() : EventQueue(EventQueueConfig{}) {}

    /**
     * @brief Constructs an EventQueue with custom configuration.
     * @param config Configuration parameters for performance tuning.
     */
    explicit EventQueue(const EventQueueConfig& config) : config_(config) {
        if (config_.use_disruptor) {
            // Configure disruptor
            DisruptorQueue<Event*>::Config disruptor_config;
            disruptor_config.buffer_size = config_.buffer_size;
            disruptor_config.wait_strategy = config_.wait_strategy;
            disruptor_config.multi_producer = config_.multi_producer;
            disruptor_config.multi_consumer = config_.multi_consumer;
            
            disruptor_queue_ = std::make_unique<DisruptorQueue<Event*>>(disruptor_config);
        }
    }

    /**
     * @brief Destructor - ensures proper cleanup.
     */
    ~EventQueue() = default;

    // Disable copy constructor and assignment
    EventQueue(const EventQueue&) = delete;
    EventQueue& operator=(const EventQueue&) = delete;

    // Enable move constructor and assignment
    EventQueue(EventQueue&&) = default;
    EventQueue& operator=(EventQueue&&) = default;

    /**
     * @brief Pushes a new event onto the back of the queue.
     * @param event A raw pointer to an Event. The queue does not take ownership.
     * 
     * This method is thread-safe and can be called from multiple producer threads.
     * When using the disruptor backend, this operation is lock-free.
     */
    void enqueue(Event* event) {
        if (config_.use_disruptor && disruptor_queue_) [[likely]] {
            // Use high-performance disruptor implementation
            disruptor_queue_->publish(event);
        } else {
            // Fall back to traditional mutex-based implementation
            std::lock_guard<std::mutex> lock(queue_mutex_);
            traditional_queue_.push(event);
            cv_.notify_one();
        }
    }

    /**
     * @brief Attempts to dequeue an event without blocking.
     * @return A raw pointer to the dequeued event, or nullptr if queue is empty.
     * 
     * This method is thread-safe and can be called from multiple consumer threads.
     * Returns immediately if no event is available.
     */
    Event* dequeue() {
        if (config_.use_disruptor && disruptor_queue_) [[likely]] {
            // Use high-performance disruptor implementation
            return disruptor_queue_->try_consume();
        } else {
            // Fall back to traditional mutex-based implementation
            std::lock_guard<std::mutex> lock(queue_mutex_);
            if (traditional_queue_.empty()) {
                return nullptr;
            }
            Event* event = traditional_queue_.front();
            traditional_queue_.pop();
            return event;
        }
    }
    
    /**
     * @brief Waits until the queue has an event, then dequeues and returns it.
     * @return A raw pointer to the dequeued event.
     * 
     * This method blocks until an event becomes available. It is thread-safe
     * and can be called from multiple consumer threads.
     */
    Event* wait_and_dequeue() {
        if (config_.use_disruptor && disruptor_queue_) [[likely]] {
            // Use high-performance disruptor implementation
            return disruptor_queue_->consume();
        } else {
            // Fall back to traditional mutex-based implementation
            std::unique_lock<std::mutex> lock(queue_mutex_);
            cv_.wait(lock, [this] { return !traditional_queue_.empty(); });

            Event* event = traditional_queue_.front();
            traditional_queue_.pop();
            return event;
        }
    }

    /**
     * @brief Checks if the event queue is empty.
     * @return True if the queue contains no events, false otherwise.
     * 
     * Note: In a multi-threaded environment, this value may become stale
     * immediately after the call returns.
     */
    bool empty() const {
        if (config_.use_disruptor && disruptor_queue_) [[likely]] {
            return disruptor_queue_->empty();
        } else {
            std::lock_guard<std::mutex> lock(queue_mutex_);
            return traditional_queue_.empty();
        }
    }

    /**
     * @brief Gets the current number of events in the queue.
     * @return The number of events as a size_t.
     * 
     * Note: In a multi-threaded environment, this value may become stale
     * immediately after the call returns. When using disruptor backend,
     * this is an approximation due to the lock-free nature.
     */
    size_t size() const {
        if (config_.use_disruptor && disruptor_queue_) [[likely]] {
            return disruptor_queue_->size();
        } else {
            std::lock_guard<std::mutex> lock(queue_mutex_);
            return traditional_queue_.size();
        }
    }

    /**
     * @brief Removes all events from the queue.
     * 
     * @warning This operation is not thread-safe and should only be called
     *          when no other threads are accessing the queue.
     */
    void clear() {
        if (config_.use_disruptor && disruptor_queue_) [[likely]] {
            disruptor_queue_->clear();
        } else {
            std::lock_guard<std::mutex> lock(queue_mutex_);
            std::queue<Event*> empty_queue;
            traditional_queue_.swap(empty_queue);
        }
    }

    /**
     * @brief Gets the total capacity of the queue.
     * @return The maximum number of events the queue can hold.
     */
    size_t capacity() const {
        if (config_.use_disruptor && disruptor_queue_) [[likely]] {
            return disruptor_queue_->capacity();
        } else {
            // Traditional queue has no fixed capacity
            return SIZE_MAX;
        }
    }

    /**
     * @brief Checks if the disruptor backend is being used.
     * @return True if using high-performance disruptor, false if using traditional queue.
     */
    bool is_using_disruptor() const noexcept {
        return config_.use_disruptor && disruptor_queue_ != nullptr;
    }

    /**
     * @brief Gets performance statistics for the queue.
     * @return A structure containing various performance metrics.
     */
    struct Statistics {
        bool using_disruptor;
        size_t current_size;
        size_t capacity;
        double utilization_percentage;
        WaitStrategyType wait_strategy;
    };

    Statistics get_statistics() const {
        Statistics stats;
        stats.using_disruptor = is_using_disruptor();
        stats.current_size = size();
        stats.capacity = capacity();
        stats.utilization_percentage = (stats.capacity != SIZE_MAX) ? 
            static_cast<double>(stats.current_size) / stats.capacity * 100.0 : 0.0;
        stats.wait_strategy = config_.wait_strategy;
        return stats;
    }

    /**
     * @brief Gets the current configuration.
     * @return The configuration used to initialize this queue.
     */
    const EventQueueConfig& get_config() const noexcept {
        return config_;
    }

private:
    // Configuration
    EventQueueConfig config_;

    // High-performance disruptor backend (preferred)
    std::unique_ptr<DisruptorQueue<Event*>> disruptor_queue_;

    // Traditional mutex-based backend (fallback)
    std::queue<Event*> traditional_queue_;
    std::condition_variable cv_;
    mutable std::mutex queue_mutex_;
};

} // namespace nexus::core