cmake_minimum_required(VERSION 3.20)
project(nexus_trading_platform)

# Set C++ standard
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Set compiler-specific options
if(MSVC)
    add_compile_options(/W4 /permissive- /Zc:__cplusplus)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
else()
    add_compile_options(-Wall -Wextra -pedantic)
endif()

# Find required packages
find_package(SQLite3 REQUIRED)

# Add threading support - NEW: Required for real-time optimizations
find_package(Threads REQUIRED)

# Include directories
include_directories(src/cpp)

# Source files
set(CORE_SOURCES
    src/cpp/core/backtest_engine.cpp
    src/cpp/core/thread_affinity.cpp
    src/cpp/core/exporter.cpp
    src/cpp/core/latency_tracker.cpp
    src/cpp/core/high_resolution_clock.cpp
)

set(DATA_SOURCES
    src/cpp/data/market_data_handler.cpp
    src/cpp/data/database_manager.cpp
    src/cpp/data/data_validator.cpp
)

set(STRATEGY_SOURCES
    src/cpp/strategies/sma_strategy.cpp
    src/cpp/strategies/macd_strategy.cpp
    src/cpp/strategies/rsi_strategy.cpp
    src/cpp/strategies/technical_indicators.cpp
)

set(ANALYTICS_SOURCES
    src/cpp/analytics/performance_analyzer.cpp
    src/cpp/analytics/monte_carlo_simulator.cpp
    src/cpp/analytics/metrics_calculator.cpp
    src/cpp/analytics/risk_metrics.cpp
)

set(EXECUTION_SOURCES
    src/cpp/execution/execution_simulator.cpp
    src/cpp/execution/lock_free_order_book.cpp
)

set(POSITION_SOURCES
    src/cpp/position/position_manager.cpp
    src/cpp/position/risk_manager.cpp
)

set(OPTIMIZATION_SOURCES
    src/cpp/optimization/strategy_optimizer.cpp
    src/cpp/optimization/grid_search.cpp
    src/cpp/optimization/genetic_algorithm.cpp
)

set(BINDINGS_SOURCES
    src/cpp/bindings/python_bindings.cpp
)

# Combine all sources
set(ALL_SOURCES
    ${CORE_SOURCES}
    ${DATA_SOURCES}
    ${STRATEGY_SOURCES}
    ${ANALYTICS_SOURCES}
    ${EXECUTION_SOURCES}
    ${POSITION_SOURCES}
    ${OPTIMIZATION_SOURCES}
    ${BINDINGS_SOURCES}
)

# Create main library
add_library(nexus_trading_lib ${ALL_SOURCES})

# Link libraries - UPDATED: Added threading support
target_link_libraries(nexus_trading_lib 
    SQLite::SQLite3
    Threads::Threads
)

# Enable testing
enable_testing()

# Test files - only include implemented tests
set(TEST_SOURCES
    tests/cpp/test_analytics.cpp
    tests/cpp/test_position_manager.cpp
    tests/cpp/test_integration.cpp
    tests/cpp/test_optimizer.cpp
    tests/cpp/test_monte_carlo.cpp
    tests/cpp/test_multi_asset_integration.cpp
    tests/cpp/test_advanced_modules.cpp
    tests/cpp/test_sma_strategy.cpp
)

# Individual test executables
foreach(test_source ${TEST_SOURCES})
    get_filename_component(test_name ${test_source} NAME_WE)
    add_executable(${test_name} ${test_source})
    target_link_libraries(${test_name} nexus_trading_lib)
    
    # Add test to CTest - Exclude stress test from Release configuration
    if(test_name STREQUAL "test_performance_stress")
        # Add stress test but exclude it from Release configuration
        add_test(NAME ${test_name} COMMAND ${test_name})
        set_tests_properties(${test_name} PROPERTIES
            LABELS "stress;performance"
            EXCLUDE_FROM_DEFAULT_BUILD_Debug OFF
            EXCLUDE_FROM_DEFAULT_BUILD_Release ON
        )
        set_tests_properties(${test_name} PROPERTIES
            CONFIGURATION "Debug"
        )
    else()
        # Regular tests - run in all configurations
        add_test(NAME ${test_name} COMMAND ${test_name})
        set_tests_properties(${test_name} PROPERTIES
            LABELS "unit;fast"
        )
    endif()
endforeach()

# Performance stress test with special configuration
add_executable(test_performance_stress tests/cpp/test_performance_stress.cpp)
target_link_libraries(test_performance_stress nexus_trading_lib)

# Add the stress test but configure it to be excluded from Release runs
add_test(NAME test_performance_stress COMMAND test_performance_stress)
set_tests_properties(test_performance_stress PROPERTIES
    LABELS "stress;performance;long_running"
    TIMEOUT 300  # 5 minute timeout for stress tests
)

# Custom test configuration to exclude stress tests from Release
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    set_tests_properties(test_performance_stress PROPERTIES
        DISABLED TRUE
    )
endif()

# Installation rules
install(TARGETS nexus_trading_lib
    RUNTIME DESTINATION bin
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

# Install headers
install(DIRECTORY src/cpp/
    DESTINATION include
    FILES_MATCHING PATTERN "*.h"
)

# Custom CTest configuration file to handle test exclusions
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/CTestCustom.cmake.in")
    configure_file(
        "${CMAKE_CURRENT_SOURCE_DIR}/CTestCustom.cmake.in"
        "${CMAKE_CURRENT_BINARY_DIR}/CTestCustom.cmake"
        @ONLY
    )
endif()

# Set up CTest to use the custom configuration
set(CTEST_CUSTOM_CONFIGURATION_TYPE "Release")

# Create a custom target for running only fast tests
add_custom_target(test_fast
    COMMAND ${CMAKE_CTEST_COMMAND} --verbose -L "fast"
    DEPENDS ${TEST_SOURCES}
    COMMENT "Running fast unit tests only"
)

# Create a custom target for running stress tests explicitly
add_custom_target(test_stress
    COMMAND ${CMAKE_CTEST_COMMAND} --verbose -L "stress"
    DEPENDS test_performance_stress
    COMMENT "Running performance stress tests"
)

# Print configuration summary
message(STATUS "Nexus Trading Platform Configuration:")
message(STATUS "  C++ Standard: ${CMAKE_CXX_STANDARD}")
message(STATUS "  Build Type: ${CMAKE_BUILD_TYPE}")
message(STATUS "  Compiler: ${CMAKE_CXX_COMPILER_ID}")
message(STATUS "  Threading Support: ${CMAKE_THREAD_LIBS_INIT}")
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    message(STATUS "  Note: Stress tests are excluded from Release configuration")
endif()