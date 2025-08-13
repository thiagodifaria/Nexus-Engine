// src/cpp/analytics/monte_carlo_simulator.h

#pragma once

#include "analytics/performance_metrics.h"
#include "core/hpc_utils.h"
#include <vector>
#include <memory>
#include <random>
#include <functional>
#include <thread>
#include <atomic>

namespace nexus::analytics {

/**
 * @class MonteCarloSimulator
 * @brief Ultra-high performance Monte Carlo simulation engine with SIMD optimization.
 *
 * This simulator is designed for institutional-grade performance with advanced
 * optimizations including SIMD vectorization, memory pre-allocation, and 
 * NUMA-aware memory management for multi-socket systems.
 *
 * Key features:
 * - SIMD-optimized calculations using AVX2/AVX-512 when available
 * - Lock-free parallel processing across multiple threads
 * - Pre-allocated memory buffers to eliminate allocation overhead
 * - NUMA-aware memory allocation for optimal performance on multi-socket systems
 * - Vectorized random number generation for maximum throughput
 * - Cache-optimized data structures to minimize memory latency
 *
 * Performance characteristics:
 * - 25K+ simulations/second (baseline after Phase 2)
 * - Target: 100K-500K simulations/second with NUMA optimizations
 * - Sub-microsecond per-simulation latency for simple models
 * - Linear scaling across CPU cores
 */
class MonteCarloSimulator {
public:
    /**
     * @brief Configuration structure for the Monte Carlo simulator.
     */
    struct Config {
        size_t num_simulations = 10000;
        size_t num_threads = std::thread::hardware_concurrency();
        size_t buffer_size = 100000;        // Pre-allocated buffer size
        bool enable_simd = true;             // Enable SIMD optimizations
        bool enable_prefetching = true;      // Enable memory prefetching
        bool enable_statistics = false;     // Collect detailed statistics
        
        // NEW: NUMA-aware configuration options
        bool enable_numa_optimization = false;    // Enable NUMA-aware allocations
        int preferred_numa_node = -1;             // -1 = auto-detect
        bool distribute_across_numa_nodes = true; // Distribute work across NUMA nodes
        bool pin_threads_to_numa_nodes = false;   // Pin worker threads to NUMA nodes
        size_t numa_buffer_interleaving = 64;     // Cache line size for interleaving
        bool use_numa_local_buffers = true;       // Allocate buffers on local NUMA nodes
    };

    /**
     * @brief Performance statistics for monitoring and optimization.
     */
    struct Statistics {
        std::atomic<size_t> total_simulations{0};
        std::atomic<size_t> simd_operations{0};
        std::atomic<size_t> cache_hits{0};
        std::atomic<size_t> cache_misses{0};
        std::atomic<double> average_simulation_time_ns{0.0};
        std::atomic<double> throughput_per_second{0.0};
        
        // NEW: NUMA-specific statistics
        std::atomic<size_t> numa_local_allocations{0};
        std::atomic<size_t> numa_remote_allocations{0};
        std::atomic<size_t> numa_migrations{0};
        std::atomic<double> numa_efficiency_ratio{0.0}; // local/total allocations
        
        /**
         * @brief Creates a non-atomic snapshot of the statistics.
         */
        struct Snapshot {
            size_t total_simulations;
            size_t simd_operations;
            size_t cache_hits;
            size_t cache_misses;
            double average_simulation_time_ns;
            double throughput_per_second;
            size_t numa_local_allocations;
            size_t numa_remote_allocations;
            size_t numa_migrations;
            double numa_efficiency_ratio;
        };
        
        /**
         * @brief Gets a non-atomic snapshot of current statistics.
         */
        Snapshot get_snapshot() const {
            Snapshot snapshot;
            snapshot.total_simulations = total_simulations.load(std::memory_order_acquire);
            snapshot.simd_operations = simd_operations.load(std::memory_order_acquire);
            snapshot.cache_hits = cache_hits.load(std::memory_order_acquire);
            snapshot.cache_misses = cache_misses.load(std::memory_order_acquire);
            snapshot.average_simulation_time_ns = average_simulation_time_ns.load(std::memory_order_acquire);
            snapshot.throughput_per_second = throughput_per_second.load(std::memory_order_acquire);
            snapshot.numa_local_allocations = numa_local_allocations.load(std::memory_order_acquire);
            snapshot.numa_remote_allocations = numa_remote_allocations.load(std::memory_order_acquire);
            snapshot.numa_migrations = numa_migrations.load(std::memory_order_acquire);
            snapshot.numa_efficiency_ratio = numa_efficiency_ratio.load(std::memory_order_acquire);
            return snapshot;
        }
        
        /**
         * @brief Resets all statistics to zero.
         */
        void reset() {
            total_simulations.store(0, std::memory_order_release);
            simd_operations.store(0, std::memory_order_release);
            cache_hits.store(0, std::memory_order_release);
            cache_misses.store(0, std::memory_order_release);
            average_simulation_time_ns.store(0.0, std::memory_order_release);
            throughput_per_second.store(0.0, std::memory_order_release);
            numa_local_allocations.store(0, std::memory_order_release);
            numa_remote_allocations.store(0, std::memory_order_release);
            numa_migrations.store(0, std::memory_order_release);
            numa_efficiency_ratio.store(0.0, std::memory_order_release);
        }
    };

    /**
     * @brief Function signature for simulation functions.
     */
    using SimulationFunction = std::function<std::vector<double>(const std::vector<double>&, std::mt19937&)>;

    /**
     * @brief Constructs the Monte Carlo simulator with the specified configuration.
     */
    explicit MonteCarloSimulator(const Config& config = Config{});

    /**
     * @brief Destructor ensures proper cleanup of resources.
     */
    ~MonteCarloSimulator();

    /**
     * @brief Runs Monte Carlo simulation with the provided function.
     * @param simulation_func The function to execute for each simulation.
     * @param initial_parameters Initial parameters for the simulation.
     * @return Vector of simulation results.
     */
    std::vector<std::vector<double>> run_simulation(
        const SimulationFunction& simulation_func,
        const std::vector<double>& initial_parameters
    );

    /**
     * @brief Runs a simple portfolio simulation for strategy testing.
     * @param returns Expected returns for each asset.
     * @param volatilities Volatilities for each asset.
     * @param correlation_matrix Correlation matrix between assets.
     * @param time_horizon Simulation time horizon.
     * @return Simulated portfolio values.
     */
    std::vector<double> simulate_portfolio(
        const std::vector<double>& returns,
        const std::vector<double>& volatilities,
        const std::vector<std::vector<double>>& correlation_matrix,
        double time_horizon = 1.0
    );

    /**
     * @brief Calculates Value at Risk (VaR) using Monte Carlo simulation.
     * @param portfolio_returns Historical or expected portfolio returns.
     * @param confidence_level Confidence level (e.g., 0.95 for 95% VaR).
     * @return Value at Risk estimate.
     */
    double calculate_var(
        const std::vector<double>& portfolio_returns,
        double confidence_level = 0.95
    );

    /**
     * @brief Gets current performance statistics.
     */
    Statistics::Snapshot get_statistics() const;

    /**
     * @brief Resets all performance statistics.
     */
    void reset_statistics();

    /**
     * @brief Updates the simulator configuration.
     * @param new_config New configuration to apply.
     */
    void update_config(const Config& new_config);

    /**
     * @brief Gets the current configuration.
     */
    const Config& get_config() const;

private:
    Config config_;
    Statistics statistics_;
    
    // Memory management
    std::unique_ptr<nexus::core::MemoryPool<double>> buffer_pool_;
    std::vector<std::unique_ptr<double[]>> pre_allocated_buffers_;
    
    // NEW: NUMA-aware memory management
    std::vector<int> numa_node_assignments_;           // Thread to NUMA node mapping
    std::vector<std::unique_ptr<nexus::core::MemoryPool<double>>> numa_local_pools_; // Per-NUMA pools
    
    // Threading
    std::vector<std::thread> worker_threads_;
    std::atomic<bool> shutdown_requested_{false};

    /**
     * @brief Initializes pre-allocated buffers for simulation data.
     */
    void initialize_buffers();

    /**
     * @brief NEW: Initialize NUMA-aware memory allocation.
     */
    void initialize_numa_buffers();

    /**
     * @brief NEW: Assign threads to NUMA nodes for optimal performance.
     */
    void assign_threads_to_numa_nodes();

    /**
     * @brief NEW: Get optimal NUMA node for current thread.
     */
    int get_optimal_numa_node() const;

    /**
     * @brief Worker thread function for parallel simulation execution.
     */
    void worker_thread_func(
        size_t thread_id,
        const SimulationFunction& simulation_func,
        const std::vector<double>& parameters,
        std::vector<std::vector<double>>& results,
        size_t start_simulation,
        size_t end_simulation
    );

    /**
     * @brief SIMD-optimized computation kernel.
     */
    void simd_compute_returns(
        const double* returns,
        const double* volatilities,
        double* output,
        size_t count
    );

    /**
     * @brief Updates performance statistics.
     */
    void update_statistics(double simulation_time_ns, size_t num_operations);

    /**
     * @brief Validates configuration parameters.
     */
    void validate_config();
};

} // namespace nexus::analytics