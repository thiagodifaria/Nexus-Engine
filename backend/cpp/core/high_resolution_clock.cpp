// src/cpp/core/high_resolution_clock.cpp

#include "core/high_resolution_clock.h"
#include <iostream>
#include <thread>
#include <algorithm>
#include <vector>
#include <numeric>

#ifdef _WIN32
#include <Windows.h>
#include <intrin.h>
#elif defined(__linux__) || defined(__APPLE__)
#include <unistd.h>
#include <sys/time.h>
#if defined(__x86_64__) || defined(__i386__)
#include <x86intrin.h>
#endif
#endif

namespace nexus::core {

// Static member initialization
bool HighResolutionClock::initialized_ = false;
uint64_t HighResolutionClock::tsc_frequency_ = 0;
double HighResolutionClock::tsc_to_ns_multiplier_ = 0.0;
bool HighResolutionClock::tsc_reliable_ = false;
std::chrono::nanoseconds HighResolutionClock::epoch_offset_{0};

void HighResolutionClock::initialize() {
    if (initialized_) [[likely]] {
        return; // Already initialized
    }

    std::cout << "HighResolutionClock: Initializing high-resolution timing system..." << std::endl;

    // Detect TSC capabilities first
    detect_tsc_capabilities();
    
    if (tsc_reliable_) {
        // Calibrate TSC frequency against system time
        calibrate_tsc_frequency();
        
        // Calculate conversion multiplier
        if (tsc_frequency_ > 0) {
            tsc_to_ns_multiplier_ = 1000000000.0 / static_cast<double>(tsc_frequency_);
        }
        
        // Set epoch offset for nanosecond conversions
        auto system_now = std::chrono::system_clock::now();
        auto epoch_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            system_now.time_since_epoch());
        uint64_t tsc_now = get_tsc();
        
        epoch_offset_ = epoch_ns - std::chrono::nanoseconds(
            static_cast<int64_t>(tsc_now * tsc_to_ns_multiplier_));
    }
    
    initialized_ = true;
    
    std::cout << "HighResolutionClock: Initialization complete" << std::endl;
    std::cout << "  - TSC reliable: " << (tsc_reliable_ ? "Yes" : "No") << std::endl;
    if (tsc_reliable_) {
        std::cout << "  - TSC frequency: " << (tsc_frequency_ / 1000000) << " MHz" << std::endl;
        std::cout << "  - TSC to ns multiplier: " << tsc_to_ns_multiplier_ << std::endl;
    }
}

uint64_t HighResolutionClock::get_tsc() noexcept {
    if (!initialized_) [[unlikely]] {
        // Fallback to basic implementation if not initialized
        return read_tsc_impl();
    }
    
    return read_tsc_impl();
}

std::chrono::nanoseconds HighResolutionClock::get_nanoseconds() noexcept {
    if (!initialized_ || !tsc_reliable_) [[unlikely]] {
        // Fallback to high_resolution_clock if TSC not available
        auto now = std::chrono::high_resolution_clock::now();
        return std::chrono::duration_cast<std::chrono::nanoseconds>(
            now.time_since_epoch());
    }
    
    uint64_t tsc = get_tsc();
    auto tsc_ns = std::chrono::nanoseconds(
        static_cast<int64_t>(tsc * tsc_to_ns_multiplier_));
    
    return tsc_ns + epoch_offset_;
}

std::chrono::nanoseconds HighResolutionClock::tsc_to_nanoseconds(uint64_t tsc_timestamp) noexcept {
    if (!initialized_ || !tsc_reliable_) [[unlikely]] {
        return std::chrono::nanoseconds{0};
    }
    
    auto tsc_ns = std::chrono::nanoseconds(
        static_cast<int64_t>(tsc_timestamp * tsc_to_ns_multiplier_));
    
    return tsc_ns + epoch_offset_;
}

uint64_t HighResolutionClock::get_tsc_frequency() noexcept {
    return tsc_frequency_;
}

bool HighResolutionClock::is_tsc_reliable() noexcept {
    return tsc_reliable_;
}

std::chrono::high_resolution_clock::time_point HighResolutionClock::get_time_point() noexcept {
    return std::chrono::high_resolution_clock::now();
}

double HighResolutionClock::calculate_tsc_diff_ns(uint64_t start_tsc, uint64_t end_tsc) noexcept {
    if (!initialized_ || !tsc_reliable_) [[unlikely]] {
        return 0.0;
    }
    
    if (end_tsc < start_tsc) [[unlikely]] {
        // Handle TSC wraparound (very rare on 64-bit systems)
        uint64_t diff = (UINT64_MAX - start_tsc) + end_tsc + 1;
        return static_cast<double>(diff) * tsc_to_ns_multiplier_;
    }
    
    uint64_t diff = end_tsc - start_tsc;
    return static_cast<double>(diff) * tsc_to_ns_multiplier_;
}

bool HighResolutionClock::validate_calibration() {
    if (!initialized_ || !tsc_reliable_) {
        return false;
    }
    
    // Perform a quick calibration check
    const int num_samples = 10;
    const auto sleep_duration = std::chrono::milliseconds(10);
    
    std::vector<double> ratios;
    ratios.reserve(num_samples);
    
    for (int i = 0; i < num_samples; ++i) {
        auto start_time = std::chrono::high_resolution_clock::now();
        uint64_t start_tsc = get_tsc();
        
        std::this_thread::sleep_for(sleep_duration);
        
        auto end_time = std::chrono::high_resolution_clock::now();
        uint64_t end_tsc = get_tsc();
        
        auto actual_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            end_time - start_time).count();
        double tsc_ns = calculate_tsc_diff_ns(start_tsc, end_tsc);
        
        if (actual_ns > 0 && tsc_ns > 0) {
            ratios.push_back(tsc_ns / actual_ns);
        }
    }
    
    if (ratios.empty()) {
        return false;
    }
    
    // Calculate mean and check variance
    double mean = std::accumulate(ratios.begin(), ratios.end(), 0.0) / ratios.size();
    double variance = 0.0;
    
    for (double ratio : ratios) {
        variance += (ratio - mean) * (ratio - mean);
    }
    variance /= ratios.size();
    
    // Accept calibration if ratio is close to 1.0 with low variance
    bool ratio_good = (mean >= 0.95 && mean <= 1.05);
    bool variance_low = (variance < 0.01);
    
    return ratio_good && variance_low;
}

void HighResolutionClock::calibrate_tsc_frequency() {
    const auto calibration_duration = std::chrono::milliseconds(100);
    const int num_calibrations = 5;
    
    std::vector<uint64_t> frequency_samples;
    frequency_samples.reserve(num_calibrations);
    
    for (int i = 0; i < num_calibrations; ++i) {
        auto start_time = std::chrono::high_resolution_clock::now();
        uint64_t start_tsc = read_tsc_impl();
        
        std::this_thread::sleep_for(calibration_duration);
        
        auto end_time = std::chrono::high_resolution_clock::now();
        uint64_t end_tsc = read_tsc_impl();
        
        auto elapsed_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            end_time - start_time).count();
        
        if (elapsed_ns > 0 && end_tsc > start_tsc) {
            uint64_t tsc_diff = end_tsc - start_tsc;
            uint64_t frequency = (tsc_diff * 1000000000ULL) / elapsed_ns;
            frequency_samples.push_back(frequency);
        }
    }
    
    if (!frequency_samples.empty()) {
        // Use median to reduce impact of outliers
        std::sort(frequency_samples.begin(), frequency_samples.end());
        size_t median_idx = frequency_samples.size() / 2;
        tsc_frequency_ = frequency_samples[median_idx];
    }
}

void HighResolutionClock::detect_tsc_capabilities() {
    tsc_reliable_ = false;
    
#if defined(__x86_64__) || defined(__i386__)
    // Check for invariant TSC support
    uint32_t eax, ebx, ecx, edx;
    
    // CPUID leaf 0x80000007, EDX bit 8 indicates invariant TSC
#ifdef _WIN32
    int cpu_info[4];
    __cpuid(cpu_info, 0x80000007);
    edx = cpu_info[3];
#elif defined(__GNUC__)
    __asm__("cpuid" : "=a"(eax), "=b"(ebx), "=c"(ecx), "=d"(edx) : "a"(0x80000007));
#endif
    
    bool invariant_tsc = (edx & (1 << 8)) != 0;
    
    if (invariant_tsc) {
        tsc_reliable_ = true;
    }
    
#elif defined(__aarch64__) || defined(__arm__)
    // ARM has cycle counters but they may not be accessible from user space
    // For now, mark as unreliable and fall back to standard timing
    tsc_reliable_ = false;
#endif
    
    // Additional platform-specific checks could be added here
}

uint64_t HighResolutionClock::read_tsc_impl() noexcept {
#if defined(__x86_64__) || defined(__i386__)
    // Use rdtsc instruction for x86/x64
#ifdef _WIN32
    return __rdtsc();
#elif defined(__GNUC__)
    return __rdtsc();
#endif
    
#elif defined(__aarch64__)
    // ARM64 virtual counter
    uint64_t val;
    __asm__ volatile("mrs %0, cntvct_el0" : "=r"(val));
    return val;
    
#elif defined(__arm__)
    // ARM32 - may not be available in user space
    uint32_t val;
    __asm__ volatile("mrc p15, 0, %0, c9, c13, 0" : "=r"(val));
    return static_cast<uint64_t>(val);
    
#else
    // Fallback to high_resolution_clock for unsupported architectures
    auto now = std::chrono::high_resolution_clock::now();
    return static_cast<uint64_t>(
        std::chrono::duration_cast<std::chrono::nanoseconds>(
            now.time_since_epoch()).count());
#endif
}

} // namespace nexus::core