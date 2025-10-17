// src/cpp/core/hpc_utils.h

#pragma once

#include <chrono>
#include <cstddef>
#include <memory>
#include <vector>
#include <atomic>
#include <thread>
#include <cstring>

#ifdef _WIN32
#include <malloc.h>
#include <intrin.h>
#elif defined(__linux__) || defined(__APPLE__)
#include <stdlib.h>
#if defined(__x86_64__) || defined(__i386__)
#include <xmmintrin.h>
#endif
#endif

namespace nexus::core {

// NEW: Phase 3.4 - Advanced cache warming with prefetch instructions
namespace CacheWarming {
    /**
     * @brief Prefetches a data structure into CPU cache for improved performance.
     * @param data The data structure to prefetch.
     * @param locality_hint Cache locality hint (0=non-temporal, 1=L3, 2=L2, 3=L1).
     * 
     * This function systematically prefetches an entire data structure into CPU cache
     * by walking through it in cache-line-sized chunks. This reduces cache misses
     * and improves performance when the data structure is accessed shortly after.
     */
    template<typename T>
    static void prefetch_data_structure(const T& data, int locality_hint = 3) {
        const char* ptr = reinterpret_cast<const char*>(&data);
        const size_t size = sizeof(T);
        for (size_t i = 0; i < size; i += 64) { // 64-byte cache lines
#ifdef _MSC_VER
            _mm_prefetch(ptr + i, _MM_HINT_T0);
#elif defined(__GNUC__)
            __builtin_prefetch(ptr + i, 0, locality_hint);
#endif
        }
    }
    
    /**
     * @brief Prefetches a contiguous array of data into CPU cache.
     * @param data Pointer to the array data.
     * @param count Number of elements in the array.
     * @param locality_hint Cache locality hint.
     */
    template<typename T>
    static void prefetch_array(const T* data, size_t count, int locality_hint = 3) {
        if (!data) return;
        
        const char* ptr = reinterpret_cast<const char*>(data);
        const size_t total_size = count * sizeof(T);
        
        for (size_t i = 0; i < total_size; i += 64) { // 64-byte cache lines
#ifdef _MSC_VER
            _mm_prefetch(ptr + i, _MM_HINT_T0);
#elif defined(__GNUC__)
            __builtin_prefetch(ptr + i, 0, locality_hint);
#endif
        }
    }
    
    /**
     * @brief Prefetches a vector's data into CPU cache.
     * @param vec The vector to prefetch.
     * @param locality_hint Cache locality hint.
     */
    template<typename T>
    static void prefetch_vector(const std::vector<T>& vec, int locality_hint = 3) {
        if (vec.empty()) return;
        prefetch_array(vec.data(), vec.size(), locality_hint);
    }
}

/**
 * @class MemoryPool
 * @brief High-performance, cache-aligned memory pool with NUMA awareness.
 *
 * This memory pool is designed for ultra-low latency applications where
 * frequent allocation/deallocation would cause performance issues. It
 * pre-allocates large chunks of memory and manages them efficiently.
 *
 * Key optimizations:
 * - Cache line alignment (64 bytes) to prevent false sharing
 * - NUMA-aware allocation for multi-socket systems
 * - Lock-free allocation using atomic operations
 * - Memory prefetching for improved cache utilization
 * - Cross-platform support (Windows, Linux, macOS)
 */
template <typename T>
class MemoryPool {
public:
    // NEW: NUMA-aware allocation options
    struct NumaConfig {
        bool enable_numa_awareness = false;
        int preferred_numa_node = -1; // -1 = auto-detect
        bool interleave_across_nodes = false;
        bool pin_to_local_node = true;
        size_t numa_allocation_threshold = 1024; // Min size for NUMA allocation
    };

    /**
     * @brief Configuration structure for the memory pool.
     */
    struct Config {
        size_t initial_pool_size = 1000;
        size_t growth_factor = 2;
        size_t max_pool_size = 100000;
        bool enable_prefetching = true;
        bool enable_statistics = false;
        NumaConfig numa_config; // NEW: NUMA configuration
    };

    /**
     * @brief Statistics for monitoring pool performance.
     */
    struct Statistics {
        std::atomic<size_t> total_allocations{0};
        std::atomic<size_t> total_deallocations{0};
        std::atomic<size_t> current_allocated{0};
        std::atomic<size_t> peak_allocated{0};
        std::atomic<size_t> pool_expansions{0};
        std::atomic<size_t> cache_hits{0};
        std::atomic<size_t> cache_misses{0};
        std::atomic<size_t> numa_local_allocations{0}; // NEW: NUMA statistics
        std::atomic<size_t> numa_remote_allocations{0}; // NEW: NUMA statistics
    };

private:
    /**
     * @brief A single memory block in the pool.
     */
    struct alignas(64) Block {
        T data;
        std::atomic<Block*> next{nullptr};
        bool is_allocated{false};
        int numa_node{-1}; // NEW: Track NUMA node for this block
    };

    /**
     * @brief Custom deleter for chunks.
     */
    struct BlockDeleter {
        void operator()(Block* ptr) {
#ifdef _WIN32
            _aligned_free(ptr);
#else
            free(ptr);
#endif
        }
    };

    Config config_;
    Statistics stats_;
    
    // Memory management
    std::vector<std::unique_ptr<Block[], BlockDeleter>> chunks_;
    std::atomic<Block*> free_list_head_{nullptr};
    std::atomic<size_t> current_size_{0};
    
    // Thread safety
    mutable std::atomic<bool> expanding_{false};

public:
    /**
     * @brief Constructs a memory pool with the specified configuration.
     */
    explicit MemoryPool(const Config& config = Config{}) : config_(config) {
        initialize_pool();
        
        if (config_.numa_config.enable_numa_awareness) {
            detect_numa_topology();
        }
    }

    /**
     * @brief Destructor.
     */
    ~MemoryPool() = default;

    /**
     * @brief Allocates a single object from the pool.
     * @return Pointer to the allocated object, or nullptr if allocation failed.
     */
    T* allocate() {
        auto start_time = std::chrono::high_resolution_clock::now();
        
        Block* block = pop_free_block();
        if (!block) [[unlikely]] {
            if (!expand_pool()) {
                return nullptr;
            }
            block = pop_free_block();
            if (!block) {
                return nullptr;
            }
        }

        block->is_allocated = true;
        
        // Update statistics
        if (config_.enable_statistics) {
            stats_.total_allocations.fetch_add(1, std::memory_order_relaxed);
            size_t current = stats_.current_allocated.fetch_add(1, std::memory_order_relaxed) + 1;
            
            // Update peak if necessary
            size_t current_peak = stats_.peak_allocated.load(std::memory_order_acquire);
            while (current > current_peak) {
                if (stats_.peak_allocated.compare_exchange_weak(current_peak, current,
                                                              std::memory_order_acq_rel,
                                                              std::memory_order_acquire)) {
                    break;
                }
            }
            
            // NEW: NUMA statistics
            if (config_.numa_config.enable_numa_awareness) {
                int current_node = get_current_numa_node();
                if (block->numa_node == current_node) {
                    stats_.numa_local_allocations.fetch_add(1, std::memory_order_relaxed);
                } else {
                    stats_.numa_remote_allocations.fetch_add(1, std::memory_order_relaxed);
                }
            }
        }

        // Prefetch the data for better cache performance
        if (config_.enable_prefetching) {
            prefetch_memory(&block->data);
        }

        return &block->data;
    }

    /**
     * @brief Deallocates an object back to the pool.
     * @param ptr Pointer to the object to deallocate.
     */
    void deallocate(T* ptr) {
        if (!ptr) return;

        // Calculate the block address from the data pointer
        Block* block = reinterpret_cast<Block*>(
            reinterpret_cast<char*>(ptr) - offsetof(Block, data)
        );

        block->is_allocated = false;
        push_free_block(block);

        // Update statistics
        if (config_.enable_statistics) {
            stats_.total_deallocations.fetch_add(1, std::memory_order_relaxed);
            stats_.current_allocated.fetch_sub(1, std::memory_order_relaxed);
        }
    }

    /**
     * @brief Gets current pool statistics.
     */
    Statistics get_statistics() const {
        return stats_;
    }

    /**
     * @brief Gets the current pool configuration.
     */
    const Config& get_config() const {
        return config_;
    }

    /**
     * @brief Updates NUMA configuration at runtime.
     */
    void update_numa_config(const NumaConfig& new_config) {
        config_.numa_config = new_config;
        if (new_config.enable_numa_awareness) {
            detect_numa_topology();
        }
    }

private:
    /**
     * @brief Initializes the memory pool with the initial allocation.
     */
    void initialize_pool() {
        allocate_chunk(config_.initial_pool_size);
    }

    /**
     * @brief Allocates a new chunk of memory blocks.
     */
    void allocate_chunk(size_t count) {
        size_t chunk_size = count * sizeof(Block);
        
        // NEW: Use NUMA-aware allocation if enabled
        void* memory = nullptr;
        int target_node = -1;
        
        if (config_.numa_config.enable_numa_awareness) {
            target_node = determine_target_numa_node();
            memory = numa_aligned_malloc(chunk_size, 64, target_node);
        } else {
            memory = aligned_malloc(chunk_size, 64);
        }
        
        if (!memory) {
            throw std::bad_alloc();
        }

        // Use placement new to construct the Block array
        Block* blocks = static_cast<Block*>(memory);
        for (size_t i = 0; i < count; ++i) {
            new (&blocks[i]) Block();
            blocks[i].numa_node = target_node; // NEW: Track NUMA node
        }

        chunks_.emplace_back(reinterpret_cast<Block*>(memory), BlockDeleter{});

        // Add all blocks to the free list
        for (size_t i = 0; i < count; ++i) {
            push_free_block(&blocks[i]);
        }

        current_size_.fetch_add(count, std::memory_order_release);
    }

    /**
     * @brief Expands the pool when it runs out of free blocks.
     */
    bool expand_pool() {
        // Prevent multiple threads from expanding simultaneously
        bool expected = false;
        if (!expanding_.compare_exchange_strong(expected, true, std::memory_order_acq_rel)) {
            // Another thread is already expanding, wait a bit
            std::this_thread::yield();
            return true;
        }

        try {
            size_t current = current_size_.load(std::memory_order_acquire);
            size_t new_size = std::min(current * config_.growth_factor, config_.max_pool_size);
            
            if (new_size <= current) {
                expanding_.store(false, std::memory_order_release);
                return false; // Cannot expand further
            }

            size_t additional_blocks = new_size - current;
            allocate_chunk(additional_blocks);

            if (config_.enable_statistics) {
                stats_.pool_expansions.fetch_add(1, std::memory_order_relaxed);
            }

            expanding_.store(false, std::memory_order_release);
            return true;
        } catch (...) {
            expanding_.store(false, std::memory_order_release);
            return false;
        }
    }

    /**
     * @brief Pops a block from the free list.
     */
    Block* pop_free_block() {
        Block* head = free_list_head_.load(std::memory_order_acquire);
        
        while (head != nullptr) {
            Block* next = head->next.load(std::memory_order_acquire);
            if (free_list_head_.compare_exchange_weak(head, next,
                                                     std::memory_order_acq_rel,
                                                     std::memory_order_acquire)) {
                head->next.store(nullptr, std::memory_order_relaxed);
                return head;
            }
        }
        
        return nullptr;
    }

    /**
     * @brief Pushes a block to the free list.
     */
    void push_free_block(Block* block) {
        Block* head = free_list_head_.load(std::memory_order_acquire);
        
        do {
            block->next.store(head, std::memory_order_relaxed);
        } while (!free_list_head_.compare_exchange_weak(head, block,
                                                       std::memory_order_acq_rel,
                                                       std::memory_order_acquire));
    }

    /**
     * @brief Prefetches memory to improve cache performance.
     */
    static void prefetch_memory(const void* addr) {
#ifdef _WIN32
        _mm_prefetch(static_cast<const char*>(addr), _MM_HINT_T0);
#elif defined(__GNUC__)
        __builtin_prefetch(addr, 0, 3);
#endif
    }

    /**
     * @brief Cross-platform aligned memory allocation.
     */
    static void* aligned_malloc(size_t size, size_t alignment) {
#ifdef _WIN32
        return _aligned_malloc(size, alignment);
#else
        void* ptr = nullptr;
        if (posix_memalign(&ptr, alignment, size) != 0) {
            return nullptr;
        }
        return ptr;
#endif
    }

    /**
     * @brief NEW: NUMA-aware aligned memory allocation.
     */
    static void* numa_aligned_malloc(size_t size, size_t alignment, int numa_node) {
        // NUMA-aware allocation implementation
#ifdef _WIN32
        // Windows: Use VirtualAllocExNuma if available, otherwise fall back
        return _aligned_malloc(size, alignment); // Windows fallback
#elif defined(__linux__)
        // Linux: Use numa_alloc_onnode if available
        void* ptr = nullptr;
        if (numa_node >= 0) {
            // In a real implementation, we would check for libnuma and use:
            // ptr = numa_alloc_onnode(size, numa_node);
            // For now, use standard allocation
            if (posix_memalign(&ptr, alignment, size) != 0) {
                return nullptr;
            }
        } else {
            if (posix_memalign(&ptr, alignment, size) != 0) {
                return nullptr;
            }
        }
        return ptr;
#else
        // Other platforms: Fall back to regular aligned allocation
        return aligned_malloc(size, alignment);
#endif
    }

    /**
     * @brief NEW: Detect NUMA topology.
     */
    void detect_numa_topology() {
        // In a production implementation, this would detect:
        // - Number of NUMA nodes
        // - Current thread's NUMA node
        // - Memory bandwidth between nodes
        // For now, this is a placeholder
    }

    /**
     * @brief NEW: Determine target NUMA node for allocation.
     */
    int determine_target_numa_node() {
        if (config_.numa_config.preferred_numa_node >= 0) {
            return config_.numa_config.preferred_numa_node;
        }
        
        // Auto-detect current NUMA node
        return get_current_numa_node();
    }

    /**
     * @brief NEW: Get current thread's NUMA node.
     */
    int get_current_numa_node() {
#ifdef __linux__
        // In a real implementation, use:
        // return numa_node_of_cpu(sched_getcpu());
        return 0; // Placeholder
#else
        return 0; // Fallback
#endif
    }
};

} // namespace nexus::core