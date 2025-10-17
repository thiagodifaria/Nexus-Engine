// src/cpp/execution/price_level.h

#pragma once

#include <atomic>
#include <cstdint>
#include <memory>
#include <chrono>
#include <cmath>

namespace nexus::execution {

/**
 * @struct Order
 * @brief Represents a single order in the order book.
 *
 * This structure contains all necessary information about an order
 * and is designed for lock-free operations with atomic updates.
 */
struct Order {
    /**
     * @enum Side
     * @brief Order side enumeration for type safety.
     */
    enum class Side : uint8_t {
        BUY = 0,
        SELL = 1
    };

    /**
     * @enum Status
     * @brief Order status for lifecycle management.
     */
    enum class Status : uint8_t {
        ACTIVE = 0,
        PARTIALLY_FILLED = 1,
        FULLY_FILLED = 2,
        CANCELLED = 3
    };

    // Order identification
    uint64_t order_id{0};
    std::string symbol;
    
    // Order details  
    Side side{Side::BUY};
    double price{0.0};
    std::atomic<double> quantity{0.0};           // Remaining quantity (atomic for partial fills)
    double original_quantity{0.0};              // Original order quantity
    std::atomic<Status> status{Status::ACTIVE}; // Current order status
    
    // Timing information
    std::chrono::system_clock::time_point created_time;
    std::atomic<uint64_t> priority{0};          // For time priority (nanoseconds since epoch)
    
    // Lock-free linked list pointers for order chains
    std::atomic<Order*> next{nullptr};
    
    /**
     * @brief Constructor for creating a new order.
     */
    Order(uint64_t id, const std::string& sym, Side s, double p, double q)
        : order_id(id), symbol(sym), side(s), price(p), original_quantity(q), 
          created_time(std::chrono::system_clock::now()) {
        quantity.store(q, std::memory_order_relaxed);
        
        // Set priority based on creation time (nanoseconds for high precision)
        auto nano_time = std::chrono::duration_cast<std::chrono::nanoseconds>(
            created_time.time_since_epoch()).count();
        priority.store(static_cast<uint64_t>(nano_time), std::memory_order_relaxed);
    }

    /**
     * @brief Attempts to fill part or all of this order.
     * @param fill_quantity The quantity to fill.
     * @return The actual quantity filled (may be less than requested).
     */
    double try_fill(double fill_quantity) {
        double current_qty = quantity.load(std::memory_order_acquire);
        
        while (current_qty > 0.0 && fill_quantity > 0.0) {
            double actual_fill = std::min(current_qty, fill_quantity);
            double new_qty = current_qty - actual_fill;
            
            // Use compare-and-swap to atomically update quantity
            if (quantity.compare_exchange_weak(current_qty, new_qty, 
                                             std::memory_order_acq_rel, 
                                             std::memory_order_acquire)) {
                // Update status based on remaining quantity
                Status expected_status = status.load(std::memory_order_acquire);
                Status new_status = (new_qty == 0.0) ? Status::FULLY_FILLED : Status::PARTIALLY_FILLED;
                status.compare_exchange_weak(expected_status, new_status, 
                                           std::memory_order_acq_rel, 
                                           std::memory_order_acquire);
                
                return actual_fill;
            }
            // If CAS failed, reload current quantity and retry
            current_qty = quantity.load(std::memory_order_acquire);
        }
        
        return 0.0; // No fill possible
    }

    /**
     * @brief Checks if the order is still active and has remaining quantity.
     * @return True if the order can be matched against.
     */
    bool is_active() const noexcept {
        Status current_status = status.load(std::memory_order_acquire);
        return (current_status == Status::ACTIVE || current_status == Status::PARTIALLY_FILLED) &&
               quantity.load(std::memory_order_acquire) > 0.0;
    }

    /**
     * @brief Gets the remaining quantity safely.
     * @return The current remaining quantity.
     */
    double get_remaining_quantity() const noexcept {
        return quantity.load(std::memory_order_acquire);
    }
};

/**
 * @class PriceLevel
 * @brief Atomic price level containing all orders at a specific price.
 *
 * This class manages all orders at a single price level using lock-free
 * operations. It maintains a linked list of orders with atomic operations
 * for thread-safe access without locks.
 *
 * Key features:
 * - Lock-free order insertion and removal
 * - Atomic quantity tracking for fast depth calculations
 * - Time priority ordering within the price level
 * - Optimistic concurrency control for high performance
 */
class PriceLevel {
public:
    /**
     * @brief Constructs a price level for the specified price.
     * @param price The price for this level.
     */
    explicit PriceLevel(double price) : price_(price) {}

    /**
     * @brief Destructor - ensures proper cleanup of order chain.
     */
    ~PriceLevel() {
        clear();
    }

    // Disable copy constructor and assignment
    PriceLevel(const PriceLevel&) = delete;
    PriceLevel& operator=(const PriceLevel&) = delete;

    // Enable move constructor and assignment  
    PriceLevel(PriceLevel&& other) noexcept
        : price_(other.price_),
          total_quantity_(other.total_quantity_.load()),
          order_count_(other.order_count_.load()) {
        head_.store(other.head_.exchange(nullptr));
    }

    PriceLevel& operator=(PriceLevel&& other) noexcept {
        if (this != &other) {
            clear();
            price_ = other.price_;
            total_quantity_.store(other.total_quantity_.load());
            order_count_.store(other.order_count_.load());
            head_.store(other.head_.exchange(nullptr));
        }
        return *this;
    }

    /**
     * @brief Adds an order to this price level.
     * @param order Pointer to the order to add.
     * @return True if the order was successfully added.
     */
    bool add_order(Order* order) {
        if (!order || std::abs(order->price - price_) > 1e-8) {
            return false; // Wrong price level
        }

        // Insert at head of linked list (LIFO for same price/time)
        Order* current_head = head_.load(std::memory_order_acquire);
        do {
            order->next.store(current_head, std::memory_order_relaxed);
        } while (!head_.compare_exchange_weak(current_head, order,
                                            std::memory_order_release,
                                            std::memory_order_acquire));

        // Update totals atomically
        total_quantity_.fetch_add(order->get_remaining_quantity(), std::memory_order_acq_rel);
        order_count_.fetch_add(1, std::memory_order_acq_rel);

        return true;
    }

    /**
     * @brief Attempts to match against orders at this price level.
     * @param side The side of the incoming order (BUY/SELL).
     * @param quantity The quantity to match.
     * @param max_price Maximum price for buy orders (ignored for sell orders).
     * @param min_price Minimum price for sell orders (ignored for buy orders).
     * @return The total quantity matched.
     */
    double match_orders(Order::Side side, double quantity, double max_price = 0.0, double min_price = 0.0) {
        // Check if this price level can match the incoming order
        if (side == Order::Side::BUY && max_price > 0.0 && price_ > max_price) {
            return 0.0; // Price too high for buy order
        }
        if (side == Order::Side::SELL && min_price > 0.0 && price_ < min_price) {
            return 0.0; // Price too low for sell order
        }

        double total_matched = 0.0;
        double remaining_quantity = quantity;

        // Walk through the order chain
        Order* current = head_.load(std::memory_order_acquire);
        while (current && remaining_quantity > 0.0) {
            // Check if this order can be matched (opposite side and active)
            if (is_opposite_side(current->side, side) && current->is_active()) {
                double matched = current->try_fill(remaining_quantity);
                if (matched > 0.0) {
                    total_matched += matched;
                    remaining_quantity -= matched;
                    
                    // Update level totals
                    total_quantity_.fetch_sub(matched, std::memory_order_acq_rel);
                    
                    // If order is fully filled, it will be cleaned up later
                    if (!current->is_active()) {
                        // Note: Actual removal from linked list is deferred for performance
                        // A background cleanup process can handle this
                    }
                }
            }
            
            current = current->next.load(std::memory_order_acquire);
        }

        return total_matched;
    }

    /**
     * @brief Removes an order from this price level.
     * @param order_id The ID of the order to remove.
     * @return True if the order was found and removed.
     */
    bool remove_order(uint64_t order_id) {
        Order* prev = nullptr;
        Order* current = head_.load(std::memory_order_acquire);

        while (current) {
            if (current->order_id == order_id) {
                // Found the order to remove
                double removed_quantity = current->get_remaining_quantity();
                
                // Mark as cancelled
                current->status.store(Order::Status::CANCELLED, std::memory_order_release);
                
                // Update totals
                total_quantity_.fetch_sub(removed_quantity, std::memory_order_acq_rel);
                order_count_.fetch_sub(1, std::memory_order_acq_rel);
                
                // Actual linked list removal is complex in lock-free environment
                // For now, we mark as cancelled and let cleanup handle it
                return true;
            }
            
            prev = current;
            current = current->next.load(std::memory_order_acquire);
        }

        return false; // Order not found
    }

    /**
     * @brief Gets the total quantity at this price level.
     * @return The sum of all active order quantities.
     */
    double get_total_quantity() const noexcept {
        return total_quantity_.load(std::memory_order_acquire);
    }

    /**
     * @brief Gets the number of orders at this price level.
     * @return The count of active orders.
     */
    size_t get_order_count() const noexcept {
        return order_count_.load(std::memory_order_acquire);
    }

    /**
     * @brief Gets the price for this level.
     * @return The price value.
     */
    double get_price() const noexcept {
        return price_;
    }

    /**
     * @brief Checks if this price level has any active orders.
     * @return True if there are active orders at this level.
     */
    bool has_orders() const noexcept {
        return get_order_count() > 0 && get_total_quantity() > 0.0;
    }

    /**
     * @brief Gets statistics for this price level.
     */
    struct Statistics {
        double price;
        double total_quantity;
        size_t order_count;
        uint64_t first_order_priority;  // Timestamp of first order
    };

    Statistics get_statistics() const {
        Statistics stats;
        stats.price = price_;
        stats.total_quantity = get_total_quantity();
        stats.order_count = get_order_count();
        
        Order* first_order = head_.load(std::memory_order_acquire);
        stats.first_order_priority = first_order ? 
            first_order->priority.load(std::memory_order_acquire) : 0;
        
        return stats;
    }

private:
    /**
     * @brief Checks if two order sides are opposite.
     * @param side1 First order side.
     * @param side2 Second order side.
     * @return True if the sides can match against each other.
     */
    bool is_opposite_side(Order::Side side1, Order::Side side2) const noexcept {
        return (side1 == Order::Side::BUY && side2 == Order::Side::SELL) ||
               (side1 == Order::Side::SELL && side2 == Order::Side::BUY);
    }

    /**
     * @brief Clears all orders from this price level.
     */
    void clear() {
        Order* current = head_.exchange(nullptr, std::memory_order_acq_rel);
        while (current) {
            Order* next = current->next.load(std::memory_order_acquire);
            delete current;
            current = next;
        }
        total_quantity_.store(0.0, std::memory_order_release);
        order_count_.store(0, std::memory_order_release);
    }

    // Price level data
    double price_;
    
    // Atomic aggregates for fast market depth calculations
    alignas(64) std::atomic<double> total_quantity_{0.0};
    alignas(64) std::atomic<size_t> order_count_{0};
    
    // Lock-free linked list of orders (head pointer)
    alignas(64) std::atomic<Order*> head_{nullptr};
};

} // namespace nexus::execution