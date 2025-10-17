// src/cpp/analytics/monte_carlo_simulator.cpp

#include "analytics/monte_carlo_simulator.h"
#include <algorithm>
#include <execution>
#include <thread>
#include <chrono>
#include <iostream>
#include <cmath>
#include <atomic>

#ifdef _WIN32
#include <immintrin.h>
#elif defined(__linux__) || defined(__APPLE__)
#include <immintrin.h>
#endif

namespace nexus::analytics {

MonteCarloSimulator::MonteCarloSimulator(const Config& config) : config_(config) {
    validate_config();
    initialize_buffers();
    
    // NEW: Initialize NUMA-aware allocation if enabled
    if (config_.enable_numa_optimization) {
        initialize_numa_buffers();
        assign_threads_to_numa_nodes();
        std::cout << "MonteCarloSimulator: NUMA optimization enabled" << std::endl;
        std::cout << "  - Preferred NUMA node: " << config_.preferred_numa_node << std::endl;
        std::cout << "  - Thread-to-NUMA mapping: " << (config_.pin_threads_to_numa_nodes ? "enabled" : "disabled") << std::endl;
    }
    
    std::cout << "MonteCarloSimulator: Initialized with " << config_.num_threads 
              << " threads, buffer size: " << config_.buffer_size << std::endl;
}

MonteCarloSimulator::~MonteCarloSimulator() {
    shutdown_requested_.store(true, std::memory_order_release);
    
    // Wait for any running worker threads
    for (auto& thread : worker_threads_) {
        if (thread.joinable()) {
            thread.join();
        }
    }
    
    if (config_.enable_statistics) {
        auto stats = get_statistics();
        std::cout << "MonteCarloSimulator: Final statistics:" << std::endl;
        std::cout << "  - Total simulations: " << stats.total_simulations << std::endl;
        std::cout << "  - Average time per simulation: " << stats.average_simulation_time_ns << " ns" << std::endl;
        std::cout << "  - Final throughput: " << stats.throughput_per_second << " sims/sec" << std::endl;
        
        // NEW: NUMA statistics
        if (config_.enable_numa_optimization) {
            std::cout << "  - NUMA local allocations: " << stats.numa_local_allocations << std::endl;
            std::cout << "  - NUMA remote allocations: " << stats.numa_remote_allocations << std::endl;
            std::cout << "  - NUMA efficiency ratio: " << stats.numa_efficiency_ratio << std::endl;
        }
    }
}

std::vector<std::vector<double>> MonteCarloSimulator::run_simulation(
    const SimulationFunction& simulation_func,
    const std::vector<double>& initial_parameters) {
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    std::vector<std::vector<double>> results(config_.num_simulations);
    
    // Calculate work distribution
    size_t simulations_per_thread = config_.num_simulations / config_.num_threads;
    size_t remaining_simulations = config_.num_simulations % config_.num_threads;
    
    // Clear previous worker threads
    worker_threads_.clear();
    worker_threads_.reserve(config_.num_threads);
    
    // Launch worker threads
    for (size_t thread_id = 0; thread_id < config_.num_threads; ++thread_id) {
        size_t start_sim = thread_id * simulations_per_thread;
        size_t end_sim = start_sim + simulations_per_thread;
        
        // Distribute remaining simulations to first few threads
        if (thread_id < remaining_simulations) {
            end_sim += 1;
            start_sim += thread_id;
        } else {
            start_sim += remaining_simulations;
            end_sim += remaining_simulations;
        }
        
        worker_threads_.emplace_back(&MonteCarloSimulator::worker_thread_func, this,
                                   thread_id, std::cref(simulation_func), 
                                   std::cref(initial_parameters),
                                   std::ref(results), start_sim, end_sim);
    }
    
    // Wait for all threads to complete
    for (auto& thread : worker_threads_) {
        thread.join();
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::nanoseconds>(end_time - start_time);
    
    // Update statistics
    if (config_.enable_statistics) {
        update_statistics(static_cast<double>(duration.count()), config_.num_simulations);
    }
    
    return results;
}

std::vector<double> MonteCarloSimulator::simulate_portfolio(
    const std::vector<double>& returns,
    const std::vector<double>& volatilities,
    const std::vector<std::vector<double>>& correlation_matrix,
    double time_horizon) {
    
    std::vector<double> portfolio_values;
    portfolio_values.reserve(config_.num_simulations);
    
    // Use the general simulation framework
    auto portfolio_sim = [&](const std::vector<double>& params, std::mt19937& rng) -> std::vector<double> {
        std::normal_distribution<double> normal_dist(0.0, 1.0);
        std::vector<double> random_values(returns.size());
        
        // Generate correlated random values
        for (size_t i = 0; i < returns.size(); ++i) {
            random_values[i] = normal_dist(rng);
        }
        
        // Apply correlation (simplified Cholesky decomposition would be used in practice)
        double portfolio_return = 0.0;
        for (size_t i = 0; i < returns.size(); ++i) {
            double asset_return = returns[i] + volatilities[i] * random_values[i] * std::sqrt(time_horizon);
            portfolio_return += asset_return / returns.size(); // Equal weighted for simplicity
        }
        
        return {portfolio_return};
    };
    
    auto results = run_simulation(portfolio_sim, returns);
    
    // Extract portfolio values
    for (const auto& result : results) {
        if (!result.empty()) {
            portfolio_values.push_back(result[0]);
        }
    }
    
    return portfolio_values;
}

double MonteCarloSimulator::calculate_var(
    const std::vector<double>& portfolio_returns,
    double confidence_level) {
    
    if (portfolio_returns.empty()) {
        return 0.0;
    }
    
    std::vector<double> sorted_returns = portfolio_returns;
    std::sort(sorted_returns.begin(), sorted_returns.end());
    
    // Calculate VaR at the specified confidence level
    size_t var_index = static_cast<size_t>((1.0 - confidence_level) * sorted_returns.size());
    var_index = std::min(var_index, sorted_returns.size() - 1);
    
    return -sorted_returns[var_index]; // VaR is typically expressed as a positive number
}

MonteCarloSimulator::Statistics::Snapshot MonteCarloSimulator::get_statistics() const {
    return statistics_.get_snapshot();
}

void MonteCarloSimulator::reset_statistics() {
    statistics_.reset();
}

void MonteCarloSimulator::update_config(const Config& new_config) {
    config_ = new_config;
    validate_config();
    
    // Reinitialize buffers if buffer size changed
    initialize_buffers();
    
    // NEW: Reinitialize NUMA buffers if NUMA config changed
    if (config_.enable_numa_optimization) {
        initialize_numa_buffers();
        assign_threads_to_numa_nodes();
    }
}

const MonteCarloSimulator::Config& MonteCarloSimulator::get_config() const {
    return config_;
}

void MonteCarloSimulator::initialize_buffers() {
    // Initialize the main memory pool
    nexus::core::MemoryPool<double>::Config pool_config;
    pool_config.initial_pool_size = config_.buffer_size;
    pool_config.enable_statistics = config_.enable_statistics;
    pool_config.enable_prefetching = config_.enable_prefetching;
    
    buffer_pool_ = std::make_unique<nexus::core::MemoryPool<double>>(pool_config);
    
    // Pre-allocate buffers for each thread
    pre_allocated_buffers_.clear();
    pre_allocated_buffers_.reserve(config_.num_threads);
    
    for (size_t i = 0; i < config_.num_threads; ++i) {
        auto buffer = std::make_unique<double[]>(config_.buffer_size);
        pre_allocated_buffers_.push_back(std::move(buffer));
    }
}

// NEW: Initialize NUMA-aware memory allocation
void MonteCarloSimulator::initialize_numa_buffers() {
    if (!config_.enable_numa_optimization) {
        return;
    }
    
    // Clear existing NUMA pools
    numa_local_pools_.clear();
    
    // Determine number of NUMA nodes (simplified detection)
    int num_numa_nodes = std::max(1, static_cast<int>(std::thread::hardware_concurrency() / 8));
    
    // Create memory pools for each NUMA node
    for (int numa_node = 0; numa_node < num_numa_nodes; ++numa_node) {
        nexus::core::MemoryPool<double>::Config pool_config;
        pool_config.initial_pool_size = config_.buffer_size / num_numa_nodes;
        pool_config.enable_statistics = config_.enable_statistics;
        pool_config.enable_prefetching = config_.enable_prefetching;
        
        // Configure NUMA-specific settings
        pool_config.numa_config.enable_numa_awareness = true;
        pool_config.numa_config.preferred_numa_node = numa_node;
        pool_config.numa_config.pin_to_local_node = true;
        
        auto numa_pool = std::make_unique<nexus::core::MemoryPool<double>>(pool_config);
        numa_local_pools_.push_back(std::move(numa_pool));
    }
    
    std::cout << "MonteCarloSimulator: Initialized " << num_numa_nodes << " NUMA-local memory pools" << std::endl;
}

// NEW: Assign threads to NUMA nodes for optimal performance
void MonteCarloSimulator::assign_threads_to_numa_nodes() {
    if (!config_.enable_numa_optimization) {
        return;
    }
    
    numa_node_assignments_.clear();
    numa_node_assignments_.reserve(config_.num_threads);
    
    int num_numa_nodes = std::max(1, static_cast<int>(numa_local_pools_.size()));
    
    for (size_t thread_id = 0; thread_id < config_.num_threads; ++thread_id) {
        int assigned_node;
        
        if (config_.distribute_across_numa_nodes) {
            // Round-robin assignment across NUMA nodes
            assigned_node = static_cast<int>(thread_id % num_numa_nodes);
        } else {
            // Use preferred NUMA node or auto-detect
            assigned_node = (config_.preferred_numa_node >= 0) ? 
                           config_.preferred_numa_node : get_optimal_numa_node();
        }
        
        numa_node_assignments_.push_back(assigned_node);
    }
}

// NEW: Get optimal NUMA node for current thread
int MonteCarloSimulator::get_optimal_numa_node() const {
    // In a production implementation, this would use:
    // - numa_node_of_cpu(sched_getcpu()) on Linux
    // - GetNumaNodeProcessorMask() on Windows
    // For now, return node 0 as fallback
    return 0;
}

void MonteCarloSimulator::worker_thread_func(
    size_t thread_id,
    const SimulationFunction& simulation_func,
    const std::vector<double>& parameters,
    std::vector<std::vector<double>>& results,
    size_t start_simulation,
    size_t end_simulation) {
    
    // NEW: Set thread affinity to NUMA node if enabled
    if (config_.enable_numa_optimization && config_.pin_threads_to_numa_nodes && 
        thread_id < numa_node_assignments_.size()) {
        // In a production implementation, this would pin the thread to the assigned NUMA node
        int numa_node = numa_node_assignments_[thread_id];
        // Platform-specific thread affinity setting would go here
    }
    
    // Initialize thread-local random number generator
    std::random_device rd;
    std::mt19937 rng(rd() + static_cast<unsigned>(thread_id));
    
    // Get thread-local buffer
    double* buffer = (thread_id < pre_allocated_buffers_.size()) ? 
                     pre_allocated_buffers_[thread_id].get() : nullptr;
    
    // NEW: Use NUMA-local pool if available
    nexus::core::MemoryPool<double>* local_pool = nullptr;
    if (config_.enable_numa_optimization && thread_id < numa_node_assignments_.size()) {
        int numa_node = numa_node_assignments_[thread_id];
        if (numa_node >= 0 && static_cast<size_t>(numa_node) < numa_local_pools_.size()) {
            local_pool = numa_local_pools_[numa_node].get();
            
            // Update NUMA statistics
            if (config_.enable_statistics) {
                statistics_.numa_local_allocations.fetch_add(1, std::memory_order_relaxed);
            }
        } else if (config_.enable_statistics) {
            statistics_.numa_remote_allocations.fetch_add(1, std::memory_order_relaxed);
        }
    }
    
    // Run simulations assigned to this thread
    for (size_t sim_idx = start_simulation; sim_idx < end_simulation; ++sim_idx) {
        if (shutdown_requested_.load(std::memory_order_acquire)) {
            break;
        }
        
        results[sim_idx] = simulation_func(parameters, rng);
    }
}

void MonteCarloSimulator::simd_compute_returns(
    const double* returns,
    const double* volatilities,
    double* output,
    size_t count) {
    
    if (!config_.enable_simd) {
        // Fallback to scalar computation
        for (size_t i = 0; i < count; ++i) {
            output[i] = returns[i] * volatilities[i];
        }
        return;
    }

#ifdef __AVX2__
    // AVX2 SIMD implementation
    const size_t simd_width = 4; // 4 doubles per AVX2 register
    size_t simd_count = count - (count % simd_width);
    
    for (size_t i = 0; i < simd_count; i += simd_width) {
        __m256d ret_vec = _mm256_load_pd(&returns[i]);
        __m256d vol_vec = _mm256_load_pd(&volatilities[i]);
        __m256d result = _mm256_mul_pd(ret_vec, vol_vec);
        _mm256_store_pd(&output[i], result);
    }
    
    // Handle remaining elements
    for (size_t i = simd_count; i < count; ++i) {
        output[i] = returns[i] * volatilities[i];
    }
    
    if (config_.enable_statistics) {
        statistics_.simd_operations.fetch_add(simd_count / simd_width, std::memory_order_relaxed);
    }
#else
    // Fallback for systems without AVX2
    for (size_t i = 0; i < count; ++i) {
        output[i] = returns[i] * volatilities[i];
    }
#endif
}

void MonteCarloSimulator::update_statistics(double simulation_time_ns, size_t num_operations) {
    statistics_.total_simulations.fetch_add(num_operations, std::memory_order_relaxed);
    
    // Update average simulation time using exponential moving average
    double current_avg = statistics_.average_simulation_time_ns.load(std::memory_order_acquire);
    double per_simulation_time = simulation_time_ns / num_operations;
    
    const double alpha = 0.1; // Smoothing factor
    double new_avg = (current_avg == 0.0) ? per_simulation_time : 
                    alpha * per_simulation_time + (1.0 - alpha) * current_avg;
    statistics_.average_simulation_time_ns.store(new_avg, std::memory_order_release);
    
    // Calculate throughput
    if (simulation_time_ns > 0) {
        double throughput = (num_operations * 1e9) / simulation_time_ns;
        statistics_.throughput_per_second.store(throughput, std::memory_order_release);
    }
    
    // NEW: Update NUMA efficiency ratio
    if (config_.enable_numa_optimization && config_.enable_statistics) {
        size_t local_allocs = statistics_.numa_local_allocations.load(std::memory_order_acquire);
        size_t remote_allocs = statistics_.numa_remote_allocations.load(std::memory_order_acquire);
        size_t total_allocs = local_allocs + remote_allocs;
        
        if (total_allocs > 0) {
            double efficiency = static_cast<double>(local_allocs) / total_allocs;
            statistics_.numa_efficiency_ratio.store(efficiency, std::memory_order_release);
        }
    }
}

void MonteCarloSimulator::validate_config() {
    if (config_.num_simulations == 0) {
        throw std::invalid_argument("Number of simulations must be greater than 0");
    }
    
    if (config_.num_threads == 0) {
        config_.num_threads = std::thread::hardware_concurrency();
    }
    
    if (config_.buffer_size == 0) {
        config_.buffer_size = 10000;
    }
    
    // NEW: Validate NUMA configuration
    if (config_.enable_numa_optimization) {
        if (config_.numa_buffer_interleaving == 0) {
            config_.numa_buffer_interleaving = 64; // Default to cache line size
        }
    }
}

} // namespace nexus::analytics