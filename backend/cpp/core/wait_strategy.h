// src/cpp/core/wait_strategy.h

#pragma once

#include "core/atomic_sequence.h"
#include <memory>
#include <chrono>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <cstdint>

namespace nexus::core {

/**
 * @class WaitStrategy
 * @brief Abstract base class for different waiting strategies in the disruptor pattern.
 *
 * Different wait strategies provide trade-offs between CPU usage, latency, and throughput.
 * The choice of wait strategy depends on the specific requirements of the application.
 */
class WaitStrategy {
public:
    virtual ~WaitStrategy() = default;

    /**
     * @brief Waits for the requested sequence to become available.
     * @param sequence The sequence number to wait for.
     * @param cursor The producer's sequence.
     * @param dependent_sequence The dependent consumer sequence (if any).
     * @param barrier The sequence barrier for coordination.
     * @return The highest available sequence number.
     */
    virtual int64_t wait_for(
        int64_t sequence,
        std::shared_ptr<AtomicSequence> cursor,
        std::shared_ptr<AtomicSequence> dependent_sequence,
        SequenceBarrier& barrier) = 0;

    /**
     * @brief Signals waiting threads that the cursor has advanced.
     */
    virtual void signal_all_when_blocking() = 0;
};

/**
 * @class BusySpinWaitStrategy
 * @brief High-performance wait strategy that spins continuously.
 *
 * This strategy provides the lowest latency but consumes 100% CPU.
 * Best for scenarios where low latency is critical and dedicated CPU cores are available.
 * 
 * Performance characteristics:
 * - Latency: Lowest (~10-50ns)
 * - CPU Usage: 100% on waiting threads
 * - Throughput: Highest
 * - Power consumption: High
 */
class BusySpinWaitStrategy : public WaitStrategy {
public:
    int64_t wait_for(
        int64_t sequence,
        std::shared_ptr<AtomicSequence> cursor,
        std::shared_ptr<AtomicSequence> dependent_sequence,
        SequenceBarrier& barrier) override {
        
        int64_t available_sequence;
        
        // Tight spinning loop with CPU pause instructions for efficiency
        while ((available_sequence = barrier.wait_for(sequence)) < sequence) {
            // CPU pause instruction to improve spin loop performance
            #if defined(_MSC_VER)
                _mm_pause();
            #elif defined(__GNUC__)
                __builtin_ia32_pause();
            #else
                // Fallback for other compilers
                std::this_thread::yield();
            #endif
        }
        
        return available_sequence;
    }

    void signal_all_when_blocking() override {
        // No-op for busy spin - threads are always spinning
    }
};

/**
 * @class YieldingWaitStrategy
 * @brief Balanced wait strategy that yields to other threads.
 *
 * This strategy spins initially, then yields the thread to the OS scheduler.
 * Provides good latency with reasonable CPU usage.
 * 
 * Performance characteristics:
 * - Latency: Medium (~100ns-1μs)
 * - CPU Usage: Medium (yields to other threads)
 * - Throughput: Good
 * - Power consumption: Medium
 */
class YieldingWaitStrategy : public WaitStrategy {
public:
    explicit YieldingWaitStrategy(int spin_tries = 100) 
        : spin_tries_(spin_tries) {}

    int64_t wait_for(
        int64_t sequence,
        std::shared_ptr<AtomicSequence> cursor,
        std::shared_ptr<AtomicSequence> dependent_sequence,
        SequenceBarrier& barrier) override {
        
        int64_t available_sequence;
        int counter = spin_tries_;
        
        while ((available_sequence = barrier.wait_for(sequence)) < sequence) {
            if (counter > 0) {
                // First try spinning with CPU pause
                --counter;
                #if defined(_MSC_VER)
                    _mm_pause();
                #elif defined(__GNUC__)
                    __builtin_ia32_pause();
                #else
                    std::this_thread::yield();
                #endif
            } else {
                // After spin tries, yield to other threads
                std::this_thread::yield();
            }
        }
        
        return available_sequence;
    }

    void signal_all_when_blocking() override {
        // No-op for yielding strategy
    }

private:
    const int spin_tries_;
};

/**
 * @class SleepingWaitStrategy
 * @brief CPU-friendly wait strategy that uses progressive sleep intervals.
 *
 * This strategy starts with spinning, then yielding, then sleeping with
 * progressively longer intervals. Provides the lowest CPU usage.
 * 
 * Performance characteristics:
 * - Latency: Higher (~1μs-1ms depending on sleep duration)
 * - CPU Usage: Lowest
 * - Throughput: Lower but more sustainable
 * - Power consumption: Lowest
 */
class SleepingWaitStrategy : public WaitStrategy {
public:
    explicit SleepingWaitStrategy(
        int spin_tries = 200,
        int yield_tries = 100,
        std::chrono::nanoseconds min_sleep = std::chrono::nanoseconds(1000),
        std::chrono::nanoseconds max_sleep = std::chrono::microseconds(1000))
        : spin_tries_(spin_tries),
          yield_tries_(yield_tries),
          min_sleep_(min_sleep),
          max_sleep_(max_sleep) {}

    int64_t wait_for(
        int64_t sequence,
        std::shared_ptr<AtomicSequence> cursor,
        std::shared_ptr<AtomicSequence> dependent_sequence,
        SequenceBarrier& barrier) override {
        
        int64_t available_sequence;
        int spin_counter = spin_tries_;
        int yield_counter = yield_tries_;
        auto sleep_duration = min_sleep_;
        
        while ((available_sequence = barrier.wait_for(sequence)) < sequence) {
            if (spin_counter > 0) {
                // Phase 1: Spin with CPU pause
                --spin_counter;
                #if defined(_MSC_VER)
                    _mm_pause();
                #elif defined(__GNUC__)
                    __builtin_ia32_pause();
                #else
                    std::this_thread::yield();
                #endif
            } else if (yield_counter > 0) {
                // Phase 2: Yield to other threads
                --yield_counter;
                std::this_thread::yield();
            } else {
                // Phase 3: Sleep with progressive backoff
                std::this_thread::sleep_for(sleep_duration);
                
                // Progressive backoff: double sleep time up to max
                sleep_duration = std::min(sleep_duration * 2, max_sleep_);
            }
        }
        
        return available_sequence;
    }

    void signal_all_when_blocking() override {
        // Could potentially interrupt sleeping threads, but not implemented
        // in this basic version for simplicity
    }

private:
    const int spin_tries_;
    const int yield_tries_;
    const std::chrono::nanoseconds min_sleep_;
    const std::chrono::nanoseconds max_sleep_;
};

/**
 * @class BlockingWaitStrategy
 * @brief Traditional blocking wait strategy using condition variables.
 *
 * This strategy uses condition variables for blocking/signaling, similar to
 * traditional queue implementations but integrated with the disruptor pattern.
 * 
 * Performance characteristics:
 * - Latency: Medium-High (~1-10μs context switch overhead)
 * - CPU Usage: Very low when blocking
 * - Throughput: Good for bursty workloads
 * - Power consumption: Very low
 */
class BlockingWaitStrategy : public WaitStrategy {
public:
    BlockingWaitStrategy() = default;

    int64_t wait_for(
        int64_t sequence,
        std::shared_ptr<AtomicSequence> cursor,
        std::shared_ptr<AtomicSequence> dependent_sequence,
        SequenceBarrier& barrier) override {
        
        int64_t available_sequence;
        
        // Quick check without locking
        if ((available_sequence = barrier.try_wait_for(sequence)) >= sequence) {
            return available_sequence;
        }
        
        // Block until sequence is available
        std::unique_lock<std::mutex> lock(mutex_);
        while ((available_sequence = barrier.try_wait_for(sequence)) < sequence) {
            condition_.wait(lock);
        }
        
        return available_sequence;
    }

    void signal_all_when_blocking() override {
        std::lock_guard<std::mutex> lock(mutex_);
        condition_.notify_all();
    }

private:
    std::mutex mutex_;
    std::condition_variable condition_;
};

/**
 * @enum WaitStrategyType
 * @brief Enumeration of available wait strategy types for configuration.
 */
enum class WaitStrategyType {
    BUSY_SPIN,      //!< Maximum performance, high CPU usage
    YIELDING,       //!< Balanced performance and CPU usage  
    SLEEPING,       //!< Lower CPU usage, higher latency
    BLOCKING        //!< Traditional blocking with condition variables
};

/**
 * @brief Factory function to create wait strategies based on type.
 * @param type The type of wait strategy to create.
 * @return A unique pointer to the created wait strategy.
 */
inline std::unique_ptr<WaitStrategy> create_wait_strategy(WaitStrategyType type) {
    switch (type) {
        case WaitStrategyType::BUSY_SPIN:
            return std::make_unique<BusySpinWaitStrategy>();
        case WaitStrategyType::YIELDING:
            return std::make_unique<YieldingWaitStrategy>();
        case WaitStrategyType::SLEEPING:
            return std::make_unique<SleepingWaitStrategy>();
        case WaitStrategyType::BLOCKING:
            return std::make_unique<BlockingWaitStrategy>();
        default:
            return std::make_unique<YieldingWaitStrategy>(); // Default fallback
    }
}

} // namespace nexus::core