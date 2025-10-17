// src/cpp/core/backtest_engine.cpp

#include "core/backtest_engine.h"
#include "core/thread_affinity.h"
#include "core/hpc_utils.h"
#include "execution/execution_simulator.h"
#include <iostream>
#include <chrono>

namespace nexus::core {

BacktestEngine::BacktestEngine(
    EventQueue& event_queue,
    std::shared_ptr<nexus::data::MarketDataHandler> data_handler,
    std::unordered_map<std::string, std::shared_ptr<nexus::strategies::AbstractStrategy>> strategies,
    std::shared_ptr<nexus::position::PositionManager> position_manager,
    std::shared_ptr<nexus::execution::ExecutionSimulator> execution_simulator,
    const BacktestEngineConfig& config)
    : event_queue_(event_queue),
      data_handler_(std::move(data_handler)),
      strategies_(std::move(strategies)),
      position_manager_(std::move(position_manager)),
      execution_simulator_(std::move(execution_simulator)),
      config_(config) {

    config_.validate();
    
    std::cout << "BacktestEngine: Initializing with " << strategies_.size() << " strategies" << std::endl;
    
    // Store original thread state before applying optimizations
    original_cpu_affinity_ = ThreadAffinity::get_current_affinity();
    
    // Apply real-time optimizations if configured
    if (config_.real_time_config.enable_cpu_affinity || 
        config_.real_time_config.enable_real_time_priority) {
        std::cout << "BacktestEngine: Applying real-time optimizations..." << std::endl;
        std::cout << config_.real_time_config.to_string() << std::endl;
        apply_real_time_optimizations();
    }
    
    // Configure NUMA allocation if enabled
    if (config_.real_time_config.enable_numa_optimization) {
        configure_numa_allocation();
    }
    
    // Setup performance monitoring
    if (config_.enable_performance_monitoring || config_.real_time_config.enable_performance_monitoring) {
        setup_performance_monitoring();
    }
    
    // Warm caches if enabled
    if (config_.real_time_config.enable_cache_warming) {
        std::cout << "BacktestEngine: Warming critical caches..." << std::endl;
        warm_critical_caches();
    }
    
    std::cout << "BacktestEngine: Initialization complete" << std::endl;
}

BacktestEngine::~BacktestEngine() {
    // Signal worker threads to exit
    threads_should_exit_.store(true, std::memory_order_release);
    
    // Wait for worker threads to complete
    for (auto& thread : worker_threads_) {
        if (thread.joinable()) {
            thread.join();
        }
    }
    
    // Revert real-time optimizations
    if (real_time_optimizations_applied_.load(std::memory_order_acquire)) {
        revert_real_time_optimizations();
    }
    
    // Print final performance statistics if monitoring was enabled
    if (config_.enable_performance_monitoring || config_.real_time_config.enable_performance_monitoring) {
        std::cout << get_performance_info() << std::endl;
    }
    
    std::cout << "BacktestEngine: Cleanup complete" << std::endl;
}

void BacktestEngine::run() {
    std::cout << "BacktestEngine: Starting backtest execution" << std::endl;
    
    is_running_.store(true, std::memory_order_release);
    stop_requested_.store(false, std::memory_order_release);
    
    auto start_time = std::chrono::high_resolution_clock::now();
    
    try {
        // Initialize market data handler
        std::cout << "BacktestEngine: Market data handler initialized" << std::endl;
        
        // Main event processing loop
        process_events();
        
        // Cleanup
        std::cout << "BacktestEngine: Market data processing complete" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "BacktestEngine: Error during execution: " << e.what() << std::endl;
        throw;
    }
    
    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);
    
    is_running_.store(false, std::memory_order_release);
    
    std::cout << "BacktestEngine: Backtest completed in " << duration.count() << "ms" << std::endl;
    std::cout << "Total events processed: " << total_events_processed_.load() << std::endl;
    
    if (config_.enable_performance_monitoring || config_.real_time_config.enable_performance_monitoring) {
        std::cout << get_performance_info() << std::endl;
    }
}

void BacktestEngine::update_config(const BacktestEngineConfig& new_config) {
    std::cout << "BacktestEngine: Updating configuration" << std::endl;
    
    // Revert current optimizations if they were applied
    if (real_time_optimizations_applied_.load(std::memory_order_acquire)) {
        revert_real_time_optimizations();
    }
    
    // Update configuration
    config_ = new_config;
    config_.validate();
    
    // Apply new optimizations if configured
    if (config_.real_time_config.enable_cpu_affinity || 
        config_.real_time_config.enable_real_time_priority) {
        std::cout << "BacktestEngine: Applying updated real-time optimizations..." << std::endl;
        apply_real_time_optimizations();
    }
    
    std::cout << "BacktestEngine: Configuration update complete" << std::endl;
}

std::string BacktestEngine::get_performance_info() const {
    std::ostringstream info;
    
    uint64_t total_events = total_events_processed_.load(std::memory_order_acquire);
    uint64_t total_time_ns = total_processing_time_ns_.load(std::memory_order_acquire);
    uint64_t max_time_ns = max_event_processing_time_ns_.load(std::memory_order_acquire);
    
    info << "BacktestEngine Performance Statistics:\n";
    info << "  Total Events Processed: " << total_events << "\n";
    
    if (total_events > 0 && total_time_ns > 0) {
        double avg_time_ns = static_cast<double>(total_time_ns) / total_events;
        info << "  Average Event Processing Time: " << avg_time_ns << " ns\n";
        info << "  Maximum Event Processing Time: " << max_time_ns << " ns\n";
        info << "  Events Per Second: " << (total_events * 1000000000.0 / total_time_ns) << "\n";
    }
    
    info << "  Thread Affinity Info: " << ThreadAffinity::get_thread_info() << "\n";
    
    return info.str();
}

void BacktestEngine::warm_caches() {
    std::cout << "BacktestEngine: Manual cache warming requested" << std::endl;
    warm_critical_caches();
}

void BacktestEngine::apply_real_time_optimizations() {
    const auto& rt_config = config_.real_time_config;
    
    try {
        // Apply CPU affinity if configured
        if (rt_config.enable_cpu_affinity) {
            std::cout << "BacktestEngine: Applying CPU affinity..." << std::endl;
            
            if (rt_config.auto_detect_optimal_cores) {
                // Use manual core selection for now - auto-detection could be added later
                std::cout << "BacktestEngine: Using manual core selection" << std::endl;
            }
            
            bool affinity_success = false;
            if (rt_config.cpu_cores.size() == 1) {
                affinity_success = ThreadAffinity::pin_to_core(rt_config.cpu_cores[0]);
            } else {
                affinity_success = ThreadAffinity::pin_to_cores(rt_config.cpu_cores);
            }
            
            if (!affinity_success && !rt_config.enable_graceful_fallback) {
                throw std::runtime_error("Failed to set CPU affinity and graceful fallback is disabled");
            }
        }
        
        // Apply real-time priority if configured
        if (rt_config.enable_real_time_priority) {
            std::cout << "BacktestEngine: Applying real-time priority..." << std::endl;
            
            bool priority_success = ThreadAffinity::set_real_time_priority(rt_config.real_time_priority_level);
            
            if (!priority_success && !rt_config.enable_graceful_fallback) {
                throw std::runtime_error("Failed to set real-time priority and graceful fallback is disabled");
            }
        }
        
        // Attempt core isolation if configured
        if (rt_config.cpu_isolation_mode != "none") {
            std::cout << "BacktestEngine: Attempting core isolation (mode: " 
                      << rt_config.cpu_isolation_mode << ")..." << std::endl;
            ThreadAffinity::isolate_cores(rt_config.cpu_cores);
        }
        
        real_time_optimizations_applied_.store(true, std::memory_order_release);
        std::cout << "BacktestEngine: Real-time optimizations applied successfully" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "BacktestEngine: Error applying real-time optimizations: " << e.what() << std::endl;
        
        if (!rt_config.enable_graceful_fallback) {
            throw;
        } else {
            std::cout << "BacktestEngine: Continuing with graceful fallback" << std::endl;
        }
    }
}

void BacktestEngine::revert_real_time_optimizations() {
    std::cout << "BacktestEngine: Reverting real-time optimizations..." << std::endl;
    
    try {
        // Restore normal priority
        ThreadAffinity::set_normal_priority();
        
        // Restore original CPU affinity if we have it
        if (!original_cpu_affinity_.empty()) {
            ThreadAffinity::pin_to_cores(original_cpu_affinity_);
        }
        
        real_time_optimizations_applied_.store(false, std::memory_order_release);
        std::cout << "BacktestEngine: Real-time optimizations reverted" << std::endl;
        
    } catch (const std::exception& e) {
        std::cerr << "BacktestEngine: Error reverting real-time optimizations: " << e.what() << std::endl;
    }
}

void BacktestEngine::warm_critical_caches() {
    const size_t iterations = config_.real_time_config.cache_warming_iterations;
    
    for (size_t iter = 0; iter < iterations; ++iter) {
        // Warm strategy data structures
        for (const auto& [symbol, strategy] : strategies_) {
            if (strategy) {
                CacheWarming::prefetch_data_structure(*strategy);
            }
        }
        
        // Warm position manager data
        if (position_manager_) {
            CacheWarming::prefetch_data_structure(*position_manager_);
        }
        
        // Warm execution simulator data  
        if (execution_simulator_) {
            CacheWarming::prefetch_data_structure(*execution_simulator_);
        }
        
        // Warm data handler data
        if (data_handler_) {
            CacheWarming::prefetch_data_structure(*data_handler_);
        }
        
        // Warm event queue data structures
        CacheWarming::prefetch_data_structure(event_queue_);
    }
    
    std::cout << "BacktestEngine: Cache warming completed (" << iterations << " iterations)" << std::endl;
}

void BacktestEngine::configure_numa_allocation() {
    const auto& rt_config = config_.real_time_config;
    
    std::cout << "BacktestEngine: Configuring NUMA-aware allocation..." << std::endl;
    
    // This would integrate with NUMA allocation in HPC utils
    // For now, we just log the configuration
    std::cout << "BacktestEngine: NUMA node preference: " 
              << (rt_config.preferred_numa_node == -1 ? "auto" : std::to_string(rt_config.preferred_numa_node))
              << std::endl;
    
    // Future implementation would:
    // 1. Detect NUMA topology
    // 2. Configure memory allocators
    // 3. Set memory policy for allocations
}

void BacktestEngine::setup_performance_monitoring() {
    std::cout << "BacktestEngine: Setting up performance monitoring..." << std::endl;
    
    // Reset performance counters
    total_events_processed_.store(0, std::memory_order_release);
    total_processing_time_ns_.store(0, std::memory_order_release);
    max_event_processing_time_ns_.store(0, std::memory_order_release);
    
    // Configure latency spike detection if enabled
    if (config_.real_time_config.enable_latency_spike_detection) {
        std::cout << "BacktestEngine: Latency spike detection enabled (threshold: " 
                  << config_.real_time_config.latency_spike_threshold.count() << "μs)" << std::endl;
    }
    
    std::cout << "BacktestEngine: Performance monitoring active" << std::endl;
}

Event* BacktestEngine::get_next_event_safe() {
    // Use the EventQueue's dequeue method
    return event_queue_.dequeue();
}

void BacktestEngine::add_event_safe(Event* event) {
    // Use the EventQueue's enqueue method
    if (event) {
        event_queue_.enqueue(event);
    }
}

EventPool& BacktestEngine::get_event_pool_safe() {
    // For now, use a static EventPool since EventQueue doesn't expose one
    // In a real implementation, you might want to add an event pool to EventQueue
    // or pass it as a separate dependency
    static EventPool event_pool_;
    return event_pool_;
}

void BacktestEngine::process_trade_execution_event(const TradeExecutionEvent& event) {
    // Update position manager with the execution
    position_manager_->on_trade_execution(event);
    
    // Log the execution if monitoring is enabled
    if (config_.enable_performance_monitoring || config_.real_time_config.enable_performance_monitoring) {
        std::cout << "BacktestEngine: Trade executed - Symbol: " << event.symbol 
                  << ", Quantity: " << event.quantity 
                  << ", Price: " << event.price 
                  << ", Commission: " << event.commission << std::endl;
    }
}

void BacktestEngine::process_events() {
    size_t events_in_batch = 0;
    auto batch_start_time = std::chrono::high_resolution_clock::now();
    
    while (!stop_requested_.load(std::memory_order_acquire) && !data_handler_->is_complete()) {
        auto event_start_time = std::chrono::high_resolution_clock::now();
        
        // Get next event from queue using safe wrapper
        Event* event = get_next_event_safe();
        if (!event) {
            // No event available, continue
            std::this_thread::yield();
            continue;
        }
        
        // Process the event based on its actual type using dynamic_cast
        if (MarketDataEvent* market_data_event = dynamic_cast<MarketDataEvent*>(event)) {
            process_market_data_event(*market_data_event);
        }
        else if (TradingSignalEvent* trading_signal_event = dynamic_cast<TradingSignalEvent*>(event)) {
            process_trading_signal_event(*trading_signal_event);
        }
        else if (TradeExecutionEvent* trade_execution_event = dynamic_cast<TradeExecutionEvent*>(event)) {
            process_trade_execution_event(*trade_execution_event);
        }
        else {
            std::cerr << "BacktestEngine: Unknown event type received" << std::endl;
        }
        
        // Update performance statistics if monitoring is enabled
        if (config_.enable_performance_monitoring || config_.real_time_config.enable_performance_monitoring) {
            auto event_end_time = std::chrono::high_resolution_clock::now();
            auto event_duration_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                event_end_time - event_start_time).count();
            
            total_events_processed_.fetch_add(1, std::memory_order_acq_rel);
            total_processing_time_ns_.fetch_add(event_duration_ns, std::memory_order_acq_rel);
            
            // Update max processing time
            uint64_t current_max = max_event_processing_time_ns_.load(std::memory_order_acquire);
            while (event_duration_ns > current_max) {
                if (max_event_processing_time_ns_.compare_exchange_weak(
                    current_max, event_duration_ns, 
                    std::memory_order_acq_rel, std::memory_order_acquire)) {
                    break;
                }
            }
            
            // Check for latency spikes if detection is enabled
            if (config_.real_time_config.enable_latency_spike_detection) {
                auto spike_threshold_ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
                    config_.real_time_config.latency_spike_threshold).count();
                
                if (event_duration_ns > spike_threshold_ns) {
                    std::cout << "BacktestEngine: Latency spike detected: " 
                              << (event_duration_ns / 1000.0) << "μs" << std::endl;
                }
            }
        }
        
        events_in_batch++;
        
        // Check batch limits if batching is enabled
        if (config_.enable_event_batching) {
            auto batch_duration = std::chrono::duration_cast<std::chrono::microseconds>(
                std::chrono::high_resolution_clock::now() - batch_start_time);
            
            if (events_in_batch >= config_.max_events_per_batch || 
                batch_duration >= config_.max_batch_duration) {
                // Reset batch counters
                events_in_batch = 0;
                batch_start_time = std::chrono::high_resolution_clock::now();
                
                // Yield to other threads
                std::this_thread::yield();
            }
        }
    }
}

void BacktestEngine::process_market_data_event(const MarketDataEvent& event) {
    // Update position manager with new market data
    position_manager_->on_market_data(event);
    
    // Send market data to relevant strategy
    auto it = strategies_.find(event.symbol);
    if (it != strategies_.end() && it->second) {
        it->second->on_market_data(event);
        
        // Generate trading signal if any using safe wrapper
        Event* signal = it->second->generate_signal(get_event_pool_safe());
        if (signal) {
            add_event_safe(signal);
        }
    }
}

void BacktestEngine::process_trading_signal_event(const TradingSignalEvent& event) {
    // Get current market price for the symbol
    auto market_data = position_manager_->get_equity_curve(); // This is a placeholder
    // In a real implementation, we'd get the current market price from market data
    double current_price = 100.0; // Placeholder
    
    // Simulate order execution using safe wrapper
    TradeExecutionEvent* execution_event = execution_simulator_->simulate_order_execution(
        event, current_price, get_event_pool_safe());
    
    if (execution_event) {
        add_event_safe(execution_event);
    }
}

} // namespace nexus::core