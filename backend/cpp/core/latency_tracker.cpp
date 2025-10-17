// src/cpp/core/latency_tracker.cpp

#include "core/latency_tracker.h"
#include <algorithm>
#include <numeric>
#include <cmath>
#include <iostream>

namespace nexus::core {

LatencyTracker::LatencyTracker(const Config& config) : config_(config) {
    last_global_update_.store(std::chrono::system_clock::now(), std::memory_order_release);
    std::cout << "LatencyTracker: Initialized with configuration:" << std::endl;
    std::cout << "  - Max measurements per operation: " << config_.max_measurements_per_operation << std::endl;
    std::cout << "  - Statistics update interval: " << config_.statistics_update_interval.count() << "s" << std::endl;
    std::cout << "  - Percentile calculation: " << (config_.enable_percentile_calculation ? "enabled" : "disabled") << std::endl;
}

LatencyTracker::~LatencyTracker() {
    if (enabled_.load()) {
        std::cout << "LatencyTracker: Final statistics summary:" << std::endl;
        auto all_stats = get_all_statistics();
        for (const auto& [operation, stats] : all_stats) {
            std::cout << "  - " << operation << ": " << stats.sample_count 
                      << " samples, p99: " << stats.p99_us() << "µs" << std::endl;
        }
    }
}

uint64_t LatencyTracker::start_measurement(const std::string& operation_name) {
    if (!enabled_.load(std::memory_order_acquire)) [[unlikely]] {
        return 0; // Return invalid ID when disabled
    }

    uint64_t measurement_id = next_measurement_id_.fetch_add(1, std::memory_order_acq_rel);
    uint64_t start_tsc = HighResolutionClock::get_tsc();
    auto start_time = std::chrono::system_clock::now();

    ActiveMeasurement measurement{
        operation_name,
        start_tsc,
        start_time
    };

    {
        std::unique_lock<std::shared_mutex> lock(active_measurements_mutex_);
        active_measurements_[measurement_id] = std::move(measurement);
    }

    return measurement_id;
}

LatencyMeasurement LatencyTracker::end_measurement(uint64_t measurement_id) {
    LatencyMeasurement result;
    
    if (!enabled_.load(std::memory_order_acquire) || measurement_id == 0) [[unlikely]] {
        return result; // Return empty measurement when disabled or invalid ID
    }

    uint64_t end_tsc = HighResolutionClock::get_tsc();
    auto end_time = std::chrono::system_clock::now();

    // Find and remove the active measurement
    ActiveMeasurement active_measurement;
    bool found = false;
    
    {
        std::unique_lock<std::shared_mutex> lock(active_measurements_mutex_);
        auto it = active_measurements_.find(measurement_id);
        if (it != active_measurements_.end()) [[likely]] {
            active_measurement = std::move(it->second);
            active_measurements_.erase(it);
            found = true;
        }
    }

    if (!found) [[unlikely]] {
        std::cerr << "LatencyTracker: Warning - measurement ID " << measurement_id 
                  << " not found in active measurements" << std::endl;
        return result;
    }

    // Create the completed measurement
    result.operation_name = std::move(active_measurement.operation_name);
    result.start_tsc = active_measurement.start_tsc;
    result.end_tsc = end_tsc;
    result.timestamp = active_measurement.start_time;
    result.calculate_latency();

    // Add to the tracker
    add_measurement(result);

    return result;
}

void LatencyTracker::add_measurement(const LatencyMeasurement& measurement) {
    if (!enabled_.load(std::memory_order_acquire)) [[unlikely]] {
        return;
    }

    // Get or create operation data
    OperationData& data = get_or_create_operation_data(measurement.operation_name);

    {
        std::unique_lock<std::shared_mutex> lock(data.mutex);
        
        // Add the measurement
        data.measurements.push_back(measurement);
        
        // Check if we need to cleanup old measurements
        if (config_.auto_cleanup_old_measurements && 
            data.measurements.size() > config_.max_measurements_per_operation) {
            // Remove oldest measurements, keeping the most recent ones
            size_t to_remove = data.measurements.size() - config_.max_measurements_per_operation;
            data.measurements.erase(data.measurements.begin(), 
                                   data.measurements.begin() + to_remove);
        }
        
        // Mark statistics as dirty for lazy update
        data.statistics_dirty = true;
    }

    // Update statistics if real-time updates are enabled
    if (config_.enable_real_time_stats) {
        auto now = std::chrono::system_clock::now();
        auto last_update = last_global_update_.load(std::memory_order_acquire);
        
        if (now - last_update >= config_.statistics_update_interval) {
            if (last_global_update_.compare_exchange_weak(last_update, now, 
                                                         std::memory_order_acq_rel,
                                                         std::memory_order_acquire)) {
                // We won the race to update statistics
                calculate_statistics(data);
            }
        }
    }
}

LatencyStatistics LatencyTracker::get_statistics(const std::string& operation_name) const {
    std::shared_lock<std::shared_mutex> operations_lock(operations_mutex_);
    auto it = operations_.find(operation_name);
    
    if (it == operations_.end()) [[unlikely]] {
        return LatencyStatistics{}; // Return empty statistics
    }

    OperationData& data = *it->second;
    std::shared_lock<std::shared_mutex> data_lock(data.mutex);
    
    // Update statistics if needed
    if (data.statistics_dirty) {
        data_lock.unlock();
        std::unique_lock<std::shared_mutex> data_write_lock(data.mutex);
        if (data.statistics_dirty) { // Double-check under write lock
            calculate_statistics(data);
        }
        data_write_lock.unlock();
        data_lock.lock();
    }
    
    return data.statistics;
}

std::unordered_map<std::string, LatencyStatistics> LatencyTracker::get_all_statistics() const {
    std::unordered_map<std::string, LatencyStatistics> result;
    
    std::shared_lock<std::shared_mutex> operations_lock(operations_mutex_);
    
    for (const auto& [operation_name, data_ptr] : operations_) {
        result[operation_name] = get_statistics(operation_name);
    }
    
    return result;
}

void LatencyTracker::update_statistics() {
    std::shared_lock<std::shared_mutex> operations_lock(operations_mutex_);
    
    for (const auto& [operation_name, data_ptr] : operations_) {
        calculate_statistics(*data_ptr);
    }
    
    last_global_update_.store(std::chrono::system_clock::now(), std::memory_order_release);
}

void LatencyTracker::clear() {
    std::unique_lock<std::shared_mutex> operations_lock(operations_mutex_);
    operations_.clear();
    
    std::unique_lock<std::shared_mutex> active_lock(active_measurements_mutex_);
    active_measurements_.clear();
}

void LatencyTracker::clear_operation(const std::string& operation_name) {
    std::unique_lock<std::shared_mutex> operations_lock(operations_mutex_);
    operations_.erase(operation_name);
}

size_t LatencyTracker::get_total_measurement_count() const noexcept {
    size_t total = 0;
    std::shared_lock<std::shared_mutex> operations_lock(operations_mutex_);
    
    for (const auto& [operation_name, data_ptr] : operations_) {
        std::shared_lock<std::shared_mutex> data_lock(data_ptr->mutex);
        total += data_ptr->measurements.size();
    }
    
    return total;
}

size_t LatencyTracker::get_measurement_count(const std::string& operation_name) const {
    std::shared_lock<std::shared_mutex> operations_lock(operations_mutex_);
    auto it = operations_.find(operation_name);
    
    if (it == operations_.end()) [[unlikely]] {
        return 0;
    }
    
    std::shared_lock<std::shared_mutex> data_lock(it->second->mutex);
    return it->second->measurements.size();
}

std::vector<LatencyMeasurement> LatencyTracker::get_recent_measurements(
    const std::string& operation_name, size_t max_count) const {
    
    std::shared_lock<std::shared_mutex> operations_lock(operations_mutex_);
    auto it = operations_.find(operation_name);
    
    if (it == operations_.end()) [[unlikely]] {
        return {};
    }
    
    std::shared_lock<std::shared_mutex> data_lock(it->second->mutex);
    const auto& measurements = it->second->measurements;
    
    if (measurements.size() <= max_count) {
        return measurements;
    }
    
    // Return the most recent measurements
    return std::vector<LatencyMeasurement>(
        measurements.end() - max_count, measurements.end());
}

void LatencyTracker::set_enabled(bool enabled) noexcept {
    enabled_.store(enabled, std::memory_order_release);
}

bool LatencyTracker::is_enabled() const noexcept {
    return enabled_.load(std::memory_order_acquire);
}

const LatencyTracker::Config& LatencyTracker::get_config() const noexcept {
    return config_;
}

void LatencyTracker::update_config(const Config& new_config) {
    config_ = new_config;
    
    // Apply cleanup to existing measurements if max count changed
    std::shared_lock<std::shared_mutex> operations_lock(operations_mutex_);
    for (const auto& [operation_name, data_ptr] : operations_) {
        std::unique_lock<std::shared_mutex> data_lock(data_ptr->mutex);
        if (data_ptr->measurements.size() > config_.max_measurements_per_operation) {
            size_t to_remove = data_ptr->measurements.size() - config_.max_measurements_per_operation;
            data_ptr->measurements.erase(data_ptr->measurements.begin(),
                                        data_ptr->measurements.begin() + to_remove);
            data_ptr->statistics_dirty = true;
        }
    }
}

void LatencyTracker::calculate_statistics(OperationData& data) const {
    std::unique_lock<std::shared_mutex> lock(data.mutex);
    
    if (data.measurements.empty()) {
        data.statistics = LatencyStatistics{};
        data.statistics.operation_name = ""; // Will be set by caller
        data.statistics_dirty = false;
        return;
    }

    // Clean up old measurements if needed
    if (config_.auto_cleanup_old_measurements) {
        cleanup_old_measurements(data);
    }

    // Extract latency values
    std::vector<double> latencies;
    latencies.reserve(data.measurements.size());
    
    for (const auto& measurement : data.measurements) {
        // Filter out obvious outliers
        if (measurement.latency_ns > 0.0 && 
            measurement.latency_ns < 1000000000.0) { // Less than 1 second
            latencies.push_back(measurement.latency_ns);
        }
    }

    if (latencies.empty()) {
        data.statistics_dirty = false;
        return;
    }

    // Calculate basic statistics
    data.statistics.sample_count = latencies.size();
    data.statistics.min_ns = *std::min_element(latencies.begin(), latencies.end());
    data.statistics.max_ns = *std::max_element(latencies.begin(), latencies.end());
    
    double sum = std::accumulate(latencies.begin(), latencies.end(), 0.0);
    data.statistics.mean_ns = sum / latencies.size();
    
    // Calculate standard deviation
    double variance = 0.0;
    for (double latency : latencies) {
        variance += std::pow(latency - data.statistics.mean_ns, 2);
    }
    variance /= latencies.size();
    data.statistics.std_dev_ns = std::sqrt(variance);
    
    // Calculate percentiles if enabled
    if (config_.enable_percentile_calculation) {
        std::vector<double> sorted_latencies = latencies;
        std::sort(sorted_latencies.begin(), sorted_latencies.end());
        calculate_percentiles(sorted_latencies, data.statistics);
    }
    
    data.statistics.last_updated = std::chrono::system_clock::now();
    data.last_statistics_update = data.statistics.last_updated;
    data.statistics_dirty = false;
}

void LatencyTracker::calculate_percentiles(const std::vector<double>& sorted_latencies,
                                          LatencyStatistics& stats) const {
    if (sorted_latencies.empty()) {
        return;
    }

    auto percentile = [&](double p) -> double {
        if (p <= 0.0) return sorted_latencies.front();
        if (p >= 1.0) return sorted_latencies.back();
        
        double index = p * (sorted_latencies.size() - 1);
        size_t lower = static_cast<size_t>(index);
        size_t upper = lower + 1;
        
        if (upper >= sorted_latencies.size()) {
            return sorted_latencies.back();
        }
        
        double weight = index - lower;
        return sorted_latencies[lower] * (1.0 - weight) + sorted_latencies[upper] * weight;
    };

    stats.p50_ns = percentile(0.50);
    stats.p95_ns = percentile(0.95);
    stats.p99_ns = percentile(0.99);
    stats.p999_ns = percentile(0.999);
}

void LatencyTracker::cleanup_old_measurements(OperationData& data) const {
    if (!config_.auto_cleanup_old_measurements) {
        return;
    }

    auto cutoff_time = std::chrono::system_clock::now() - config_.measurement_retention_time;
    
    // Remove measurements older than the retention time
    auto new_end = std::remove_if(data.measurements.begin(), data.measurements.end(),
        [cutoff_time](const LatencyMeasurement& measurement) {
            return measurement.timestamp < cutoff_time;
        });
    
    if (new_end != data.measurements.end()) {
        data.measurements.erase(new_end, data.measurements.end());
    }
}

LatencyTracker::OperationData& LatencyTracker::get_or_create_operation_data(
    const std::string& operation_name) {
    
    // Try to find existing operation data with shared lock first
    {
        std::shared_lock<std::shared_mutex> lock(operations_mutex_);
        auto it = operations_.find(operation_name);
        if (it != operations_.end()) [[likely]] {
            return *it->second;
        }
    }
    
    // Need to create new operation data with unique lock
    std::unique_lock<std::shared_mutex> lock(operations_mutex_);
    
    // Double-check after acquiring unique lock
    auto it = operations_.find(operation_name);
    if (it != operations_.end()) [[unlikely]] {
        return *it->second;
    }
    
    // Create new operation data
    auto data = std::make_unique<OperationData>();
    data->statistics.operation_name = operation_name;
    data->measurements.reserve(config_.max_measurements_per_operation);
    
    OperationData& result = *data;
    operations_[operation_name] = std::move(data);
    
    return result;
}

} // namespace nexus::core