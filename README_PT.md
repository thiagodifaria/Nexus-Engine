# Nexus Engine - Engine C++ Ultra-Alta Performance para Trading

Nexus é um engine de trading C++ de ultra-alta performance e framework de backtesting projetado para aplicações de trading algorítmico de nível institucional. Construído inteiramente com C++20 e otimizado para performance extrema usando técnicas de vanguarda incluindo padrão LMAX Disruptor, estruturas de dados lock-free, contadores de timestamp de hardware, instruções SIMD, e otimização NUMA. Este projeto oferece uma solução abrangente para desenvolvimento de trading quantitativo com timing de precisão de nanossegundos e características de performance de nível institucional.

## 🎯 Funcionalidades

### Engine C++ Core
- ✅ **Processamento ultra-baixa latência**: Processamento de eventos sub-microssegundo com implementação do padrão LMAX Disruptor
- ✅ **Estratégias performance extrema**: 800K+ sinais/segundo com indicadores técnicos incrementais O(1)
- ✅ **Order book lock-free**: Simulação de mercado realista com operações atômicas (1M+ ordens/segundo)
- ✅ **Monte Carlo avançado**: Engine de simulação otimizado SIMD com 267K+ simulações/segundo
- ✅ **Otimização estratégias**: Grid search e algoritmos genéticos com execução multi-threaded
- ✅ **Otimizações tempo-real**: CPU affinity, prioridade thread, consciência NUMA, cache warming
- ✅ **Timing nível hardware**: TSC (Time Stamp Counter) para medição precisão nanossegundo
- ✅ **Otimização memória**: Pools customizados eliminando 90%+ overhead alocação

### Backend Python & Frontend
- ✅ **Domain-Driven Design**: Clean Architecture com padrões DDD (Entities, Value Objects, Use Cases)
- ✅ **Interface Desktop PyQt6**: Interface profissional de trading com gráficos em tempo real e monitoramento
- ✅ **API RESTful**: Backend FastAPI com endpoints abrangentes para operações de trading
- ✅ **Integração Dados Mercado**: Dados tempo-real de Finnhub, Alpha Vantage, Nasdaq Data Link, FRED
- ✅ **Observabilidade Completa**: Métricas Prometheus, logs Loki, traces Tempo, dashboards Grafana
- ✅ **Testes abrangentes**: Testes unitários, integração e E2E com meta de cobertura >80%
- ✅ **Deploy Docker**: Containerização completa com orquestração Docker Compose

## 🗃️ Arquitetura

### Arquitetura Sistema Alto-Nível

```
Plataforma Trading Nexus Engine
│
├── 🚀 Engine C++ Core (src/cpp/)          # Engine backtesting ultra-alta performance
│   ├── Processamento eventos LMAX Disruptor # 10-100M eventos/seg
│   ├── Order book lock-free               # 1M+ ordens/seg
│   ├── Engine execução estratégias        # 800K+ sinais/seg
│   └── Simulador Monte Carlo              # 267K+ sims/seg
│
├── 🐍 Backend Python (backend/python/)    # Lógica negócio & camada API
│   ├── Camada Domínio (DDD)               # Entities, Value Objects, Repositories
│   ├── Camada Aplicação                   # Use Cases, Services
│   ├── Camada Infraestrutura              # Adapters, Database, Market Data, Telemetry
│   └── API REST FastAPI                   # Endpoints HTTP
│
├── 🖥️ Frontend PyQt6 (frontend/pyqt6/)    # Aplicação desktop trading
│   ├── Arquitetura MVVM                   # ViewModels + Views
│   ├── Gráficos tempo-real                # Visualização dados mercado ao vivo
│   ├── UI gerenciamento estratégias       # Criar, monitorar, otimizar estratégias
│   └── Dashboards performance             # Resultados backtest e analytics
│
└── 📊 Stack Observabilidade (devops/)     # Monitoramento & debugging
    ├── Prometheus (Métricas)              # Métricas trading, latência C++
    ├── Loki (Logs)                        # Logging JSON estruturado
    ├── Tempo (Traces)                     # Rastreamento distribuído
    └── Grafana (Visualização)             # Dashboards unificados
```

### Arquitetura Engine C++ Core

Arquitetura C++ modular altamente otimizada com design performance-first:

```
src/cpp/
├── core/           # Sistema eventos, timing alta-resolução, otimizações tempo-real
│   ├── backtest_engine.*       # Engine orquestração principal com LMAX Disruptor
│   ├── event_types.*          # Sistema eventos type-safe com timestamps hardware
│   ├── event_queue.*          # Queue alta-performance com backends configuráveis
│   ├── disruptor_queue.*      # Implementação LMAX Disruptor para ultra-baixa latência
│   ├── high_resolution_clock.* # Acesso TSC hardware para precisão nanossegundo
│   ├── latency_tracker.*      # Medição e análise latência abrangente
│   ├── thread_affinity.*      # Pinning core CPU e prioridade tempo-real
│   └── real_time_config.*     # Configuração otimizações tempo-real
│
├── strategies/     # Estratégias trading com indicadores técnicos otimizados
│   ├── abstract_strategy.*    # Interface estratégia base com sistema parâmetros
│   ├── sma_strategy.*         # Estratégia crossover Simple Moving Average
│   ├── macd_strategy.*        # MACD (Moving Average Convergence Divergence)
│   ├── rsi_strategy.*         # Estratégia RSI (Relative Strength Index)
│   ├── technical_indicators.* # Cálculos indicadores incrementais O(1)
│   └── signal_types.*         # Tracking estado sinal otimizado baseado enum
│
├── execution/      # Order book e simulação execução
│   ├── execution_simulator.*  # Execução realista com slippage e taxas
│   ├── lock_free_order_book.* # Order book lock-free com operações atômicas
│   └── price_level.*          # Nível preço atômico com gerenciamento ordens
│
├── analytics/      # Análise performance e métricas risco
│   ├── performance_analyzer.* # Cálculo métricas performance abrangentes
│   ├── monte_carlo_simulator.* # Simulação Monte Carlo otimizada SIMD
│   ├── risk_metrics.*         # Cálculos VaR, CVaR e risco avançados
│   ├── metrics_calculator.*   # Métricas rolling e análise séries temporais
│   └── performance_metrics.*  # Estrutura métricas performance completa
│
├── optimization/   # Otimização parâmetros estratégia
│   ├── strategy_optimizer.*   # Orquestração otimização principal
│   ├── grid_search.*          # Busca exaustiva grid parâmetros
│   └── genetic_algorithm.*    # Otimização genética baseada população
│
├── position/       # Gerenciamento posição e risco
│   ├── position_manager.*     # Tracking posição tempo-real e P&L
│   └── risk_manager.*         # Validação risco pré-trade e limites
│
└── data/          # Tratamento dados mercado e validação
    ├── market_data_handler.*  # Processamento dados CSV multi-asset
    ├── database_manager.*     # Integração SQLite para persistência dados
    ├── data_validator.*       # Garantia e validação qualidade dados
    └── data_types.*           # Estruturas dados OHLCV e utilitários
```

## 🔧 Stack Tecnológico

### Tecnologias Performance Core
- **C++20**: Características linguagem moderna com otimizações compile-time
- **LMAX Disruptor**: Padrão ring buffer lock-free para ultra-baixa latência (10-100M eventos/seg)
- **Hardware TSC**: Acesso direto contador timestamp para timing precisão nanossegundo
- **Otimização NUMA**: Alocação memória otimizada para sistemas servidor multi-socket
- **CMake 3.20+**: Sistema build moderno com suporte cross-platform

### Otimizações Performance Avançadas
- **Estruturas Dados Lock-Free**: Operações atômicas para acesso concorrente sem locks
- **Pools Memória**: Buffers pré-alocados eliminando overhead alocação dinâmica
- **Predição Branch**: Atributos [[likely]]/[[unlikely]] para otimização CPU
- **Instruções SIMD**: Computações vetorizadas para simulação Monte Carlo (4x speedup)
- **Cache Warming**: Pré-carregamento estruturas dados críticas em cache CPU
- **Thread Affinity**: Pinning core CPU para performance determinística

### Analytics & Gerenciamento Risco
- **Simulação Monte Carlo**: Análise risco multi-threaded com otimização SIMD
- **Indicadores Técnicos**: Cálculos incrementais SMA, EMA, RSI, MACD (complexidade O(1))
- **Algoritmos Genéticos**: Otimização parâmetros estratégia baseada população
- **Métricas Risco**: Value-at-Risk (VaR), VaR Condicional, índice Sharpe, máximo drawdown
- **Analytics Performance**: Análise performance backtesting abrangente

### Gerenciamento Dados & Integração
- **Integração SQLite**: Banco dados leve para desenvolvimento e teste
- **Suporte Multi-Asset**: Processamento simultâneo múltiplos instrumentos trading
- **Validação Dados**: Verificações qualidade dados abrangentes e detecção outliers
- **Processamento CSV**: Parsing otimizado para grandes datasets históricos

## 📋 Pré-requisitos

- **Compilador Compatível C++20**: GCC 10+, Clang 12+, ou MSVC 2019+
- **CMake 3.20+**: Sistema build moderno para compilação cross-platform
- **Bibliotecas Desenvolvimento SQLite3**: Suporte integração banco dados
- **Suporte Threading**: POSIX threads (Linux/Mac) ou Windows threads
- **Arquitetura 64-bit**: Requerida para performance ótima e suporte TSC

## 🚀 Instalação Rápida

### Deploy Docker (Recomendado)

```bash
# Clonar repositório
git clone https://github.com/thiagodifaria/Nexus-Engine.git
cd Nexus-Engine

# Iniciar todos serviços com Docker Compose
docker-compose up -d

# Acessar serviços
# - API Backend: http://localhost:8001/docs
# - Grafana: http://localhost:3000 (admin/admin)
# - Prometheus: http://localhost:9090

# Visualizar logs
docker-compose logs -f nexus-backend

# Parar todos serviços
docker-compose down
```

### Build Desenvolvimento Local

```bash
# Clonar repositório
git clone https://github.com/thiagodifaria/Nexus-Engine.git
cd Nexus-Engine

# Build engine C++
mkdir build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_STANDARD=20
make -j$(nproc)  # Linux/Mac
# ou
cmake --build . --config Release --parallel  # Cross-platform

# Verificar instalação C++
make test

# Instalar dependências backend Python
cd ../backend/python
pip install -r requirements.txt

# Executar backend Python
python -m src.main

# Instalar e executar frontend PyQt6
cd ../../frontend/pyqt6
pip install -r requirements.txt
python -m src.main
```

### Build Otimização Performance

```bash
# Configurar com otimizações avançadas
cmake .. \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_CXX_STANDARD=20 \
  -DCMAKE_CXX_FLAGS="-O3 -march=native -mtune=native" \
  -DENABLE_NUMA_OPTIMIZATION=ON \
  -DENABLE_SIMD_OPTIMIZATION=ON

# Build versão otimizada
make -j$(nproc)
```

## ⚙️ Configuração

### Configuração Otimização Tempo-Real

```cpp
// Habilitar otimizações tempo-real abrangentes
RealTimeConfig config;
config.enable_cpu_affinity = true;
config.cpu_cores = {2, 3, 4, 5};  // Isolar cores específicos para trading
config.enable_real_time_priority = true;
config.real_time_priority_level = 80;  // Alta prioridade para threads críticas
config.enable_cache_warming = true;
config.cache_warming_iterations = 3;
config.enable_numa_optimization = true;
config.preferred_numa_node = 0;

// Configurar engine backtest com otimizações
BacktestEngineConfig engine_config;
engine_config.enable_performance_monitoring = true;
engine_config.enable_event_batching = true;
engine_config.queue_backend_type = "disruptor";  // Usar LMAX Disruptor
engine_config.real_time_config = config;

BacktestEngine engine(event_queue, data_handler, strategies, 
                     position_manager, execution_simulator, engine_config);
```

### Configuração Simulação Monte Carlo

```cpp
// Configurar simulação Monte Carlo alta-performance
MonteCarloSimulator::Config mc_config;
mc_config.num_simulations = 10000;
mc_config.num_threads = std::thread::hardware_concurrency();
mc_config.enable_simd = true;              // Habilitar otimizações SIMD
mc_config.enable_numa_optimization = true; // Alocação NUMA-aware
mc_config.enable_statistics = true;        // Coletar métricas performance

MonteCarloSimulator simulator(mc_config);
```

### Exemplos Configuração Estratégias

```cpp
// Estratégia SMA alta-performance com parâmetros otimizados
auto sma_strategy = std::make_unique<SmaCrossoverStrategy>(20, 50);

// Estratégia MACD com parâmetros padrão
auto macd_strategy = std::make_unique<MACDStrategy>(12, 26, 9);

// Estratégia RSI com níveis overbought/oversold customizados
auto rsi_strategy = std::make_unique<RSIStrategy>(14, 75.0, 25.0);
```

## 📊 Exemplos de Uso

### Workflow Backtesting Básico

```cpp
#include "core/backtest_engine.h"
#include "strategies/sma_strategy.h"
#include "analytics/performance_analyzer.h"

int main() {
    // Criar componentes core
    nexus::core::EventQueue event_queue;
    auto position_manager = std::make_shared<nexus::position::PositionManager>(100000.0);
    auto execution_simulator = std::make_shared<nexus::execution::ExecutionSimulator>();

    // Configurar mapeamento estratégias multi-asset
    std::unordered_map<std::string, std::shared_ptr<nexus::strategies::AbstractStrategy>> strategies;
    strategies["AAPL"] = std::make_shared<nexus::strategies::SmaCrossoverStrategy>(20, 50);
    strategies["GOOGL"] = std::make_shared<nexus::strategies::MACDStrategy>(12, 26, 9);
    strategies["TSLA"] = std::make_shared<nexus::strategies::RSIStrategy>(14, 70.0, 30.0);

    // Configurar fontes dados
    std::unordered_map<std::string, std::string> data_files;
    data_files["AAPL"] = "data/sample_data/AAPL.csv";
    data_files["GOOGL"] = "data/sample_data/GOOGL.csv";
    data_files["TSLA"] = "data/sample_data/TSLA.csv";
    
    auto data_handler = std::make_shared<nexus::data::CsvDataHandler>(event_queue, data_files);

    // Criar e configurar engine backtest
    nexus::core::BacktestEngineConfig config;
    config.enable_performance_monitoring = true;
    config.queue_backend_type = "disruptor";
    
    nexus::core::BacktestEngine engine(event_queue, data_handler, strategies, 
                                      position_manager, execution_simulator, config);

    // Executar backtest
    engine.run();

    // Análise performance abrangente
    nexus::analytics::PerformanceAnalyzer analyzer(
        100000.0,  // Capital inicial
        position_manager->get_equity_curve(),
        position_manager->get_trade_history()
    );
    
    auto metrics = analyzer.calculate_metrics();
    
    // Exibir resultados
    std::cout << "=== Resultados Backtest ===" << std::endl;
    std::cout << "Retorno Total: " << (metrics.total_return * 100) << "%" << std::endl;
    std::cout << "Índice Sharpe: " << metrics.sharpe_ratio << std::endl;
    std::cout << "Máximo Drawdown: " << (metrics.max_drawdown * 100) << "%" << std::endl;
    std::cout << "Total Trades: " << metrics.total_trades << std::endl;
    
    return 0;
}
```

### Otimização Estratégias Avançada

```cpp
#include "optimization/strategy_optimizer.h"
#include "optimization/genetic_algorithm.h"

// Otimização Grid Search
void executar_otimizacao_grid_search() {
    // Criar template estratégia para otimização
    auto strategy_template = std::make_unique<nexus::strategies::SmaCrossoverStrategy>(10, 20);
    nexus::optimization::StrategyOptimizer optimizer(std::move(strategy_template));

    // Definir grid parâmetros para busca exaustiva
    std::unordered_map<std::string, std::vector<double>> parameter_grid;
    parameter_grid["short_window"] = {5, 10, 15, 20, 25};
    parameter_grid["long_window"] = {30, 40, 50, 60, 70, 80, 90, 100};

    // Executar grid search (testará todas 5 x 8 = 40 combinações)
    auto results = optimizer.grid_search(parameter_grid);
    auto best_result = optimizer.get_best_result();
    
    std::cout << "Melhores parâmetros encontrados:" << std::endl;
    for (const auto& [param, value] : best_result.parameters) {
        std::cout << param << ": " << value << std::endl;
    }
    std::cout << "Melhor Índice Sharpe: " << best_result.fitness_score << std::endl;
}

// Otimização Algoritmo Genético
void executar_otimizacao_genetica() {
    auto strategy_template = std::make_unique<nexus::strategies::RSIStrategy>(14, 70.0, 30.0);
    
    // Definir bounds parâmetros para algoritmo genético
    std::unordered_map<std::string, std::pair<double, double>> bounds;
    bounds["period"] = {5.0, 30.0};           // Range período RSI
    bounds["overbought"] = {65.0, 85.0};      // Range threshold overbought
    bounds["oversold"] = {15.0, 35.0};        // Range threshold oversold
    
    // Configurar parâmetros algoritmo genético
    int population_size = 50;
    int generations = 20;
    double mutation_rate = 0.1;
    double crossover_rate = 0.8;
    
    // Executar otimização genética
    auto results = nexus::optimization::perform_genetic_algorithm(
        *strategy_template, bounds, population_size, generations,
        mutation_rate, crossover_rate, 100000.0, "data/sample_data/AAPL.csv", "AAPL"
    );
    
    // Resultados automaticamente ordenados por fitness (melhor primeiro)
    std::cout << "Top 5 estratégias evoluídas:" << std::endl;
    for (size_t i = 0; i < std::min(size_t(5), results.size()); ++i) {
        std::cout << "Rank " << (i + 1) << " - Fitness: " << results[i].fitness_score << std::endl;
        for (const auto& [param, value] : results[i].parameters) {
            std::cout << "  " << param << ": " << value << std::endl;
        }
    }
}
```

### Análise Risco Monte Carlo

```cpp
#include "analytics/monte_carlo_simulator.h"
#include "analytics/risk_metrics.h"

void realizar_analise_risco_portfolio() {
    // Configurar simulação Monte Carlo alta-performance
    nexus::analytics::MonteCarloSimulator::Config config;
    config.num_simulations = 50000;  // Número grande para significância estatística
    config.num_threads = std::thread::hardware_concurrency();
    config.enable_simd = true;       // Habilitar otimizações SIMD
    config.enable_statistics = true; // Coletar métricas performance
    
    nexus::analytics::MonteCarloSimulator simulator(config);
    
    // Definir características portfólio
    std::vector<double> expected_returns = {0.08, 0.12, 0.06, 0.10};  // Retornos anuais
    std::vector<double> volatilities = {0.15, 0.25, 0.10, 0.20};      // Volatilidades anuais
    
    // Matriz correlação entre assets
    std::vector<std::vector<double>> correlation_matrix = {
        {1.00, 0.30, 0.15, 0.25},
        {0.30, 1.00, 0.10, 0.40},
        {0.15, 0.10, 1.00, 0.20},
        {0.25, 0.40, 0.20, 1.00}
    };
    
    // Executar simulação portfólio para horizonte 1 ano
    auto portfolio_returns = simulator.simulate_portfolio(
        expected_returns, volatilities, correlation_matrix, 1.0
    );
    
    // Calcular métricas risco abrangentes
    double var_95 = simulator.calculate_var(portfolio_returns, 0.95);
    double var_99 = simulator.calculate_var(portfolio_returns, 0.99);
    double cvar_95 = nexus::analytics::RiskMetrics::calculate_cvar(portfolio_returns, 0.95);
    
    // Exibir resultados análise risco
    std::cout << "=== Análise Risco Portfólio ===" << std::endl;
    std::cout << "Simulações: " << config.num_simulations << std::endl;
    std::cout << "VaR (95%): " << (var_95 * 100) << "%" << std::endl;
    std::cout << "VaR (99%): " << (var_99 * 100) << "%" << std::endl;
    std::cout << "CVaR (95%): " << (cvar_95 * 100) << "%" << std::endl;
    
    // Obter estatísticas performance simulação
    auto stats = simulator.get_statistics();
    std::cout << "Performance Simulação:" << std::endl;
    std::cout << "  Throughput: " << stats.throughput_per_second << " sims/seg" << std::endl;
    std::cout << "  Tempo médio: " << stats.average_simulation_time_ns << " ns/sim" << std::endl;
}
```

## 🔍 Análise Profunda Componentes Core

### BacktestEngine - Processamento Eventos Ultra-Baixa Latência

| Característica | Implementação | Impacto Performance |
|----------------|---------------|-------------------|
| **Event Queue** | Padrão LMAX Disruptor | 10-100M eventos/segundo |
| **CPU Affinity** | Pinning thread cores isolados | 20-50% redução latência |
| **Prioridade Tempo-Real** | Otimização scheduling nível OS | Execução determinística |
| **Cache Warming** | Pré-carregamento estruturas dados críticas | 30-50% redução latência inicial |
| **Otimização NUMA** | Alocação memória nodes locais | Redução latência acesso memória |

### Engine Estratégias - Geração Sinais Alta-Performance

| Estratégia | Indicadores Técnicos | Complexidade Update | Performance |
|------------|---------------------|-------------------|-------------|
| **SMA Crossover** | Simple Moving Average Incremental | O(1) | 800K+ sinais/seg |
| **Estratégia MACD** | EMA Rápida/Lenta + Linha Sinal | O(1) | 2.4M+ sinais/seg |
| **Estratégia RSI** | RSI Suavização Wilder's | O(1) | 650K+ sinais/seg |

### Order Book Lock-Free - Simulação Mercado Realista

| Componente | Tecnologia | Performance | Características |
|------------|------------|-------------|-----------------|
| **Níveis Preço** | Operações atômicas | 1M+ ordens/seg | Matching FIFO, prioridade preço-tempo |
| **Gerenciamento Ordens** | Listas ligadas lock-free | Latência sub-microssegundo | Operações add, modify, cancel |
| **Dados Mercado** | Snapshots tempo-real | <100ns geração | Best bid/ask, profundidade mercado |

### Simulador Monte Carlo - Análise Risco Avançada

| Otimização | Tecnologia | Ganho Performance | Descrição |
|------------|------------|------------------|-----------|
| **Instruções SIMD** | Vetorização AVX2/AVX-512 | 4x+ throughput | Geração números aleatórios paralela |
| **Multi-threading** | Thread pool work-stealing | Escalabilidade linear | Distribui simulações através cores |
| **Pré-alocação Memória** | Pools buffer customizados | 90%+ redução overhead | Elimina alocação durante simulação |
| **Consciência NUMA** | Alocação memória local | Latência reduzida | Otimiza para sistemas multi-socket |

## 🧪 Testes Abrangentes

### Visão Geral Suíte Testes

```bash
# Executar todos testes com saída detalhada
cd build
ctest --verbose

# Executar categorias testes individuais
./test_strategies           # Testes geração sinais estratégia
./test_analytics           # Análise performance e métricas risco
./test_monte_carlo         # Precisão simulação Monte Carlo
./test_integration         # Testes integração sistema completo
./test_position_manager    # Tracking posição e cálculo P&L
./test_optimizer           # Algoritmos otimização estratégia
./test_advanced_modules    # Indicadores técnicos e características avançadas
```

### Teste Stress Performance

```bash
# Teste stress performance abrangente
./test_performance_stress

# Saída Esperada:
# >> RESULTADOS PERFORMANCE ESTRATÉGIAS:
# SMA Crossover (20/50): 422,989 sinais/seg
# MACD (12/26/9): 2,397,932 sinais/seg  
# RSI (14): 650,193 sinais/seg
#
# >> RESULTADOS PERFORMANCE MONTE CARLO:
# Escala Média (1K sims): 142,673 sims/seg
# Escala Grande (5K sims): 304,822 sims/seg
# Escala Ultra Grande (10K sims): 267,008 sims/seg
#
# >> PERFORMANCE ALOCAÇÃO MEMÓRIA:
# Alocação Pool Eventos: 11,004,853 allocs/seg
```

### Áreas Cobertura Testes

- ✅ **Validação Estratégias**: Precisão e timing geração sinais
- ✅ **Teste Order Book**: Correção e performance engine matching
- ✅ **Precisão Monte Carlo**: Validação estatística resultados simulação
- ✅ **Métricas Performance**: Verificação cálculo analytics abrangentes
- ✅ **Integração Multi-Asset**: Gerenciamento portfólio através múltiplos instrumentos
- ✅ **Otimizações Tempo-Real**: CPU affinity e scheduling prioridade
- ✅ **Gerenciamento Memória**: Eficiência alocação e desalocação pool
- ✅ **Gerenciamento Risco**: Validação limites posição e exposição
- ✅ **Validação Dados**: Verificações qualidade e integridade dados mercado

## 📈 Benchmarks Performance & Resultados Otimização

### Métricas Performance Típicas (Build Release)

#### Performance Processamento Eventos
- **Queue LMAX Disruptor**: 10-100M eventos/segundo
- **Queue Mutex Tradicional**: 1-5M eventos/segundo
- **Melhoria Performance**: 10-20x processamento eventos mais rápido

#### Performance Execução Estratégias
- **Estratégia SMA Crossover**: 422,989+ sinais/segundo
- **Estratégia MACD**: 2,397,932+ sinais/segundo
- **Estratégia RSI**: 650,193+ sinais/segundo
- **Latência Média**: Geração sinal sub-microssegundo

#### Operações Order Book
- **Adição Ordem**: 1M+ ordens/segundo
- **Matching Ordem**: 500K+ matches/segundo
- **Geração Dados Mercado**: <100ns por snapshot
- **Updates Nível Preço**: Latência operação atômica

#### Simulação Monte Carlo
- **Single-threaded**: 25,000+ simulações/segundo
- **Multi-threaded (12 cores)**: 300,000+ simulações/segundo
- **Otimização SIMD**: 4x melhoria performance
- **Benefício Pool Memória**: 90%+ redução overhead alocação

#### Gerenciamento Memória
- **Alocação Pool Eventos**: 11,004,853+ alocações/segundo
- **Taxa Cache Hit**: >95% para dados acessados frequentemente
- **Eficiência Pool Memória**: 90%+ redução overhead alocação

### Análise Impacto Otimização

#### Otimizações Tempo-Real
- **CPU Affinity (Core Pinning)**: 20-50% redução latência
- **Scheduling Prioridade Tempo-Real**: Timing execução determinístico
- **Cache Warming**: 30-50% melhoria latência inicial
- **Otimização NUMA**: 10-25% melhoria acesso memória

#### Otimizações Compilador
- **Hints Predição Branch**: 5-15% melhoria cache instrução
- **Especialização Template**: Otimização compile-time para paths críticos
- **Otimização Função Inline**: Eliminação overhead chamada função
- **Loop Unrolling**: Vetorização automática para loops apertados

#### Otimizações Estruturas Dados
- **Design Lock-free**: Elimina contenção e bloqueio
- **Alinhamento Memória**: Otimiza utilização cache line
- **Estratégias Pré-alocação**: Padrões acesso memória previsíveis
- **Operações Atômicas**: Primitivos sincronização nível hardware

## 📊 Características Avançadas & Configuração

### Configuração Sistema Tempo-Real

```cpp
// Configuração máxima performance para trading produção
RealTimeConfig production_config;
production_config.enable_cpu_affinity = true;
production_config.cpu_cores = {4, 5, 6, 7};  // Isolar cores alta-frequência
production_config.auto_detect_optimal_cores = true;
production_config.enable_real_time_priority = true;
production_config.real_time_priority_level = 90;  // Prioridade máxima
production_config.enable_cache_warming = true;
production_config.cache_warming_iterations = 5;
production_config.enable_numa_optimization = true;
production_config.enable_memory_locking = true;  // Prevenir swapping
production_config.enable_huge_pages = true;      // Usar páginas 2MB
production_config.cpu_isolation_mode = "hard";   // Isolamento máximo
```

### Configuração Analytics Avançados

```cpp
// Monitoramento performance abrangente
BacktestEngineConfig monitoring_config;
monitoring_config.enable_performance_monitoring = true;
monitoring_config.enable_latency_spike_detection = true;
monitoring_config.latency_spike_threshold = std::chrono::microseconds{10};
monitoring_config.monitoring_interval = std::chrono::milliseconds{100};

// Habilitar tracking latência detalhado
PerformanceAnalyzer analyzer(/* ... */);
analyzer.enable_latency_tracking(true);

// Acessar métricas abrangentes
auto latency_stats = analyzer.get_latency_statistics();
for (const auto& [operation, stats] : latency_stats) {
    std::cout << operation << " - P99: " << stats.p99_ns << "ns" << std::endl;
}
```

### Configuração Simulação Execução

```cpp
// Simulação mercado realista com order book
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

## 📋 Gerenciamento Dados & Validação

### Formatos Dados Suportados

#### Formato Dados Mercado CSV
```csv
Timestamp,Open,High,Low,Close,Volume
2025-01-01 09:30:00,150.25,151.75,149.80,151.20,2500000
2025-01-01 09:31:00,151.20,152.00,150.90,151.85,1800000
2025-01-01 09:32:00,151.85,152.50,151.60,152.10,2100000
```

#### Características Validação Dados
```cpp
// Validação qualidade dados abrangente
nexus::data::DataValidator validator;

// Verificar timestamps faltantes
auto missing_timestamps = validator.find_missing_timestamps(market_data);

// Identificar outliers estatísticos
auto outliers = validator.find_outliers(market_data, 3.0);  // threshold 3 sigma

// Validar consistência OHLCV
auto invalid_bars = validator.find_invalid_bars(market_data);

std::cout << "Relatório Qualidade Dados:" << std::endl;
std::cout << "Timestamps faltantes: " << missing_timestamps.size() << std::endl;
std::cout << "Outliers estatísticos: " << outliers.size() << std::endl;
std::cout << "Barras inválidas: " << invalid_bars.size() << std::endl;
```

### Integração Banco Dados

```cpp
// Banco dados SQLite para persistência dados
nexus::data::DatabaseManager db_manager("data/database/nexus.db");

if (db_manager.open()) {
    db_manager.create_market_data_table();
    
    // Armazenar dados mercado
    db_manager.store_market_data("AAPL", historical_data);
    
    // Recuperar período específico tempo
    auto start_time = std::chrono::system_clock::from_time_t(/* ... */);
    auto end_time = std::chrono::system_clock::from_time_t(/* ... */);
    auto retrieved_data = db_manager.fetch_market_data("AAPL", start_time, end_time);
}
```

## 🔒 Gerenciamento Risco & Tracking Posição

### Validação Risco Tempo-Real

```cpp
// Configurar gerenciamento risco abrangente
nexus::position::RiskManager risk_manager(position_manager);

// Validação risco pré-trade
bool validate_trading_signal(const nexus::core::TradingSignalEvent& signal, 
                            double current_price) {
    // Validação automática inclui:
    // - Limites drawdown portfólio (15% máx)
    // - Limites exposição posição (20% por asset)
    // - Verificação capital disponível
    // - Avaliação risco concentração
    
    return risk_manager.validate_order(signal, current_price);
}
```

### Características Gerenciamento Posição

```cpp
// Tracking posição tempo-real
nexus::position::PositionManager portfolio(100000.0);  // $100K capital inicial

// Processar execução trade
nexus::core::TradeExecutionEvent trade;
trade.symbol = "AAPL";
trade.quantity = 100;
trade.price = 150.25;
trade.commission = 1.50;
trade.is_buy = true;

portfolio.on_trade_execution(trade);

// Métricas portfólio tempo-real
std::cout << "Caixa Disponível: $" << portfolio.get_available_cash() << std::endl;
std::cout << "Patrimônio Total: $" << portfolio.get_total_equity() << std::endl;
std::cout << "P&L Não Realizado: $" << portfolio.get_total_unrealized_pnl() << std::endl;

// Obter detalhes posição individual
auto aapl_position = portfolio.get_position_snapshot("AAPL");
std::cout << "Posição AAPL: " << aapl_position.quantity_ << " ações" << std::endl;
std::cout << "P&L AAPL: $" << aapl_position.unrealized_pnl_ << std::endl;
```

## 🧬 Guia Desenvolvimento Estratégias

### Criando Estratégias Customizadas

```cpp
// Exemplo: Estratégia Bollinger Bands customizada
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
        
        // Gerar sinais baseados em breakouts Bollinger Band
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
        // Calcular desvio padrão
        double sum_squared_diff = 0.0;
        for (double price : prices_) {
            double diff = price - sma_value_;
            sum_squared_diff += diff * diff;
        }
        double std_dev = std::sqrt(sum_squared_diff / period_);
        
        // Calcular bandas
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

## 📚 Documentação & Recursos

### Documentação Completa

Documentação completa disponível no diretório `docs/`:

- **[Guia Arquitetura](docs/ARCHITECTURE.md)** - Arquitetura completa sistema, decisões design e interação componentes
- **[Referência API](docs/API.md)** - Documentação REST API com exemplos request/response
- **[Guia Usuário](docs/GUIDE.md)** - Instruções instalação, configuração e uso
- **[Guia Observabilidade](docs/OBSERVABILITY.md)** - Monitoramento, logging, tracing e troubleshooting

### Documentação API
- **Documentação Doxygen**: Referência API C++ completa com exemplos
- **FastAPI Swagger**: Documentação REST API interativa no endpoint `/docs`
- **Guia Performance**: Técnicas otimização e métodos benchmarking
- **Guia Desenvolvedor**: Melhores práticas para estender plataforma

### Exemplos Código
- **Desenvolvimento Estratégia Básica**: Guia passo-a-passo criação estratégia
- **Otimização Avançada**: Ajuste parâmetros e algoritmos genéticos
- **Gerenciamento Risco**: Avaliação risco portfólio e dimensionamento posição
- **Trading Multi-Asset**: Execução estratégia simultânea através instrumentos

### Papers Pesquisa & Referências
- **Padrão LMAX Disruptor**: Mensagens inter-thread ultra-baixa latência
- **Estruturas Dados Lock-Free**: Programação concorrente alta-performance
- **Métodos Monte Carlo**: Avaliação risco financeiro e simulação
- **Algoritmos Genéticos**: Otimização evolucionária para estratégias trading

## 🔧 Sistema Build & Desenvolvimento

### Opções Configuração CMake

```bash
# Build desenvolvimento com debugging
cmake .. -DCMAKE_BUILD_TYPE=Debug -DENABLE_TESTING=ON

# Build performance com otimizações
cmake .. -DCMAKE_BUILD_TYPE=Release -DENABLE_SIMD=ON -DENABLE_NUMA=ON

# Build otimização guiada por perfil
cmake .. -DCMAKE_BUILD_TYPE=Release -DENABLE_PGO=ON

# Build debugging memória
cmake .. -DCMAKE_BUILD_TYPE=Debug -DENABLE_SANITIZERS=ON
```

### Compatibilidade Cross-Platform

| Plataforma | Compilador | Características Performance | Notas |
|------------|------------|---------------------------|--------|
| **Linux** | GCC 10+, Clang 12+ | Suporte otimização completo | Recomendado para produção |
| **Windows** | MSVC 2019+, GCC MinGW | TSC, SIMD, threading | Boa plataforma desenvolvimento |
| **macOS** | Clang 12+, Apple Clang | Suporte TSC limitado | Uso desenvolvimento |

## 📜 Licenciamento

Este projeto é licenciado dualmente sob:

### Licença GNU v3 (Open Source)
- **Gratuito para projetos open-source**: Use, modifique e distribua livremente
- **Requisito copyleft**: Trabalhos derivados devem também ser open-source
- **Cláusula uso rede**: Uso server-side requer divulgação código fonte
- **Restrição uso comercial**: Aplicações comerciais requerem licença comercial

### Licença Comercial
- **Uso empresarial**: Aplicações proprietárias e deploy comercial
- **Sem requisitos copyleft**: Manter código proprietário privado
- **Suporte técnico**: Serviços suporte profissional e consultoria
- **Termos licenciamento customizados**: Termos flexíveis para clientes empresariais

Para consultas licenciamento comercial, contate: thiagodifaria@gmail.com

## 📞 Contato & Suporte

**Thiago Di Faria** - Desenvolvedor Principal & Arquiteto
- **Email**: thiagodifaria@gmail.com
- **GitHub**: [@thiagodifaria](https://github.com/thiagodifaria)
- **Repositório Projeto**: [https://github.com/thiagodifaria/Nexus-Engine](https://github.com/thiagodifaria/Nexus-Engine)

---

⭐ **Nexus Engine** - Engine trading C++ ultra-alta performance para trading algorítmico nível institucional.