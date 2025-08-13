// src/cpp/core/atomic_sequence.h

#pragma once

#include <atomic>
#include <cstdint>
#include <thread>
#include <vector>
#include <memory>

namespace nexus::core {

/**
 * @class AtomicSequence
 * @brief Lock-free sequence number for coordination between producers and consumers.
 *
 * This class provides atomic sequence numbers used in the LMAX Disruptor pattern
 * to coordinate access to the ring buffer between multiple producers and consumers.
 * It ensures memory ordering and provides efficient ways to wait for specific
 * sequence values without using locks.
 */
class AtomicSequence {
public:
    /**
     * @brief Constructs an atomic sequence with an initial value.
     * @param initial_value The starting sequence number (default: -1).
     */
    explicit AtomicSequence(int64_t initial_value = -1) noexcept
        : sequence_(initial_value) {}

    /**
     * @brief Gets the current sequence value.
     * @return The current sequence number with acquire memory ordering.
     */
    int64_t get() const noexcept {
        return sequence_.load(std::memory_order_acquire);
    }

    /**
     * @brief Sets the sequence to a specific value.
     * @param value The new sequence value.
     */
    void set(int64_t value) noexcept {
        sequence_.store(value, std::memory_order_release);
    }

    /**
     * @brief Atomically increments and returns the new sequence value.
     * @return The new sequence value after incrementing.
     */
    int64_t increment_and_get() noexcept {
        return sequence_.fetch_add(1, std::memory_order_acq_rel) + 1;
    }

    /**
     * @brief Atomically adds a delta and returns the new sequence value.
     * @param delta The value to add to the sequence.
     * @return The new sequence value after adding delta.
     */
    int64_t add_and_get(int64_t delta) noexcept {
        return sequence_.fetch_add(delta, std::memory_order_acq_rel) + delta;
    }

    /**
     * @brief Attempts to set the sequence value using compare-and-swap.
     * @param expected_value The expected current value.
     * @param new_value The new value to set if current equals expected.
     * @return True if the swap was successful, false otherwise.
     */
    bool compare_and_set(int64_t expected_value, int64_t new_value) noexcept {
        return sequence_.compare_exchange_weak(
            expected_value, new_value, 
            std::memory_order_acq_rel, 
            std::memory_order_acquire
        );
    }

    /**
     * @brief Volatile read for the current sequence value.
     * @return The current sequence value with relaxed memory ordering.
     * @note Used in tight polling loops where memory ordering is less critical.
     */
    int64_t get_volatile() const noexcept {
        return sequence_.load(std::memory_order_relaxed);
    }

private:
    // Cache line padding to prevent false sharing
    alignas(64) std::atomic<int64_t> sequence_;
    char padding_[64 - sizeof(std::atomic<int64_t>)];
};

/**
 * @class SequenceBarrier
 * @brief Coordinates waiting for available sequences across multiple dependencies.
 *
 * The SequenceBarrier is used by consumers to wait for events to become available
 * while tracking multiple dependency sequences (e.g., other consumers that must
 * process events first).
 */
class SequenceBarrier {
public:
    /**
     * @brief Constructs a sequence barrier with producer and dependency sequences.
     * @param producer_sequence The producer's current sequence.
     * @param dependency_sequences Vector of consumer sequences that must advance first.
     */
    explicit SequenceBarrier(
        std::shared_ptr<AtomicSequence> producer_sequence,
        std::vector<std::shared_ptr<AtomicSequence>> dependency_sequences = {})
        : producer_sequence_(std::move(producer_sequence)),
          dependency_sequences_(std::move(dependency_sequences)) {}

    /**
     * @brief Waits for the requested sequence to become available.
     * @param sequence The sequence number to wait for.
     * @return The highest available sequence number (may be higher than requested).
     * @note This method blocks until the sequence becomes available.
     */
    int64_t wait_for(int64_t sequence) const {
        int64_t available_sequence;
        
        // First check if the producer has published the sequence
        while ((available_sequence = producer_sequence_->get()) < sequence) {
            // Use a hybrid approach: spin briefly, then yield
            static constexpr int SPIN_ITERATIONS = 100;
            for (int i = 0; i < SPIN_ITERATIONS && available_sequence < sequence; ++i) {
                available_sequence = producer_sequence_->get_volatile();
                if (available_sequence >= sequence) break;
                
                // CPU pause instruction for better performance in spin loops
                #if defined(_MSC_VER)
                    _mm_pause();
                #elif defined(__GNUC__)
                    __builtin_ia32_pause();
                #else
                    std::this_thread::yield();
                #endif
            }
            
            if (available_sequence < sequence) {
                std::this_thread::yield();
            }
        }
        
        // Check dependency sequences to ensure proper ordering
        return get_minimum_sequence_of_dependencies(available_sequence);
    }

    /**
     * @brief Checks if a sequence is available without blocking.
     * @param sequence The sequence number to check.
     * @return The highest available sequence if >= requested sequence, -1 otherwise.
     */
    int64_t try_wait_for(int64_t sequence) const {
        int64_t available_sequence = producer_sequence_->get();
        if (available_sequence < sequence) {
            return -1;
        }
        
        return get_minimum_sequence_of_dependencies(available_sequence);
    }

    /**
     * @brief Gets the highest published sequence number.
     * @return The current producer sequence value.
     */
    int64_t get_cursor() const noexcept {
        return producer_sequence_->get();
    }

private:
    /**
     * @brief Finds the minimum sequence among all dependencies.
     * @param available_sequence The available sequence from producer.
     * @return The minimum sequence ensuring all dependencies are satisfied.
     */
    int64_t get_minimum_sequence_of_dependencies(int64_t available_sequence) const {
        if (dependency_sequences_.empty()) {
            return available_sequence;
        }
        
        int64_t minimum = available_sequence;
        for (const auto& dependency : dependency_sequences_) {
            int64_t dependency_sequence = dependency->get();
            if (dependency_sequence < minimum) {
                minimum = dependency_sequence;
            }
        }
        
        return minimum;
    }

    std::shared_ptr<AtomicSequence> producer_sequence_;
    std::vector<std::shared_ptr<AtomicSequence>> dependency_sequences_;
};

} // namespace nexus::core