// src/cpp/core/high_resolution_clock.h

#pragma once

#include <chrono>
#include <cstdint>

namespace nexus::core {

/**
 * @class HighResolutionClock
 * @brief Hardware timestamp counter (TSC) access for nanosecond precision timing.
 *
 * This class provides access to the highest resolution timing mechanisms available
 * on the target platform, including direct hardware timestamp counter access for
 * ultra-low latency measurement and optimization.
 *
 * Key features:
 * - Hardware TSC access for sub-nanosecond precision
 * - Cross-platform high-resolution timing
 * - Calibrated conversion from TSC to nanoseconds
 * - Thread-safe operations with minimal overhead
 * - CPU frequency detection and calibration
 *
 * Performance characteristics:
 * - TSC read: ~10-20 CPU cycles
 * - Nanosecond conversion: ~5-10 CPU cycles
 * - Calibration overhead: One-time at initialization
 */
class HighResolutionClock {
public:
    /**
     * @brief Initializes the high-resolution clock system.
     * 
     * This method calibrates the TSC frequency and sets up the conversion
     * factors for accurate nanosecond timing. Should be called once at
     * application startup.
     */
    static void initialize();

    /**
     * @brief Gets the current hardware timestamp counter value.
     * @return Raw TSC value with maximum precision.
     * 
     * This is the fastest timing method available, providing direct access
     * to the CPU's timestamp counter. Use for ultra-low latency measurements.
     */
    static uint64_t get_tsc() noexcept;

    /**
     * @brief Gets the current time in nanoseconds since epoch.
     * @return Current time as nanoseconds with maximum available precision.
     * 
     * Provides nanosecond precision timing calibrated against system time.
     * Suitable for most high-frequency trading latency measurements.
     */
    static std::chrono::nanoseconds get_nanoseconds() noexcept;

    /**
     * @brief Converts a TSC timestamp to nanoseconds.
     * @param tsc_timestamp The TSC timestamp to convert.
     * @return Equivalent time in nanoseconds.
     * 
     * Allows conversion of previously captured TSC values to human-readable
     * nanosecond timestamps using calibrated conversion factors.
     */
    static std::chrono::nanoseconds tsc_to_nanoseconds(uint64_t tsc_timestamp) noexcept;

    /**
     * @brief Gets the TSC frequency in Hz.
     * @return TSC frequency for timing calculations.
     * 
     * Returns the calibrated TSC frequency, useful for custom timing
     * calculations and validation of timing measurements.
     */
    static uint64_t get_tsc_frequency() noexcept;

    /**
     * @brief Checks if the TSC is stable and reliable.
     * @return True if TSC is suitable for timing measurements.
     * 
     * Verifies that the TSC is invariant (constant frequency) and synchronized
     * across CPU cores, ensuring reliable timing measurements.
     */
    static bool is_tsc_reliable() noexcept;

    /**
     * @brief Gets a high-resolution timestamp for performance measurement.
     * @return High-resolution time point for interval measurement.
     * 
     * Provides the standard high-resolution clock timestamp suitable for
     * measuring time intervals with maximum available precision.
     */
    static std::chrono::high_resolution_clock::time_point get_time_point() noexcept;

    /**
     * @brief Calculates the difference between two TSC timestamps in nanoseconds.
     * @param start_tsc The starting TSC timestamp.
     * @param end_tsc The ending TSC timestamp.
     * @return Time difference in nanoseconds.
     * 
     * Efficiently calculates time differences using TSC values, avoiding
     * the overhead of converting individual timestamps.
     */
    static double calculate_tsc_diff_ns(uint64_t start_tsc, uint64_t end_tsc) noexcept;

    /**
     * @brief Performs a timing calibration check.
     * @return True if timing calibration is within acceptable bounds.
     * 
     * Validates that the timing calibration is accurate and stable,
     * useful for runtime verification of timing system integrity.
     */
    static bool validate_calibration();

private:
    // Calibration state
    static bool initialized_;
    static uint64_t tsc_frequency_;
    static double tsc_to_ns_multiplier_;
    static bool tsc_reliable_;
    static std::chrono::nanoseconds epoch_offset_;

    /**
     * @brief Calibrates the TSC frequency against system time.
     */
    static void calibrate_tsc_frequency();

    /**
     * @brief Detects TSC capabilities and reliability.
     */
    static void detect_tsc_capabilities();

    /**
     * @brief Platform-specific TSC reading implementation.
     */
    static uint64_t read_tsc_impl() noexcept;
};

/**
 * @brief RAII helper class for measuring elapsed time with high precision.
 * 
 * This class provides a convenient way to measure elapsed time for code blocks
 * using the highest available precision timing. Automatically captures start
 * time on construction and calculates elapsed time on destruction or query.
 */
class HighResolutionTimer {
public:
    /**
     * @brief Constructs timer and captures start time.
     */
    HighResolutionTimer() noexcept : start_tsc_(HighResolutionClock::get_tsc()) {}

    /**
     * @brief Gets elapsed time since construction in nanoseconds.
     * @return Elapsed time as floating-point nanoseconds.
     */
    double elapsed_nanoseconds() const noexcept {
        uint64_t end_tsc = HighResolutionClock::get_tsc();
        return HighResolutionClock::calculate_tsc_diff_ns(start_tsc_, end_tsc);
    }

    /**
     * @brief Gets elapsed time since construction as chrono duration.
     * @return Elapsed time as nanoseconds duration.
     */
    std::chrono::nanoseconds elapsed_duration() const noexcept {
        return std::chrono::nanoseconds(static_cast<int64_t>(elapsed_nanoseconds()));
    }

    /**
     * @brief Resets the timer to current time.
     */
    void reset() noexcept {
        start_tsc_ = HighResolutionClock::get_tsc();
    }

private:
    uint64_t start_tsc_;
};

} // namespace nexus::core