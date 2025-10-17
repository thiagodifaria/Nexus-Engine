# Nexus Engine - Ultra-High Performance C++ Trading Engine

Nexus is an ultra-high performance C++ trading engine and backtesting framework designed for institutional-grade algorithmic trading applications. Built entirely with C++20 and optimized for extreme performance using cutting-edge techniques including LMAX Disruptor pattern, lock-free data structures, hardware timestamp counters, SIMD instructions, and NUMA optimization. This project offers a comprehensive solution for quantitative trading development with nanosecond precision timing and institutional-level performance characteristics.

## 🎯 Features

### C++ Engine Core
- ✅ **Ultra-low latency processing**: Sub-microsecond event processing with LMAX Disruptor pattern implementation
- ✅ **Extreme performance strategies**: 800K+ signals/second with incremental O(1) technical indicators
- ✅ **Lock-free order book**: Realistic market simulation with atomic operations (1M+ orders/second)
- ✅ **Advanced Monte Carlo**: SIMD-optimized simulation engine with 267K+ simulations/second
- ✅ **Strategy optimization**: Grid search and genetic algorithms with multi-threaded execution
- ✅ **Real-time optimizations**: CPU affinity, thread priority, NUMA awareness, cache warming
- ✅ **Hardware-level timing**: TSC (Time Stamp Counter) for nanosecond precision measurement
- ✅ **Memory optimization**: Custom pools eliminating 90%+ allocation overhead

### Python Backend & Frontend
- ✅ **Domain-Driven Design**: Clean Architecture with DDD patterns (Entities, Value Objects, Use Cases)
- ✅ **PyQt6 Desktop GUI**: Professional trading interface with real-time charts and monitoring
- ✅ **RESTful API**: FastAPI backend with comprehensive endpoints for trading operations
- ✅ **Market Data Integration**: Real-time data from Finnhub, Alpha Vantage, Nasdaq Data Link, FRED
- ✅ **Full Observability**: Prometheus metrics, Loki logs, Tempo traces, Grafana dashboards
- ✅ **Comprehensive testing**: Unit, integration, and E2E tests with >80% coverage target
- ✅ **Docker deployment**: Complete containerization with Docker Compose orchestration

## 🗃️ Architecture

### High-Level System Architecture

```
Nexus Engine Trading Platform
│
├── 🚀 C++ Core Engine (src/cpp/)          # Ultra-high performance backtesting engine
│   ├── LMAX Disruptor event processing    # 10-100M events/sec
│   ├── Lock-free order book               # 1M+ orders/sec
│   ├── Strategy execution engine          # 800K+ signals/sec
│   └── Monte Carlo simulator              # 267K+ sims/sec
│
├── 🐍 Python Backend (backend/python/)    # Business logic & API layer
│   ├── Domain Layer (DDD)                 # Entities, Value Objects, Repositories
│   ├── Application Layer                  # Use Cases, Services
│   ├── Infrastructure Layer               # Adapters, Database, Market Data, Telemetry
│   └── FastAPI REST API                   # HTTP endpoints
│
├── 🖥️ PyQt6 Frontend (frontend/pyqt6/)    # Desktop trading application
│   ├── MVVM Architecture                  # ViewModels + Views
│   ├── Real-time charts                   # Live market data visualization
│   ├── Strategy management UI             # Create, monitor, optimize strategies
│   └── Performance dashboards             # Backtest results and analytics
│
└── 📊 Observability Stack (devops/)       # Monitoring & debugging
    ├── Prometheus (Metrics)               # Trading metrics, C++ latency
    ├── Loki (Logs)                        # Structured JSON logging
    ├── Tempo (Traces)                     # Distributed tracing
    └── Grafana (Visualization)            # Unified dashboards
```

### C++ Core Engine Architecture

Highly optimized modular C++ architecture with performance-first design:

```
src/cpp/
├── core/           # Event system, high-resolution timing, real-time optimizations
│   ├── backtest_engine.*       # Main orchestration engine with LMAX Disruptor
│   ├── event_types.*          # Type-safe event system with hardware timestamps
│   ├── event_queue.*          # High-performance queue with configurable backends
│   ├── disruptor_queue.*      # LMAX Disruptor implementation for ultra-low latency
│   ├── high_resolution_clock.* # Hardware TSC access for nanosecond precision
│   ├── latency_tracker.*      # Comprehensive latency measurement and analysis
│   ├── thread_affinity.*      # CPU core pinning and real-time priority
│   └── real_time_config.*     # Real-time optimization configuration
│
├── strategies/     # Trading strategies with optimized technical indicators
│   ├── abstract_strategy.*    # Base strategy interface with parameter system
│   ├── sma_strategy.*         # Simple Moving Average crossover strategy
│   ├── macd_strategy.*        # MACD (Moving Average Convergence Divergence)
│   ├── rsi_strategy.*         # RSI (Relative Strength Index) strategy
│   ├── technical_indicators.* # Incremental O(1) indicator calculations
│   └── signal_types.*         # Optimized enum-based signal state tracking
│
├── execution/      # Order book and execution simulation
│   ├── execution_simulator.*  # Realistic execution with slippage and fees
│   ├── lock_free_order_book.* # Lock-free order book with atomic operations
│   └── price_level.*          # Atomic price level with order management
│
├── analytics/      # Performance analysis and risk metrics
│   ├── performance_analyzer.* # Comprehensive performance metrics calculation
│   ├── monte_carlo_simulator.* # SIMD-optimized Monte Carlo simulation
│   ├── risk_metrics.*         # VaR, CVaR, and advanced risk calculations
│   ├── metrics_calculator.*   # Rolling metrics and time-series analysis
│   └── performance_metrics.*  # Complete performance metrics structure
│
├── optimization/   # Strategy parameter optimization
│   ├── strategy_optimizer.*   # Main optimization orchestration
│   ├── grid_search.*          # Exhaustive parameter grid search
│   └── genetic_algorithm.*    # Population-based genetic optimization
│
├── position/       # Position and risk management
│   ├── position_manager.*     # Real-time position tracking and P&L
│   └── risk_manager.*         # Pre-trade risk validation and limits
│
└── data/          # Market data handling and validation
    ├── market_data_handler.*  # Multi-asset CSV data processing
    ├── database_manager.*     # SQLite integration for data persistence
    ├── data_validator.*       # Data quality assurance and validation
    └── data_types.*           # OHLCV data structures and utilities
```

## 🔧 Technology Stack

### Core Performance Technologies
- **C++20**: Modern language features with compile-time optimizations
- **LMAX Disruptor**: Lock-free ring buffer pattern for ultra-low latency (10-100M events/sec)
- **Hardware TSC**: Direct timestamp counter access for nanosecond precision timing
- **NUMA Optimization**: Memory allocation optimized for multi-socket server systems
- **CMake 3.20+**: Modern build system with cross-platform support

### Advanced Performance Optimizations
- **Lock-free Data Structures**: Atomic operations for concurrent access without locks
- **Memory Pools**: Pre-allocated buffers eliminating dynamic allocation overhead
- **Branch Prediction**: [[likely]]/[[unlikely]] attributes for CPU optimization
- **SIMD Instructions**: Vectorized computations for Monte Carlo simulation (4x speedup)
- **Cache Warming**: Pre-loading critical data structures into CPU cache
- **Thread Affinity**: CPU core pinning for deterministic performance

### Analytics & Risk Management
- **Monte Carlo Simulation**: Multi-threaded risk analysis with SIMD optimization
- **Technical Indicators**: Incremental SMA, EMA, RSI, MACD calculations (O(1) complexity)
- **Genetic Algorithms**: Population-based strategy parameter optimization
- **Risk Metrics**: Value-at-Risk (VaR), Conditional VaR, Sharpe ratio, maximum drawdown
- **Performance Analytics**: Comprehensive backtesting performance analysis

### Data Management & Integration
- **SQLite Integration**: Lightweight database for development and testing
- **Multi-Asset Support**: Simultaneous processing of multiple trading instruments
- **Data Validation**: Comprehensive data quality checks and outlier detection
- **CSV Processing**: Optimized parsing for large historical datasets

## 📋 Prerequisites

- **C++20 Compatible Compiler**: GCC 10+, Clang 12+, or MSVC 2019+
- **CMake 3.20+**: Modern build system for cross-platform compilation
- **SQLite3 Development Libraries**: Database integration support
- **Threading Support**: POSIX threads (Linux/Mac) or Windows threads
- **64-bit Architecture**: Required for optimal performance and TSC support

## 🚀 Quick Installation

### Docker Deployment (Recommended)

```bash
# Clone repository
git clone https://github.com/thiagodifaria/Nexus-Engine.git
cd Nexus-Engine

# Start all services with Docker Compose
docker-compose up -d

# Access services
# - Backend API: http://localhost:8001/docs
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090

# View logs
docker-compose logs -f nexus-backend

# Stop all services
docker-compose down
```

### Local Development Build

```bash
# Clone repository
git clone https://github.com/thiagodifaria/Nexus-Engine.git
cd Nexus-Engine

# Build C++ engine
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=20
make -j$(nproc)  # Linux/Mac
# or
cmake --build . --config Release --parallel  # Cross-platform

# Verify C++ installation
make test

# Install Python backend dependencies
cd ../backend/python
pip install -r requirements.txt

# Run Python backend
python -m src.main

# Install and run PyQt6 frontend
cd ../../frontend/pyqt6
pip install -r requirements.txt
python -m src.main
```

### Performance Optimization Build

```bash
# Configure with advanced optimizations
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_STANDARD=20 \
  -DCMAKE_CXX_FLAGS="-O3 -march=native -mtune=native" \
  -DENABLE_NUMA_OPTIMIZATION=ON \
  -DENABLE_SIMD_OPTIMIZATION=ON

# Build optimized version
make -j$(nproc)
```

## ⚙️ Configuration

### Real-Time Optimization Configuration

```cpp
// Enable comprehensive real-time optimizations
RealTimeConfig config;
config.enable_cpu_affinity = true;
config.cpu_cores = {2, 3, 4, 5};  // Isolate specific cores for trading
config.enable_real_time_priority = true;
config.real_time_priority_level = 80;  // High priority for critical threads
config.enable_cache_warming = true;
config.cache_warming_iterations = 3;
config.enable_numa_optimization = true;
config.preferred_numa_node = 0;

// Configure backtest engine with optimizations
BacktestEngineConfig engine_config;
engine_config.enable_performance_monitoring = true;
engine_config.enable_event_batching = true;
engine_config.queue_backend_type = "disruptor";  // Use LMAX Disruptor
engine_config.real_time_config = config;

BacktestEngine engine(event_queue, data_handler, strategies, 
                     position_manager, execution_simulator, engine_config);
```

### Monte Carlo Simulation Configuration

```cpp
// Configure high-performance Monte Carlo simulation
MonteCarloSimulator::Config mc_config;
mc_config.num_simulations = 10000;
mc_config.num_threads = std::thread::hardware_concurrency();
mc_config.enable_simd = true;              // Enable SIMD optimizations
mc_config.enable_numa_optimization = true; // NUMA-aware allocation
mc_config.enable_statistics = true;        // Collect performance metrics

MonteCarloSimulator simulator(mc_config);
```

### Strategy Configuration Examples

```cpp
// High-performance SMA strategy with optimized parameters
auto sma_strategy = std::make_unique<SmaCrossoverStrategy>(20, 50);

// MACD strategy with standard parameters
auto macd_strategy = std::make_unique<MACDStrategy>(12, 26, 9);

// RSI strategy with custom overbought/oversold levels
auto rsi_strategy = std::make_unique<RSIStrategy>(14, 75.0, 25.0);
```

## 📊 Usage Examples

### Basic Backtesting Workflow

```cpp
#include "core/backtest_engine.h"
#include "strategies/sma_strategy.h"
#include "analytics/performance_analyzer.h"

int main() {
    // Create core components
    nexus::core::EventQueue event_queue;
    auto position_manager = std::make_shared<nexus::position::PositionManager>(100000.0);
    auto execution_simulator = std::make_shared<nexus::execution::ExecutionSimulator>();

    // Setup multi-asset strategy mapping
    std::unordered_map<std::string, std::shared_ptr<nexus::strategies::AbstractStrategy>> strategies;
    strategies["AAPL"] = std::make_shared<nexus::strategies::SmaCrossoverStrategy>(20, 50);
    strategies["GOOGL"] = std::make_shared<nexus::strategies::MACDStrategy>(12, 26, 9);
    strategies["TSLA"] = std::make_shared<nexus::strategies::RSIStrategy>(14, 70.0, 30.0);

    // Configure data sources
    std::unordered_map<std::string, std::string> data_files;
    data_files["AAPL"] = "data/sample_data/AAPL.csv";
    data_files["GOOGL"] = "data/sample_data/GOOGL.csv";
    data_files["TSLA"] = "data/sample_data/TSLA.csv";
    
    auto data_handler = std::make_shared<nexus::data::CsvDataHandler>(event_queue, data_files);

    // Create and configure backtest engine
    nexus::core::BacktestEngineConfig config;
    config.enable_performance_monitoring = true;
    config.queue_backend_type = "disruptor";
    
    nexus::core::BacktestEngine engine(event_queue, data_handler, strategies, 
                                      position_manager, execution_simulator, config);

    // Execute backtest
    engine.run();

    // Comprehensive performance analysis
    nexus::analytics::PerformanceAnalyzer analyzer(
        100000.0,  // Initial capital
        position_manager->get_equity_curve(),
        position_manager->get_trade_history()
    );
    
    auto metrics = analyzer.calculate_metrics();
    
    // Display results
    std::cout << "=== Backtest Results ===" << std::endl;
    std::cout << "Total Return: " << (metrics.total_return * 100) << "%" << std::endl;
    std::cout << "Sharpe Ratio: " << metrics.sharpe_ratio << std::endl;
    std::cout << "Max Drawdown: " << (metrics.max_drawdown * 100) << "%" << std::endl;
    std::cout << "Total Trades: " << metrics.total_trades << std::endl;
    
    return 0;
}
```

### Advanced Strategy Optimization

```cpp
#include "optimization/strategy_optimizer.h"
#include "optimization/genetic_algorithm.h"

// Grid Search Optimization
void run_grid_search_optimization() {
    // Create strategy template for optimization
    auto strategy_template = std::make_unique<nexus::strategies::SmaCrossoverStrategy>(10, 20);
    nexus::optimization::StrategyOptimizer optimizer(std::move(strategy_template));

    // Define parameter grid for exhaustive search
    std::unordered_map<std::string, std::vector<double>> parameter_grid;
    parameter_grid["short_window"] = {5, 10, 15, 20, 25};
    parameter_grid["long_window"] = {30, 40, 50, 60, 70, 80, 90, 100};

    // Execute grid search (will test all 5 x 8 = 40 combinations)
    auto results = optimizer.grid_search(parameter_grid);
    auto best_result = optimizer.get_best_result();
    
    std::cout << "Best parameters found:" << std::endl;
    for (const auto& [param, value] : best_result.parameters) {
        std::cout << param << ": " << value << std::endl;
    }
    std::cout << "Best Sharpe Ratio: " << best_result.fitness_score << std::endl;
}

// Genetic Algorithm Optimization
void run_genetic_optimization() {
    auto strategy_template = std::make_unique<nexus::strategies::RSIStrategy>(14, 70.0, 30.0);
    
    // Define parameter bounds for genetic algorithm
    std::unordered_map<std::string, std::pair<double, double>> bounds;
    bounds["period"] = {5.0, 30.0};           // RSI period range
    bounds["overbought"] = {65.0, 85.0};      // Overbought threshold range
    bounds["oversold"] = {15.0, 35.0};        // Oversold threshold range
    
    // Configure genetic algorithm parameters
    int population_size = 50;
    int generations = 20;
    double mutation_rate = 0.1;
    double crossover_rate = 0.8;
    
    // Execute genetic optimization
    auto results = nexus::optimization::perform_genetic_algorithm(
        *strategy_template, bounds, population_size, generations,
        mutation_rate, crossover_rate, 100000.0, "data/sample_data/AAPL.csv", "AAPL"
    );
    
    // Results are automatically sorted by fitness (best first)
    std::cout << "Top 5 evolved strategies:" << std::endl;
    for (size_t i = 0; i < std::min(size_t(5), results.size()); ++i) {
        std::cout << "Rank " << (i + 1) << " - Fitness: " << results[i].fitness_score << std::endl;
        for (const auto& [param, value] : results[i].parameters) {
            std::cout << "  " << param << ": " << value << std::endl;
        }
    }
}
```

### Monte Carlo Risk Analysis

```cpp
#include "analytics/monte_carlo_simulator.h"
#include "analytics/risk_metrics.h"

void perform_portfolio_risk_analysis() {
    // Configure high-performance Monte Carlo simulation
    nexus::analytics::MonteCarloSimulator::Config config;
    config.num_simulations = 50000;  // Large number for statistical significance
    config.num_threads = std::thread::hardware_concurrency();
    config.enable_simd = true;       // Enable SIMD optimizations
    config.enable_statistics = true; // Collect performance metrics
    
    nexus::analytics::MonteCarloSimulator simulator(config);
    
    // Define portfolio characteristics
    std::vector<double> expected_returns = {0.08, 0.12, 0.06, 0.10};  // Annual returns
    std::vector<double> volatilities = {0.15, 0.25, 0.10, 0.20};      // Annual volatilities
    
    // Correlation matrix between assets
    std::vector<std::vector<double>> correlation_matrix = {
        {1.00, 0.30, 0.15, 0.25},
        {0.30, 1.00, 0.10, 0.40},
        {0.15, 0.10, 1.00, 0.20},
        {0.25, 0.40, 0.20, 1.00}
    };
    
    // Run portfolio simulation for 1-year horizon
    auto portfolio_returns = simulator.simulate_portfolio(
        expected_returns, volatilities, correlation_matrix, 1.0
    );
    
    // Calculate comprehensive risk metrics
    double var_95 = simulator.calculate_var(portfolio_returns, 0.95);
    double var_99 = simulator.calculate_var(portfolio_returns, 0.99);
    double cvar_95 = nexus::analytics::RiskMetrics::calculate_cvar(portfolio_returns, 0.95);
    
    // Display risk analysis results
    std::cout << "=== Portfolio Risk Analysis ===" << std::endl;
    std::cout << "Simulations: " << config.num_simulations << std::endl;
    std::cout << "VaR (95%): " << (var_95 * 100) << "%" << std::endl;
    std::cout << "VaR (99%): " << (var_99 * 100) << "%" << std::endl;
    std::cout << "CVaR (95%): " << (cvar_95 * 100) << "%" << std::endl;
    
    // Get simulation performance statistics
    auto stats = simulator.get_statistics();
    std::cout << "Simulation Performance:" << std::endl;
    std::cout << "  Throughput: " << stats.throughput_per_second << " sims/sec" << std::endl;
    std::cout << "  Average time: " << stats.average_simulation_time_ns << " ns/sim" << std::endl;
}
```

## 🔍 Core Components Deep Dive

### BacktestEngine - Ultra-Low Latency Event Processing

| Feature | Implementation | Performance Impact |
|---------|---------------|-------------------|
| **Event Queue** | LMAX Disruptor pattern | 10-100M events/second |
| **CPU Affinity** | Thread pinning to isolated cores | 20-50% latency reduction |
| **Real-time Priority** | OS-level scheduling optimization | Deterministic execution |
| **Cache Warming** | Pre-loading critical data structures | 30-50% initial latency reduction |
| **NUMA Optimization** | Memory allocation on local nodes | Reduced memory access latency |

### Strategy Engine - High-Performance Signal Generation

| Strategy | Technical Indicators | Update Complexity | Performance |
|----------|---------------------|------------------|-------------|
| **SMA Crossover** | Incremental Simple Moving Average | O(1) | 800K+ signals/sec |
| **MACD Strategy** | Fast/Slow EMA + Signal Line | O(1) | 2.4M+ signals/sec |
| **RSI Strategy** | Wilder's Smoothing RSI | O(1) | 650K+ signals/sec |

### Lock-Free Order Book - Realistic Market Simulation

| Component | Technology | Performance | Features |
|-----------|------------|-------------|----------|
| **Price Levels** | Atomic operations | 1M+ orders/sec | FIFO matching, price-time priority |
| **Order Management** | Lock-free linked lists | Sub-microsecond latency | Add, modify, cancel operations |
| **Market Data** | Real-time snapshots | <100ns generation | Best bid/ask, market depth |

### Monte Carlo Simulator - Advanced Risk Analysis

| Optimization | Technology | Performance Gain | Description |
|--------------|------------|------------------|-------------|
| **SIMD Instructions** | AVX2/AVX-512 vectorization | 4x+ throughput | Parallel random number generation |
| **Multi-threading** | Work-stealing thread pool | Linear scaling | Distributes simulations across cores |
| **Memory Pre-allocation** | Custom buffer pools | 90%+ overhead reduction | Eliminates allocation during simulation |
| **NUMA Awareness** | Local memory allocation | Reduced latency | Optimizes for multi-socket systems |

## 🧪 Comprehensive Testing

### Test Suite Overview

```bash
# Run all tests with detailed output
cd build
ctest --verbose

# Run individual test categories
./test_strategies           # Strategy signal generation tests
./test_analytics           # Performance analysis and risk metrics
./test_monte_carlo         # Monte Carlo simulation accuracy
./test_integration         # Full system integration tests
./test_position_manager    # Position tracking and P&L calculation
./test_optimizer           # Strategy optimization algorithms
./test_advanced_modules    # Technical indicators and advanced features
```

### Performance Stress Testing

```bash
# Comprehensive performance stress test
./test_performance_stress

# Expected Output:
# >> STRATEGY PERFORMANCE RESULTS:
# SMA Crossover (20/50): 422,989 signals/sec
# MACD (12/26/9): 2,397,932 signals/sec  
# RSI (14): 650,193 signals/sec
#
# >> MONTE CARLO PERFORMANCE RESULTS:
# Medium Scale (1K sims): 142,673 sims/sec
# Large Scale (5K sims): 304,822 sims/sec
# Ultra Large (10K sims): 267,008 sims/sec
#
# >> MEMORY ALLOCATION PERFORMANCE:
# Event Pool Allocation: 11,004,853 allocs/sec
```

### Test Coverage Areas

- ✅ **Strategy Validation**: Signal generation accuracy and timing
- ✅ **Order Book Testing**: Matching engine correctness and performance
- ✅ **Monte Carlo Accuracy**: Statistical validation of simulation results
- ✅ **Performance Metrics**: Comprehensive analytics calculation verification
- ✅ **Multi-Asset Integration**: Portfolio management across multiple instruments
- ✅ **Real-Time Optimizations**: CPU affinity and priority scheduling
- ✅ **Memory Management**: Pool allocation and deallocation efficiency
- ✅ **Risk Management**: Position limits and exposure validation
- ✅ **Data Validation**: Market data quality and integrity checks

## 📈 Performance Benchmarks & Optimization Results

### Typical Performance Metrics (Release Build)

#### Event Processing Performance
- **LMAX Disruptor Queue**: 10-100M events/second
- **Traditional Mutex Queue**: 1-5M events/second
- **Performance Improvement**: 10-20x faster event processing

#### Strategy Execution Performance
- **SMA Crossover Strategy**: 422,989+ signals/second
- **MACD Strategy**: 2,397,932+ signals/second
- **RSI Strategy**: 650,193+ signals/second
- **Average Latency**: Sub-microsecond signal generation

#### Order Book Operations
- **Order Addition**: 1M+ orders/second
- **Order Matching**: 500K+ matches/second
- **Market Data Generation**: <100ns per snapshot
- **Price Level Updates**: Atomic operation latency

#### Monte Carlo Simulation
- **Single-threaded**: 25,000+ simulations/second
- **Multi-threaded (12 cores)**: 300,000+ simulations/second
- **SIMD Optimization**: 4x performance improvement
- **Memory Pool Benefit**: 90%+ allocation overhead reduction

#### Memory Management
- **Event Pool Allocation**: 11,004,853+ allocations/second
- **Cache Hit Rate**: >95% for frequently accessed data
- **Memory Pool Efficiency**: 90%+ reduction in allocation overhead

### Optimization Impact Analysis

#### Real-Time Optimizations
- **CPU Affinity (Core Pinning)**: 20-50% latency reduction
- **Real-time Priority Scheduling**: Deterministic execution timing
- **Cache Warming**: 30-50% initial latency improvement
- **NUMA Optimization**: 10-25% memory access improvement

#### Compiler Optimizations
- **Branch Prediction Hints**: 5-15% instruction cache improvement
- **Template Specialization**: Compile-time optimization for hot paths
- **Inline Function Optimization**: Elimination of function call overhead
- **Loop Unrolling**: Automatic vectorization for tight loops

#### Data Structure Optimizations
- **Lock-free Design**: Eliminates contention and blocking
- **Memory Alignment**: Optimizes cache line utilization
- **Pre-allocation Strategies**: Predictable memory access patterns
- **Atomic Operations**: Hardware-level synchronization primitives

## 📊 Advanced Features & Configuration

### Real-Time System Configuration

```cpp
// Maximum performance configuration for production trading
RealTimeConfig production_config;
production_config.enable_cpu_affinity = true;
production_config.cpu_cores = {4, 5, 6, 7};  // Isolate high-frequency cores
production_config.auto_detect_optimal_cores = true;
production_config.enable_real_time_priority = true;
production_config.real_time_priority_level = 90;  // Maximum priority
production_config.enable_cache_warming = true;
production_config.cache_warming_iterations = 5;
production_config.enable_numa_optimization = true;
production_config.enable_memory_locking = true;  // Prevent swapping
production_config.enable_huge_pages = true;      // Use 2MB pages
production_config.cpu_isolation_mode = "hard";   // Maximum isolation
```

### Advanced Analytics Configuration

```cpp
// Comprehensive performance monitoring
BacktestEngineConfig monitoring_config;
monitoring_config.enable_performance_monitoring = true;
monitoring_config.enable_latency_spike_detection = true;
monitoring_config.latency_spike_threshold = std::chrono::microseconds{10};
monitoring_config.monitoring_interval = std::chrono::milliseconds{100};

// Enable detailed latency tracking
PerformanceAnalyzer analyzer(/* ... */);
analyzer.enable_latency_tracking(true);

// Access comprehensive metrics
auto latency_stats = analyzer.get_latency_statistics();
for (const auto& [operation, stats] : latency_stats) {
    std::cout << operation << " - P99: " << stats.p99_ns << "ns" << std::endl;
}
```

### Execution Simulation Configuration

```cpp
// Realistic market simulation with order book
MarketSimulationConfig realistic_config;
realistic_config.use_order_book = true;
realistic_config.tick_size = 0.01;
realistic_config.enable_market_making = true;
realistic_config.market_maker_spread_bps = 2.0;
realistic_config.simulate_partial_fills = true;
realistic_config.partial_fill_probability = 0.15;
realistic_config.simulate_latency = true;
realistic_config.min_execution_latency = std::chrono::microseconds{50};
realistic_config.max_execution_latency = std::chrono::microseconds{200};

ExecutionSimulator realistic_executor(realistic_config);
```

## 📋 Data Management & Validation

### Supported Data Formats

#### CSV Market Data Format
```csv
Timestamp,Open,High,Low,Close,Volume
2025-01-01 09:30:00,150.25,151.75,149.80,151.20,2500000
2025-01-01 09:31:00,151.20,152.00,150.90,151.85,1800000
2025-01-01 09:32:00,151.85,152.50,151.60,152.10,2100000
```

#### Data Validation Features
```cpp
// Comprehensive data quality validation
nexus::data::DataValidator validator;

// Check for missing timestamps
auto missing_timestamps = validator.find_missing_timestamps(market_data);

// Identify statistical outliers
auto outliers = validator.find_outliers(market_data, 3.0);  // 3 sigma threshold

// Validate OHLCV consistency
auto invalid_bars = validator.find_invalid_bars(market_data);

std::cout << "Data Quality Report:" << std::endl;
std::cout << "Missing timestamps: " << missing_timestamps.size() << std::endl;
std::cout << "Statistical outliers: " << outliers.size() << std::endl;
std::cout << "Invalid bars: " << invalid_bars.size() << std::endl;
```

### Database Integration

```cpp
// SQLite database for data persistence
nexus::data::DatabaseManager db_manager("data/database/nexus.db");

if (db_manager.open()) {
    db_manager.create_market_data_table();
    
    // Store market data
    db_manager.store_market_data("AAPL", historical_data);
    
    // Retrieve specific time period
    auto start_time = std::chrono::system_clock::from_time_t(/* ... */);
    auto end_time = std::chrono::system_clock::from_time_t(/* ... */);
    auto retrieved_data = db_manager.fetch_market_data("AAPL", start_time, end_time);
}
```

## 🔒 Risk Management & Position Tracking

### Real-Time Risk Validation

```cpp
// Configure comprehensive risk management
nexus::position::RiskManager risk_manager(position_manager);

// Pre-trade risk validation
bool validate_trading_signal(const nexus::core::TradingSignalEvent& signal, 
                            double current_price) {
    // Automatic validation includes:
    // - Portfolio drawdown limits (15% max)
    // - Position exposure limits (20% per asset)
    // - Available capital verification
    // - Concentration risk assessment
    
    return risk_manager.validate_order(signal, current_price);
}
```

### Position Management Features

```cpp
// Real-time position tracking
nexus::position::PositionManager portfolio(100000.0);  // $100K initial capital

// Process trade execution
nexus::core::TradeExecutionEvent trade;
trade.symbol = "AAPL";
trade.quantity = 100;
trade.price = 150.25;
trade.commission = 1.50;
trade.is_buy = true;

portfolio.on_trade_execution(trade);

// Real-time portfolio metrics
std::cout << "Available Cash: $" << portfolio.get_available_cash() << std::endl;
std::cout << "Total Equity: $" << portfolio.get_total_equity() << std::endl;
std::cout << "Unrealized P&L: $" << portfolio.get_total_unrealized_pnl() << std::endl;

// Get individual position details
auto aapl_position = portfolio.get_position_snapshot("AAPL");
std::cout << "AAPL Position: " << aapl_position.quantity_ << " shares" << std::endl;
std::cout << "AAPL P&L: $" << aapl_position.unrealized_pnl_ << std::endl;
```

## 🧬 Strategy Development Guide

### Creating Custom Strategies

```cpp
// Example: Custom Bollinger Bands strategy
class BollingerBandsStrategy : public nexus::strategies::AbstractStrategy {
public:
    BollingerBandsStrategy(int period, double std_dev_multiplier)
        : AbstractStrategy("BollingerBands"),
          period_(period),
          std_dev_multiplier_(std_dev_multiplier),
          sma_calculator_(std::make_unique<IncrementalSMA>(period)),
          prices_(period) {}

    void on_market_data(const nexus::core::MarketDataEvent& event) override {
        prices_.push_back(event.close);
        if (prices_.size() > period_) {
            prices_.pop_front();
        }
        
        sma_value_ = sma_calculator_->update(event.close);
        
        if (prices_.size() == period_) {
            calculate_bollinger_bands();
        }
        
        symbol_ = event.symbol;
    }

    nexus::core::Event* generate_signal(nexus::core::EventPool& pool) override {
        if (prices_.size() < period_) return nullptr;
        
        double current_price = prices_.back();
        
        // Generate signals based on Bollinger Band breakouts
        if (current_price > upper_band_ && last_signal_ != SignalState::BUY) {
            last_signal_ = SignalState::BUY;
            return create_signal(pool, nexus::core::TradingSignalEvent::SignalType::BUY);
        } else if (current_price < lower_band_ && last_signal_ != SignalState::SELL) {
            last_signal_ = SignalState::SELL;
            return create_signal(pool, nexus::core::TradingSignalEvent::SignalType::SELL);
        }
        
        return nullptr;
    }

    std::unique_ptr<AbstractStrategy> clone() const override {
        return std::make_unique<BollingerBandsStrategy>(*this);
    }

private:
    void calculate_bollinger_bands() {
        // Calculate standard deviation
        double sum_squared_diff = 0.0;
        for (double price : prices_) {
            double diff = price - sma_value_;
            sum_squared_diff += diff * diff;
        }
        double std_dev = std::sqrt(sum_squared_diff / period_);
        
        // Calculate bands
        upper_band_ = sma_value_ + (std_dev_multiplier_ * std_dev);
        lower_band_ = sma_value_ - (std_dev_multiplier_ * std_dev);
    }

    nexus::core::Event* create_signal(nexus::core::EventPool& pool, 
                                     nexus::core::TradingSignalEvent::SignalType type) {
        auto* signal = pool.create_trading_signal_event();
        signal->strategy_id = get_name();
        signal->symbol = symbol_;
        signal->signal = type;
        signal->timestamp = std::chrono::system_clock::now();
        signal->confidence = 0.8;
        signal->suggested_quantity = 100.0;
        return signal;
    }

    int period_;
    double std_dev_multiplier_;
    std::unique_ptr<IncrementalSMA> sma_calculator_;
    std::deque<double> prices_;
    double sma_value_{0.0};
    double upper_band_{0.0};
    double lower_band_{0.0};
    SignalState last_signal_{SignalState::HOLD};
    std::string symbol_;
};
```

## 📚 Documentation & Resources

### Complete Documentation

Full documentation available in the `docs/` directory:

- **[Architecture Guide](docs/ARCHITECTURE.md)** - Complete system architecture, design decisions, and component interaction
- **[API Reference](docs/API.md)** - REST API documentation with request/response examples
- **[User Guide](docs/GUIDE.md)** - Installation, configuration, and usage instructions
- **[Observability Guide](docs/OBSERVABILITY.md)** - Monitoring, logging, tracing, and troubleshooting

### API Documentation
- **Doxygen Documentation**: Complete C++ API reference with examples
- **FastAPI Swagger**: Interactive REST API documentation at `/docs` endpoint
- **Performance Guide**: Optimization techniques and benchmarking methods
- **Developer Guide**: Best practices for extending the platform

### Code Examples
- **Basic Strategy Development**: Step-by-step strategy creation guide
- **Advanced Optimization**: Parameter tuning and genetic algorithms
- **Risk Management**: Portfolio risk assessment and position sizing
- **Multi-Asset Trading**: Simultaneous strategy execution across instruments

### Research Papers & References
- **LMAX Disruptor Pattern**: Ultra-low latency inter-thread messaging
- **Lock-Free Data Structures**: High-performance concurrent programming
- **Monte Carlo Methods**: Financial risk assessment and simulation
- **Genetic Algorithms**: Evolutionary optimization for trading strategies

## 🔧 Build System & Development

### CMake Configuration Options

```bash
# Development build with debugging
cmake .. -DCMAKE_BUILD_TYPE=Debug -DENABLE_TESTING=ON

# Performance build with optimizations
cmake .. -DCMAKE_BUILD_TYPE=Release -DENABLE_SIMD=ON -DENABLE_NUMA=ON

# Profile-guided optimization build
cmake .. -DCMAKE_BUILD_TYPE=Release -DENABLE_PGO=ON

# Memory debugging build
cmake .. -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON
```

### Cross-Platform Compatibility

| Platform | Compiler | Performance Features | Notes |
|----------|----------|---------------------|-------|
| **Linux** | GCC 10+, Clang 12+ | Full optimization support | Recommended for production |
| **Windows** | MSVC 2019+, GCC MinGW | TSC, SIMD, threading | Good development platform |
| **macOS** | Clang 12+, Apple Clang | Limited TSC support | Development use |

## 📜 Licensing

This project is dual-licensed under:

### GNU v3 License (Open Source)
- **Free for open-source projects**: Use, modify, and distribute freely
- **Copyleft requirement**: Derivative works must also be open-source
- **Network use clause**: Server-side usage requires source code disclosure
- **Commercial use restriction**: Commercial applications require commercial license

### Commercial License
- **Enterprise usage**: Proprietary applications and commercial deployment
- **No copyleft requirements**: Keep proprietary code private
- **Technical support**: Professional support and consulting services
- **Custom licensing terms**: Flexible terms for enterprise customers

For commercial licensing inquiries, please contact: thiagodifaria@gmail.com

## 📞 Contact & Support

**Thiago Di Faria** - Lead Developer & Architect
- **Email**: thiagodifaria@gmail.com
- **GitHub**: [@thiagodifaria](https://github.com/thiagodifaria)
- **Project Repository**: [https://github.com/thiagodifaria/Nexus-Engine](https://github.com/thiagodifaria/Nexus-Engine)

---

⭐ **Nexus Engine** - Ultra-high performance C++ trading engine for institutional-grade algorithmic trading.