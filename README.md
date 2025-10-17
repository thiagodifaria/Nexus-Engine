# Nexus Engine

![Nexus Logo](https://img.shields.io/badge/Nexus-Trading%20Platform-blue?style=for-the-badge&logo=chart-line)

**Ultra-High Performance C++ Trading Engine & Backtesting Framework**

[![C++](https://img.shields.io/badge/C++-20-00599c?style=flat&logo=cplusplus&logoColor=white)](https://isocpp.org)
[![CMake](https://img.shields.io/badge/CMake-3.20+-064f8c?style=flat&logo=cmake&logoColor=white)](https://cmake.org)
[![LMAX](https://img.shields.io/badge/LMAX-Disruptor-red?style=flat)](https://lmax-exchange.github.io/disruptor/)
[![License](https://img.shields.io/badge/License-GNU%20v3%20%2B%20Commercial-green.svg?style=flat)](LICENSE)
[![Development](https://img.shields.io/badge/Status-In%20Development-orange?style=flat)](https://github.com/thiagodifaria/nexus-trading)

---

## 🌍 **Documentation / Documentação**

**📖 [🇺🇸 Read in English](README_EN.md)**  
**📖 [🇧🇷 Leia em Português](README_PT.md)**

---

## 🎯 What is Nexus Engine?

Nexus is an **ultra-high performance C++ trading engine** designed for **institutional-grade backtesting** and **algorithmic trading** applications. Built entirely with **C++20** and optimized for extreme performance using cutting-edge techniques like **LMAX Disruptor pattern**, **lock-free data structures**, **hardware timestamp counters**, and **NUMA optimization**.

### ⚡ Key Highlights

- 🚀 **Ultra-Low Latency** - Sub-microsecond event processing with LMAX Disruptor pattern
- 🔥 **Extreme Performance** - 800K+ signals/sec, 267K+ Monte Carlo sims/sec, 11M+ memory allocs/sec
- 📊 **Advanced Analytics** - Comprehensive risk analysis, performance metrics, and Monte Carlo simulation
- 🎯 **Multi-Strategy Engine** - SMA, MACD, RSI with incremental O(1) technical indicators
- 🧬 **Strategy Optimization** - Grid search and genetic algorithms for parameter optimization
- 🏦 **Institutional Features** - Lock-free order book, real-time risk management, thread affinity
- ⚡ **Hardware Optimized** - TSC timing, SIMD instructions, branch prediction hints, cache warming
- 🛡️ **Enterprise Architecture** - Modular design, comprehensive testing, structured logging

### 🏆 What Makes It Special?

```
✅ Hardware TSC timing for nanosecond precision measurement
✅ LMAX Disruptor for 10-100M+ events/second throughput
✅ Lock-free order book with atomic operations (1M+ orders/sec)
✅ Real-time optimizations (CPU affinity, thread priority, NUMA)
✅ SIMD-optimized Monte Carlo simulation (4x performance boost)
✅ Branch prediction optimization for critical code paths
✅ Comprehensive latency tracking and performance monitoring
✅ Memory pools eliminating 90%+ allocation overhead
✅ Python backend layer with DDD + Clean Architecture
✅ PyQt6 desktop GUI with real-time trading interface
✅ Full observability stack (Prometheus, Loki, Tempo, Grafana)
✅ Real-time market data integration (Finnhub, Alpha Vantage)
```

---

## ⚡ Quick Start

### Option 1: Docker Deployment (Recommended)
```bash
# Clone the repository
git clone https://github.com/thiagodifaria/Nexus-Engine.git
cd Nexus-Engine

# Start all services with Docker Compose
docker-compose up -d

# Access the application
# Frontend: http://localhost:8000
# Backend API: http://localhost:8001
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### Option 2: Local Development Build
```bash
# Clone the repository
git clone https://github.com/thiagodifaria/Nexus-Engine.git
cd Nexus-Engine

# Build C++ engine with CMake (Release for maximum performance)
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=20
make -j$(nproc)

# Run comprehensive tests
ctest --verbose

# Install Python dependencies
cd ../backend/python
pip install -r requirements.txt

# Run Python backend
python -m src.main

# Run PyQt6 frontend
cd ../../frontend/pyqt6
python -m src.main
```

### 🔥 Performance Benchmarks
```bash
# Expected Performance Results:
# Strategy execution: 800K+ signals/sec  
# Monte Carlo simulation: 267K+ sims/sec
# Memory allocation: 11M+ allocs/sec
# Order book operations: 1M+ orders/sec
# Event processing: 10-100M+ events/sec
```

---

## 🔍 Platform Overview

| Component | Technology | Performance | Description |
|-----------|------------|-------------|-------------|
| 🚀 **Core Engine** | LMAX Disruptor + C++20 | 10-100M events/sec | Ultra-low latency event processing system |
| 📈 **Strategy Engine** | Incremental Indicators | 800K+ signals/sec | SMA, MACD, RSI with O(1) update complexity |
| 📊 **Monte Carlo** | SIMD + Multi-threading | 267K+ sims/sec | Risk analysis with hardware optimization |
| ⚙️ **Optimization** | Genetic + Grid Search | Multi-core | Advanced parameter optimization algorithms |
| 🏦 **Order Book** | Lock-Free Architecture | 1M+ orders/sec | Realistic market simulation with atomic ops |
| 💾 **Memory System** | Custom Pools + NUMA | 11M+ allocs/sec | Zero-overhead allocation for critical paths |
| 🐍 **Python Backend** | DDD + Clean Architecture | FastAPI | Business logic, market data, REST API |
| 🖥️ **Desktop Frontend** | PyQt6 + MVVM | Real-time | Professional trading interface with live charts |
| 📊 **Observability** | Prometheus + Loki + Tempo | Full-stack | Three pillars monitoring with Grafana dashboards |
| 📡 **Market Data** | Multi-provider Integration | Real-time | Finnhub, Alpha Vantage, Nasdaq, FRED |

---

## 📚 Documentation

Complete documentation available in the `docs/` directory:

- **[Architecture Guide](docs/ARCHITECTURE.md)** - System design and component interaction
- **[API Reference](docs/API.md)** - Complete REST API documentation
- **[User Guide](docs/GUIDE.md)** - Setup and usage instructions
- **[Observability Guide](docs/OBSERVABILITY.md)** - Monitoring and troubleshooting

---

## 📞 Contact

**Thiago Di Faria** - thiagodifaria@gmail.com

[![GitHub](https://img.shields.io/badge/GitHub-@thiagodifaria-black?style=flat&logo=github)](https://github.com/thiagodifaria)

---

### 🌟 **Star this project if you find it useful!**

**Made with ⚡ for Ultra-High Performance Trading by [Thiago Di Faria](https://github.com/thiagodifaria)**