// src/cpp/core/real_time_config.h

#pragma once

#include <vector>
#include <string>
#include <chrono>
#include <sstream>
#include <algorithm>
#include <memory>

namespace nexus::core {

/**
 * @struct RealTimeConfig
 * @brief Configuration parameters for real-time trading system optimization.
 *
 * This structure contains all configuration parameters needed for real-time
 * system optimization including CPU affinity, priority scheduling, cache warming,
 * and other low-latency trading optimizations.
 *
 * The configuration is designed to be:
 * - Zero-overhead when disabled
 * - Platform-agnostic with sensible defaults
 * - Tunable for different hardware configurations
 * - Safe with validation and fallback mechanisms
 */
struct RealTimeConfig {
    // --- CPU Affinity Configuration ---
    
    /**
     * @brief Enable CPU core affinity for deterministic scheduling.
     * When enabled, pins critical threads to specific CPU cores to reduce
     * context switching and improve cache locality.
     */
    bool enable_cpu_affinity = false;
    
    /**
     * @brief CPU cores to use for critical trading threads.
     * Specify which cores should be used for latency-critical operations.
     * Recommended: Use isolated cores not used by OS or other processes.
     * Example: {2, 3} for cores 2 and 3 on a 4+ core system.
     */
    std::vector<int> cpu_cores = {0, 1};
    
    /**
     * @brief Enable automatic CPU core detection and allocation.
     * When enabled, automatically selects optimal cores based on system topology.
     * Falls back to manual core selection if auto-detection fails.
     */
    bool auto_detect_optimal_cores = true;
    
    // --- Thread Priority Configuration ---
    
    /**
     * @brief Enable real-time priority scheduling for critical threads.
     * Provides deterministic latency by reducing preemption from other processes.
     * Requires elevated privileges on most systems.
     */
    bool enable_real_time_priority = false;
    
    /**
     * @brief Real-time priority level (1-99, higher = more priority).
     * Standard values:
     * - 99: Maximum priority (use sparingly)
     * - 80-90: High priority for critical trading threads
     * - 50-70: Medium priority for important but non-critical threads
     * - 1-30: Low priority for background tasks
     */
    int real_time_priority_level = 80;
    
    // --- Cache and Memory Optimization ---
    
    /**
     * @brief Enable cache warming strategies at startup.
     * Pre-loads critical data structures into CPU cache to reduce
     * cold start latency and improve initial performance.
     */
    bool enable_cache_warming = true;
    
    /**
     * @brief Cache warming iterations for critical data structures.
     * Number of passes through critical data to ensure cache population.
     * Higher values provide better warming but increase startup time.
     */
    size_t cache_warming_iterations = 3;
    
    /**
     * @brief Enable NUMA-aware memory allocation.
     * Optimizes memory allocation for multi-socket systems by keeping
     * memory allocation local to the CPU cores being used.
     */
    bool enable_numa_optimization = false;
    
    /**
     * @brief Preferred NUMA node for memory allocation (-1 = auto).
     * Specifies which NUMA node to prefer for memory allocations.
     * Use -1 for automatic detection based on CPU affinity.
     */
    int preferred_numa_node = -1;
    
    // --- System Resource Management ---
    
    /**
     * @brief Enable memory page locking to prevent swapping.
     * Locks process memory in physical RAM to eliminate swap-related latency.
     * Requires sufficient available RAM and elevated privileges.
     */
    bool enable_memory_locking = false;
    
    /**
     * @brief Enable huge pages for large memory allocations.
     * Uses system huge pages (2MB/1GB pages) to reduce TLB misses
     * and improve memory access performance for large data structures.
     */
    bool enable_huge_pages = false;
    
    /**
     * @brief CPU core isolation mode.
     * Determines how aggressively to isolate CPU cores from OS interference.
     * Options: "none", "soft", "hard"
     */
    std::string cpu_isolation_mode = "soft";
    
    // --- Performance Monitoring ---
    
    /**
     * @brief Enable detailed real-time performance monitoring.
     * Collects fine-grained performance metrics including latency histograms,
     * CPU utilization, and cache miss rates.
     */
    bool enable_performance_monitoring = true;
    
    /**
     * @brief Performance monitoring update interval.
     * How frequently to update performance metrics (in milliseconds).
     * Lower values provide more granular monitoring but add overhead.
     */
    std::chrono::milliseconds monitoring_interval{100};
    
    /**
     * @brief Enable latency spike detection and alerting.
     * Monitors for latency spikes beyond acceptable thresholds and
     * provides alerts for performance degradation.
     */
    bool enable_latency_spike_detection = true;
    
    /**
     * @brief Latency spike threshold (in microseconds).
     * Threshold above which latency spikes are reported.
     * Typical values: 10-100μs for HFT systems.
     */
    std::chrono::microseconds latency_spike_threshold{50};
    
    // --- Safety and Fallback Configuration ---
    
    /**
     * @brief Enable graceful fallback on configuration failures.
     * When enabled, system continues with reduced performance if
     * real-time optimizations fail rather than terminating.
     */
    bool enable_graceful_fallback = true;
    
    /**
     * @brief Timeout for real-time configuration setup (in seconds).
     * Maximum time allowed for real-time configuration before fallback.
     * Prevents hanging during system initialization.
     */
    std::chrono::seconds configuration_timeout{10};
    
    /**
     * @brief Validates the configuration parameters.
     * Checks for invalid values and corrects them where possible.
     * Should be called before using the configuration.
     */
    void validate() {
        // Validate CPU cores
        if (cpu_cores.empty()) {
            cpu_cores = {0, 1}; // Default to first two cores
        }
        
        // Remove duplicate cores and sort
        std::sort(cpu_cores.begin(), cpu_cores.end());
        cpu_cores.erase(std::unique(cpu_cores.begin(), cpu_cores.end()), cpu_cores.end());
        
        // Validate priority level
        if (real_time_priority_level < 1) real_time_priority_level = 1;
        if (real_time_priority_level > 99) real_time_priority_level = 99;
        
        // Validate cache warming iterations
        if (cache_warming_iterations == 0) cache_warming_iterations = 1;
        if (cache_warming_iterations > 10) cache_warming_iterations = 10;
        
        // Validate NUMA node
        if (preferred_numa_node < -1) preferred_numa_node = -1;
        
        // Validate CPU isolation mode
        if (cpu_isolation_mode != "none" && 
            cpu_isolation_mode != "soft" && 
            cpu_isolation_mode != "hard") {
            cpu_isolation_mode = "soft";
        }
        
        // Validate monitoring interval
        if (monitoring_interval < std::chrono::milliseconds{1}) {
            monitoring_interval = std::chrono::milliseconds{1};
        }
        if (monitoring_interval > std::chrono::seconds{10}) {
            monitoring_interval = std::chrono::seconds{10};
        }
        
        // Validate latency spike threshold
        if (latency_spike_threshold < std::chrono::microseconds{1}) {
            latency_spike_threshold = std::chrono::microseconds{1};
        }
        
        // Validate configuration timeout
        if (configuration_timeout < std::chrono::seconds{1}) {
            configuration_timeout = std::chrono::seconds{1};
        }
        if (configuration_timeout > std::chrono::minutes{5}) {
            configuration_timeout = std::chrono::minutes{5};
        }
    }
    
    /**
     * @brief Gets a string representation of the current configuration.
     * @return Configuration summary for logging and debugging.
     */
    std::string to_string() const {
        std::ostringstream oss;
        oss << "RealTimeConfig:\n";
        oss << "  CPU Affinity: " << (enable_cpu_affinity ? "enabled" : "disabled");
        if (enable_cpu_affinity) {
            oss << " (cores: ";
            for (size_t i = 0; i < cpu_cores.size(); ++i) {
                if (i > 0) oss << ",";
                oss << cpu_cores[i];
            }
            oss << ")";
        }
        oss << "\n";
        oss << "  Real-time Priority: " << (enable_real_time_priority ? "enabled" : "disabled");
        if (enable_real_time_priority) {
            oss << " (level: " << real_time_priority_level << ")";
        }
        oss << "\n";
        oss << "  Cache Warming: " << (enable_cache_warming ? "enabled" : "disabled");
        if (enable_cache_warming) {
            oss << " (iterations: " << cache_warming_iterations << ")";
        }
        oss << "\n";
        oss << "  NUMA Optimization: " << (enable_numa_optimization ? "enabled" : "disabled");
        if (enable_numa_optimization) {
            oss << " (node: " << preferred_numa_node << ")";
        }
        oss << "\n";
        oss << "  Performance Monitoring: " << (enable_performance_monitoring ? "enabled" : "disabled");
        return oss.str();
    }
};

} // namespace nexus::core