// src/cpp/core/thread_affinity.cpp

#include "core/thread_affinity.h"
#include <iostream>
#include <sstream>
#include <algorithm>
#include <thread>

namespace nexus::core {

size_t ThreadAffinity::get_cpu_count() noexcept {
    return std::thread::hardware_concurrency();
}

bool ThreadAffinity::pin_to_core(int core_id) noexcept {
    if (!is_valid_core_id(core_id)) {
        log_error("pin_to_core", "Invalid core ID: " + std::to_string(core_id));
        return false;
    }
    
    return set_affinity_impl({core_id});
}

bool ThreadAffinity::pin_to_cores(const std::vector<int>& core_ids) noexcept {
    if (core_ids.empty()) {
        log_error("pin_to_cores", "Empty core list provided");
        return false;
    }
    
    // Validate all core IDs
    for (int core_id : core_ids) {
        if (!is_valid_core_id(core_id)) {
            log_error("pin_to_cores", "Invalid core ID: " + std::to_string(core_id));
            return false;
        }
    }
    
    return set_affinity_impl(core_ids);
}

bool ThreadAffinity::set_real_time_priority(int priority) noexcept {
    if (priority < 1 || priority > 99) {
        log_error("set_real_time_priority", "Priority must be between 1 and 99");
        return false;
    }
    
    return set_priority_impl(priority, true);
}

bool ThreadAffinity::set_normal_priority() noexcept {
    return set_priority_impl(0, false);
}

bool ThreadAffinity::is_valid_core_id(int core_id) noexcept {
    return core_id >= 0 && core_id < static_cast<int>(get_cpu_count());
}

std::vector<int> ThreadAffinity::get_current_affinity() noexcept {
    std::vector<int> cores;
    
#ifdef _WIN32
    HANDLE thread = GetCurrentThread();
    DWORD_PTR affinity_mask = SetThreadAffinityMask(thread, ~0ULL);
    if (affinity_mask != 0) {
        SetThreadAffinityMask(thread, affinity_mask); // Restore original
        for (int i = 0; i < 64; ++i) {
            if (affinity_mask & (1ULL << i)) {
                cores.push_back(i);
            }
        }
    }
#elif defined(__linux__)
    cpu_set_t cpu_set;
    if (pthread_getaffinity_np(pthread_self(), sizeof(cpu_set), &cpu_set) == 0) {
        for (int i = 0; i < CPU_SETSIZE; ++i) {
            if (CPU_ISSET(i, &cpu_set)) {
                cores.push_back(i);
            }
        }
    }
#elif defined(__APPLE__)
    // macOS doesn't provide easy affinity querying, return all cores
    for (int i = 0; i < static_cast<int>(get_cpu_count()); ++i) {
        cores.push_back(i);
    }
#endif
    
    return cores;
}

std::string ThreadAffinity::get_thread_info() noexcept {
    std::ostringstream info;
    info << "Thread ID: " << std::this_thread::get_id() << ", ";
    
#ifdef _WIN32
    info << "Platform: Windows, ";
    HANDLE thread = GetCurrentThread();
    int priority = GetThreadPriority(thread);
    info << "Priority: " << priority;
#elif defined(__linux__)
    info << "Platform: Linux, ";
    int policy;
    struct sched_param param;
    if (pthread_getschedparam(pthread_self(), &policy, &param) == 0) {
        info << "Policy: " << policy << ", Priority: " << param.sched_priority;
    }
#elif defined(__APPLE__)
    info << "Platform: macOS, ";
    int policy;
    struct sched_param param;
    if (pthread_getschedparam(pthread_self(), &policy, &param) == 0) {
        info << "Policy: " << policy << ", Priority: " << param.sched_priority;
    }
#else
    info << "Platform: Unknown";
#endif
    
    auto affinity = get_current_affinity();
    info << ", Affinity: [";
    for (size_t i = 0; i < affinity.size(); ++i) {
        if (i > 0) info << ",";
        info << affinity[i];
    }
    info << "]";
    
    return info.str();
}

bool ThreadAffinity::isolate_cores(const std::vector<int>& core_ids) noexcept {
    if (core_ids.empty()) {
        log_error("isolate_cores", "Empty core list provided");
        return false;
    }
    
    // Validate all core IDs first
    for (int core_id : core_ids) {
        if (!is_valid_core_id(core_id)) {
            log_error("isolate_cores", "Invalid core ID: " + std::to_string(core_id));
            return false;
        }
    }
    
#ifdef __linux__
    // On Linux, we can attempt to use cgroups for core isolation
    // This requires root privileges, so we'll do best effort
    std::cout << "ThreadAffinity: Core isolation requested for cores: ";
    for (size_t i = 0; i < core_ids.size(); ++i) {
        if (i > 0) std::cout << ",";
        std::cout << core_ids[i];
    }
    std::cout << " (requires manual cgroups setup)" << std::endl;
    return true;
#else
    // On Windows and macOS, core isolation is not directly supported
    // Fall back to setting affinity for the current thread
    std::cout << "ThreadAffinity: Core isolation not supported on this platform, using affinity instead" << std::endl;
    return set_affinity_impl(core_ids);
#endif
}

// Platform-specific implementations

bool ThreadAffinity::set_affinity_impl(const std::vector<int>& core_ids) noexcept {
#ifdef _WIN32
    HANDLE thread = GetCurrentThread();
    DWORD_PTR affinity_mask = 0;
    
    for (int core_id : core_ids) {
        affinity_mask |= (1ULL << core_id);
    }
    
    DWORD_PTR result = SetThreadAffinityMask(thread, affinity_mask);
    if (result == 0) {
        log_error("set_affinity_impl", "SetThreadAffinityMask failed with error: " + std::to_string(GetLastError()));
        return false;
    }
    
    std::cout << "ThreadAffinity: Successfully pinned thread to cores: ";
    for (size_t i = 0; i < core_ids.size(); ++i) {
        if (i > 0) std::cout << ",";
        std::cout << core_ids[i];
    }
    std::cout << std::endl;
    return true;
    
#elif defined(__linux__)
    cpu_set_t cpu_set;
    CPU_ZERO(&cpu_set);
    
    for (int core_id : core_ids) {
        CPU_SET(core_id, &cpu_set);
    }
    
    int result = pthread_setaffinity_np(pthread_self(), sizeof(cpu_set), &cpu_set);
    if (result != 0) {
        log_error("set_affinity_impl", "pthread_setaffinity_np failed with error: " + std::to_string(result));
        return false;
    }
    
    std::cout << "ThreadAffinity: Successfully pinned thread to cores: ";
    for (size_t i = 0; i < core_ids.size(); ++i) {
        if (i > 0) std::cout << ",";
        std::cout << core_ids[i];
    }
    std::cout << std::endl;
    return true;
    
#elif defined(__APPLE__)
    // macOS doesn't support direct thread affinity, but we can set thread affinity policy
    // This is a best-effort approach
    if (core_ids.size() == 1) {
        thread_affinity_policy_data_t policy = { core_ids[0] };
        kern_return_t result = thread_policy_set(mach_thread_self(),
                                               THREAD_AFFINITY_POLICY,
                                               (thread_policy_t)&policy,
                                               THREAD_AFFINITY_POLICY_COUNT);
        
        if (result != KERN_SUCCESS) {
            log_error("set_affinity_impl", "thread_policy_set failed with error: " + std::to_string(result));
            return false;
        }
        
        std::cout << "ThreadAffinity: Set thread affinity hint for core: " << core_ids[0] << std::endl;
        return true;
    } else {
        std::cout << "ThreadAffinity: macOS supports single-core affinity hints only" << std::endl;
        return false;
    }
    
#else
    log_error("set_affinity_impl", "Thread affinity not supported on this platform");
    return false;
#endif
}

bool ThreadAffinity::set_priority_impl(int priority, bool real_time) noexcept {
#ifdef _WIN32
    HANDLE thread = GetCurrentThread();
    int win_priority;
    
    if (real_time) {
        // Map priority (1-99) to Windows real-time priorities
        if (priority >= 90) win_priority = THREAD_PRIORITY_TIME_CRITICAL;
        else if (priority >= 70) win_priority = THREAD_PRIORITY_HIGHEST;
        else if (priority >= 50) win_priority = THREAD_PRIORITY_ABOVE_NORMAL;
        else win_priority = THREAD_PRIORITY_NORMAL;
        
        // Try to set real-time priority class for the process
        HANDLE process = GetCurrentProcess();
        if (!SetPriorityClass(process, REALTIME_PRIORITY_CLASS)) {
            // Fall back to high priority class
            SetPriorityClass(process, HIGH_PRIORITY_CLASS);
        }
    } else {
        win_priority = THREAD_PRIORITY_NORMAL;
        HANDLE process = GetCurrentProcess();
        SetPriorityClass(process, NORMAL_PRIORITY_CLASS);
    }
    
    BOOL result = SetThreadPriority(thread, win_priority);
    if (!result) {
        log_error("set_priority_impl", "SetThreadPriority failed with error: " + std::to_string(GetLastError()));
        return false;
    }
    
    std::cout << "ThreadAffinity: Set thread priority to " << (real_time ? "real-time" : "normal") 
              << " (level " << priority << ")" << std::endl;
    return true;
    
#elif defined(__linux__) || defined(__APPLE__)
    struct sched_param param;
    int policy;
    
    if (real_time) {
        policy = SCHED_FIFO; // First-in-first-out real-time scheduling
        param.sched_priority = priority;
    } else {
        policy = SCHED_OTHER; // Normal scheduling
        param.sched_priority = 0;
    }
    
    int result = pthread_setschedparam(pthread_self(), policy, &param);
    if (result != 0) {
        log_error("set_priority_impl", "pthread_setschedparam failed with error: " + std::to_string(result));
        return false;
    }
    
    std::cout << "ThreadAffinity: Set thread priority to " << (real_time ? "real-time" : "normal") 
              << " (level " << priority << ")" << std::endl;
    return true;
    
#else
    log_error("set_priority_impl", "Thread priority setting not supported on this platform");
    return false;
#endif
}

void ThreadAffinity::log_error(const std::string& operation, const std::string& details) noexcept {
    std::cerr << "ThreadAffinity Error in " << operation << ": " << details << std::endl;
}

} // namespace nexus::core