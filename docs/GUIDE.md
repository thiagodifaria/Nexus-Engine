# 📖 Nexus Engine - User Guide

## 🎯 Visão Geral

Guia completo para ajudar você a usar o Nexus Engine, desde a instalação até o deployment em produção. Decidi estruturar em três seções principais:

1. **Getting Started**: Setup inicial e primeiro backtest
2. **Creating Strategies**: Como criar estratégias customizadas
3. **Deployment Guide**: Como deployar em produção

## 🚀 Getting Started

### Pre requisites

Para rodar em Linux, macOS e Windows. Você vai precisar de:

**Softwares necessários:**
- Python 3.11+ (https://www.python.org/downloads/)
- C++ compiler (GCC 11+, Clang 14+, ou MSVC 2022)
- CMake 3.20+ (https://cmake.org/download/)
- PostgreSQL 15+ (https://www.postgresql.org/download/)
- Git (https://git-scm.com/downloads/)

**Opcional (para observability):**
- Docker & Docker Compose (https://www.docker.com/)

### Installation

#### 1. Clone o repositório

```bash
git clone https://github.com/yourusername/nexus-engine.git
cd nexus-engine
```

#### 2. Setup Python environment

Scripts de setup para facilitar a instalação.

**Linux/macOS:**

```bash
# Criar virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Instalar o package em modo editable
pip install -e .
```

**Windows:**

```bash
# Criar virtual environment
python -m venv venv
venv\Scripts\activate

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Instalar package
pip install -e .
```

#### 3. Build C++ engine

CMake build system para compilar o C++ engine e bindings.

**Linux/macOS:**

```bash
# Criar build directory
mkdir build && cd build

# Configurar com CMake
cmake .. -DCMAKE_BUILD_TYPE=Release

# Compilar (usar -j para paralelização)
make -j$(nproc)

# Instalar bindings Python
make install

# Voltar ao root
cd ..
```

**Windows:**

```bash
# Criar build directory
mkdir build
cd build

# Configurar com CMake (Visual Studio)
cmake .. -G "Visual Studio 17 2022" -A x64

# Compilar
cmake --build . --config Release

# Instalar bindings
cmake --install .

# Voltar ao root
cd ..
```

#### 4. Setup database

Migrations para criar schema do banco.

```bash
# Criar database PostgreSQL
createdb nexus_engine

# Configurar connection string no .env
echo "DATABASE_URL=postgresql://user:password@localhost:5432/nexus_engine" > .env

# Executar migrations
alembic upgrade head
```

#### 5. Configure API keys

Você vai precisar de API keys para market data providers.

**Criar arquivo .env:**

```bash
# Market Data APIs
ALPHA_VANTAGE_API_KEY=your_key_here
FINNHUB_API_KEY=your_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/nexus_engine

# Redis (opcional, para cache)
REDIS_URL=redis://localhost:6379

# Observability (opcional)
PROMETHEUS_PORT=8000
GRAFANA_URL=http://localhost:3000
```

**Obter API keys grátis:**

- Alpha Vantage: https://www.alphavantage.co/support/#api-key
- Finnhub: https://finnhub.io/register

#### 6. Verify installation

Script de verificação para testar se tudo está funcionando.

```bash
# Testar C++ bindings
python -c "import nexus_bindings; print('C++ bindings OK')"

# Testar database connection
python -c "from backend.python.src.infrastructure.database.session import engine; engine.connect(); print('Database OK')"

# Executar testes
pytest scripts/tests/unit -v
```

### Your First Backtest

Um exemplo completo para você executar seu primeiro backtest em minutos!

#### Método 1: Via Python API

```python
# first_backtest.py
from backend.python.src.application.use_cases.run_backtest import RunBacktestUseCase
from backend.python.src.application.services.strategy_service import StrategyService
from backend.python.src.application.services.market_data_service import MarketDataService
from backend.python.src.domain.entities.strategy import StrategyType
from backend.python.src.domain.value_objects import Symbol, TimeRange, StrategyParameters
from datetime import datetime

# Setup services (normalmente via DI container)
strategy_service = StrategyService(...)
market_data_service = MarketDataService(...)
run_backtest_uc = RunBacktestUseCase(...)

# 1. Criar estratégia SMA 50/200
strategy = strategy_service.create_strategy(
    name="Golden Cross Strategy",
    strategy_type=StrategyType.SMA_CROSSOVER,
    parameters=StrategyParameters(params={
        "fast_period": 50,
        "slow_period": 200
    })
)

print(f"✅ Strategy created: {strategy.name} (ID: {strategy.id})")

# 2. Executar backtest em AAPL (2024)
result = run_backtest_uc.execute(
    strategy_id=strategy.id,
    symbol=Symbol("AAPL"),
    time_range=TimeRange(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31)
    ),
    initial_capital=100000.0
)

# 3. Visualizar resultados
print(f"\n📊 Backtest Results:")
print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Total Trades: {result.total_trades}")
print(f"Win Rate: {result.win_rate:.2%}")
print(f"Profit Factor: {result.profit_factor:.2f}")

# 4. Plot equity curve
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 6))
plt.plot(result.equity_curve)
plt.title(f"{strategy.name} - Equity Curve")
plt.xlabel("Days")
plt.ylabel("Equity ($)")
plt.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig("equity_curve.png")
print(f"\n📈 Equity curve saved to equity_curve.png")
```

**Executar:**

```bash
python first_backtest.py
```

#### Método 2: Via C++ API diretamente

```python
# first_backtest_cpp.py
import nexus_bindings as nexus
import pandas as pd
from datetime import datetime

# 1. Carregar dados históricos (você pode usar yfinance para isso)
import yfinance as yf

print("📥 Downloading AAPL data...")
df = yf.download('AAPL', start='2024-01-01', end='2024-12-31')
prices = df['Close'].tolist()
timestamps = df.index.tolist()

print(f"✅ Downloaded {len(prices)} days of data")

# 2. Criar estratégia
strategy = nexus.SmaStrategy(fast_period=50, slow_period=200)
print(f"✅ Strategy created: SMA(50, 200)")

# 3. Executar backtest
engine = nexus.BacktestEngine()
print(f"⚙️  Running backtest...")

result = engine.run(
    strategy=strategy,
    prices=prices,
    timestamps=timestamps,
    initial_capital=100000.0
)

# 4. Resultados
print(f"\n📊 Backtest Results:")
print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Sortino Ratio: {result.sortino_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Calmar Ratio: {result.calmar_ratio:.2f}")
print(f"\nTotal Trades: {result.total_trades}")
print(f"Winning Trades: {result.winning_trades} ({result.win_rate:.1%})")
print(f"Losing Trades: {result.losing_trades}")
print(f"Avg Win: ${result.avg_win:.2f}")
print(f"Avg Loss: ${result.avg_loss:.2f}")
print(f"Profit Factor: {result.profit_factor:.2f}")

# 5. Plot
import matplotlib.pyplot as plt

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))

# Equity curve
ax1.plot(result.equity_curve)
ax1.set_title('Equity Curve')
ax1.set_ylabel('Equity ($)')
ax1.grid(True, alpha=0.3)

# Drawdown
equity = result.equity_curve
running_max = [equity[0]]
for e in equity[1:]:
    running_max.append(max(running_max[-1], e))

drawdown = [(e - m) / m for e, m in zip(equity, running_max)]

ax2.fill_between(range(len(drawdown)), drawdown, 0, alpha=0.3, color='red')
ax2.set_title('Drawdown')
ax2.set_ylabel('Drawdown (%)')
ax2.set_xlabel('Days')
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('backtest_results.png')
print(f"\n📈 Results saved to backtest_results.png")
```

**Executar:**

```bash
python first_backtest_cpp.py
```

#### Método 3: Via Desktop UI

Interface gráfica PyQt6 para uso sem programação.

**Iniciar aplicação:**

```bash
python frontend/src/main.py
```

**Passos na UI:**

1. **Tab "Strategy Editor"**
   - Clicar "New Strategy"
   - Name: "Golden Cross Strategy"
   - Type: "SMA Crossover"
   - Fast Period: 50
   - Slow Period: 200
   - Clicar "Save"

2. **Tab "Backtest"**
   - Selecionar estratégia criada
   - Symbol: AAPL
   - Start Date: 2024-01-01
   - End Date: 2024-12-31
   - Initial Capital: $100,000
   - Clicar "Run Backtest"

3. **Tab "Results"**
   - Visualizar métricas
   - Ver equity curve
   - Analisar trades
   - Exportar relatório

### Common Issues

Soluções para os problemas mais comuns:

#### ImportError: No module named 'nexus_bindings'

**Causa:** C++ bindings não foram compilados/instalados.

**Solução:**

```bash
# Recompilar bindings
cd build
cmake --build . --config Release
cmake --install .
```

#### Database connection error

**Causa:** PostgreSQL não está rodando ou credenciais incorretas.

**Solução:**

```bash
# Verificar se PostgreSQL está rodando
pg_isready

# Se não estiver, iniciar
# Linux/macOS:
sudo systemctl start postgresql
# ou
brew services start postgresql

# Windows:
net start postgresql-x64-15

# Verificar credenciais no .env
cat .env | grep DATABASE_URL
```

#### API rate limit exceeded

**Causa:** Muitas chamadas para Alpha Vantage (limite de 5 chamadas/minuto grátis).

**Solução:**

```python
# Usar cache para evitar rechamadas
market_data_service = MarketDataService(
    adapter=alpha_vantage_adapter,
    cache_service=cache_service,  # Redis ou in-memory cache
    cache_ttl=3600  # 1 hora
)
```

Ou usar yfinance (sem rate limit):

```python
import yfinance as yf
df = yf.download('AAPL', start='2024-01-01', end='2024-12-31')
```

## 💡 Creating Strategies

### Strategy Development Workflow

Três formas de criar estratégias:

1. **C++ Strategy** (máxima performance)
2. **Python Strategy** (máxima flexibilidade)
3. **UI Strategy** (sem código)

### Creating C++ Strategy

Template para facilitar criação de novas estratégias C++.

#### 1. Create strategy header

```cpp
// src/cpp/strategies/my_strategy.h
#ifndef MY_STRATEGY_H
#define MY_STRATEGY_H

#include "abstract_strategy.h"
#include <vector>

namespace nexus {

class MyStrategy : public AbstractStrategy {
public:
    MyStrategy(double param1, double param2);
    ~MyStrategy() override = default;

    SignalType on_data(const MarketDataPoint& data) override;

    // Getters para indicadores (opcional)
    double get_indicator1() const { return indicator1_; }
    double get_indicator2() const { return indicator2_; }

protected:
    void update_indicators(const MarketDataPoint& data) override;
    SignalType generate_signal(const MarketDataPoint& data) override;

private:
    // Parâmetros
    double param1_;
    double param2_;

    // Estado interno
    std::vector<double> price_history_;
    double indicator1_{0.0};
    double indicator2_{0.0};

    // Helpers
    void calculate_indicator1();
    void calculate_indicator2();
};

} // namespace nexus

#endif // MY_STRATEGY_H
```

#### 2. Implement strategy

```cpp
// src/cpp/strategies/my_strategy.cpp
#include "my_strategy.h"
#include <algorithm>
#include <numeric>

namespace nexus {

MyStrategy::MyStrategy(double param1, double param2)
    : param1_(param1), param2_(param2) {
    // Validar parâmetros
    if (param1 <= 0 || param2 <= 0) {
        throw std::invalid_argument("Parameters must be positive");
    }
}

void MyStrategy::update_indicators(const MarketDataPoint& data) {
    // Adicionar preço ao histórico
    price_history_.push_back(data.close);

    // Limitar tamanho do histórico (para economizar memória)
    const size_t max_history = std::max(param1_, param2_) * 2;
    if (price_history_.size() > max_history) {
        price_history_.erase(price_history_.begin());
    }

    // Calcular indicadores
    calculate_indicator1();
    calculate_indicator2();
}

SignalType MyStrategy::generate_signal(const MarketDataPoint& data) {
    // Aguardar dados suficientes
    if (price_history_.size() < std::max(param1_, param2_)) {
        return SignalType::HOLD;
    }

    // Lógica de sinal
    if (indicator1_ > indicator2_) {
        return SignalType::BUY;
    } else if (indicator1_ < indicator2_) {
        return SignalType::SELL;
    }

    return SignalType::HOLD;
}

void MyStrategy::calculate_indicator1() {
    if (price_history_.size() < param1_) return;

    // Exemplo: Média móvel simples
    auto start = price_history_.end() - static_cast<int>(param1_);
    auto end = price_history_.end();

    indicator1_ = std::accumulate(start, end, 0.0) / param1_;
}

void MyStrategy::calculate_indicator2() {
    if (price_history_.size() < param2_) return;

    auto start = price_history_.end() - static_cast<int>(param2_);
    auto end = price_history_.end();

    indicator2_ = std::accumulate(start, end, 0.0) / param2_;
}

} // namespace nexus
```

#### 3. Add PyBind11 bindings

```cpp
// src/cpp/bindings/python_bindings.cpp
#include <pybind11/pybind11.h>
#include "strategies/my_strategy.h"

PYBIND11_MODULE(nexus_bindings, m) {
    // ... bindings existentes ...

    // Adicionar MyStrategy
    py::class_<MyStrategy, AbstractStrategy>(m, "MyStrategy")
        .def(py::init<double, double>(),
             py::arg("param1"),
             py::arg("param2"))
        .def("on_data", &MyStrategy::on_data)
        .def("get_indicator1", &MyStrategy::get_indicator1)
        .def("get_indicator2", &MyStrategy::get_indicator2);
}
```

#### 4. Recompile and test

```bash
# Recompilar
cd build
cmake --build . --config Release
cmake --install .

# Testar em Python
python
>>> import nexus_bindings as nexus
>>> strategy = nexus.MyStrategy(param1=10.0, param2=20.0)
>>> signal = strategy.on_data(100.0)
>>> print(signal)
```

#### 5. Create unit tests

```cpp
// tests/cpp/test_my_strategy.cpp
#include <gtest/gtest.h>
#include "strategies/my_strategy.h"

TEST(MyStrategyTest, ValidatesParameters) {
    // Deve lançar exceção com parâmetros inválidos
    EXPECT_THROW(
        nexus::MyStrategy(-1.0, 20.0),
        std::invalid_argument
    );
}

TEST(MyStrategyTest, GeneratesSignals) {
    nexus::MyStrategy strategy(10.0, 20.0);

    // Alimentar com dados
    std::vector<double> prices = {100, 101, 102, ..., 110};

    for (double price : prices) {
        auto signal = strategy.on_data(price);
        // Assert signal logic
    }

    // Verificar indicadores
    EXPECT_GT(strategy.get_indicator1(), 0.0);
    EXPECT_GT(strategy.get_indicator2(), 0.0);
}
```

### Creating Python Strategy

Também suporte para estratégias em Python puro (menos performance, mais flexibilidade).

```python
# backend/python/src/domain/strategies/my_python_strategy.py
from typing import List, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np

from backend.python.src.domain.entities.signal import Signal, SignalType
from backend.python.src.domain.strategies.base import BaseStrategy

@dataclass
class MyPythonStrategyParams:
    """Parâmetros da estratégia"""
    param1: float
    param2: float

    def validate(self):
        if self.param1 <= 0 or self.param2 <= 0:
            raise ValueError("Parameters must be positive")

class MyPythonStrategy(BaseStrategy):
    """
    Estratégia Python usando pandas para análise
    """

    def __init__(self, params: MyPythonStrategyParams):
        super().__init__()
        params.validate()
        self.params = params
        self.price_history = []

    def on_data(self, price: float, timestamp: pd.Timestamp) -> Signal:
        """
        Processa novo dado e gera sinal

        Args:
            price: Preço atual
            timestamp: Timestamp

        Returns:
            Signal (BUY/SELL/HOLD)
        """
        # Adicionar ao histórico
        self.price_history.append(price)

        # Aguardar dados suficientes
        min_required = int(max(self.params.param1, self.params.param2))
        if len(self.price_history) < min_required:
            return Signal(SignalType.HOLD, timestamp)

        # Calcular indicadores usando pandas
        df = pd.DataFrame({'price': self.price_history})
        indicator1 = df['price'].rolling(int(self.params.param1)).mean().iloc[-1]
        indicator2 = df['price'].rolling(int(self.params.param2)).mean().iloc[-1]

        # Gerar sinal
        if indicator1 > indicator2:
            return Signal(SignalType.BUY, timestamp, confidence=0.8)
        elif indicator1 < indicator2:
            return Signal(SignalType.SELL, timestamp, confidence=0.8)

        return Signal(SignalType.HOLD, timestamp)

    def backtest(self, prices: pd.Series) -> pd.DataFrame:
        """
        Executa backtest vectorizado (mais rápido para Python)

        Args:
            prices: Series de preços com datetime index

        Returns:
            DataFrame com signals e métricas
        """
        df = pd.DataFrame({'price': prices})

        # Calcular indicadores vectorizados
        df['indicator1'] = df['price'].rolling(int(self.params.param1)).mean()
        df['indicator2'] = df['price'].rolling(int(self.params.param2)).mean()

        # Gerar sinais
        df['signal'] = 0
        df.loc[df['indicator1'] > df['indicator2'], 'signal'] = 1  # BUY
        df.loc[df['indicator1'] < df['indicator2'], 'signal'] = -1  # SELL

        # Calcular retornos
        df['returns'] = df['price'].pct_change()
        df['strategy_returns'] = df['signal'].shift(1) * df['returns']

        # Equity curve
        df['equity'] = (1 + df['strategy_returns']).cumprod() * 100000

        return df
```

**Usar estratégia Python:**

```python
# Criar estratégia
params = MyPythonStrategyParams(param1=50.0, param2=200.0)
strategy = MyPythonStrategy(params)

# Backtest vectorizado (rápido)
import yfinance as yf
df = yf.download('AAPL', start='2024-01-01', end='2024-12-31')
results = strategy.backtest(df['Close'])

# Visualizar
print(f"Final Equity: ${results['equity'].iloc[-1]:,.2f}")
print(f"Total Return: {(results['equity'].iloc[-1] / 100000 - 1):.2%}")

# Plot
import matplotlib.pyplot as plt
results['equity'].plot(title='Equity Curve', figsize=(12, 6))
plt.show()
```

### Strategy Best Practices

Lista de best practices baseadas em minha experiência:

#### 1. Parameter Validation

**Sempre valide parâmetros no constructor:**

```cpp
MyStrategy::MyStrategy(int fast, int slow) {
    if (fast >= slow) {
        throw std::invalid_argument("fast must be < slow");
    }
    if (fast < 2 || slow < 2) {
        throw std::invalid_argument("periods must be >= 2");
    }
}
```

#### 2. Avoid Look-Ahead Bias

**Nunca use informação do futuro:**

```cpp
// ❌ ERRADO - Usa data[i+1]
for (int i = 0; i < data.size() - 1; i++) {
    if (data[i+1] > data[i]) {  // Look-ahead bias!
        signals.push_back(BUY);
    }
}

// ✅ CORRETO - Usa apenas data passado
for (int i = 1; i < data.size(); i++) {
    if (data[i] > data[i-1]) {  // OK
        signals.push_back(BUY);
    }
}
```

#### 3. Handle Warmup Period

**Retorne HOLD até ter dados suficientes:**

```cpp
SignalType MyStrategy::generate_signal(const MarketDataPoint& data) {
    // Warmup period
    if (price_history_.size() < slow_period_) {
        return SignalType::HOLD;
    }

    // Lógica de sinal...
}
```

#### 4. Unit Test Thoroughly

**Teste edge cases:**

```cpp
TEST(MyStrategyTest, HandlesEmptyData) {
    MyStrategy strategy(10, 20);
    EXPECT_EQ(strategy.on_data(100.0), SignalType::HOLD);
}

TEST(MyStrategyTest, HandlesNaN) {
    MyStrategy strategy(10, 20);
    EXPECT_THROW(strategy.on_data(NAN), std::invalid_argument);
}

TEST(MyStrategyTest, HandlesCrossovers) {
    MyStrategy strategy(2, 5);

    // Feed data that causes crossover
    std::vector<double> prices = {100, 101, 102, 103, 104, 103, 102, 101, 100};

    std::vector<SignalType> signals;
    for (double p : prices) {
        signals.push_back(strategy.on_data(p));
    }

    // Assert correct crossover signals
    // ...
}
```

#### 5. Document Strategy Logic

**Documente claramente a lógica:**

```cpp
/**
 * Triple Moving Average Strategy
 *
 * Signals:
 * - BUY: When fast_sma > mid_sma > slow_sma (bullish alignment)
 * - SELL: When fast_sma < mid_sma < slow_sma (bearish alignment)
 * - HOLD: Otherwise
 *
 * Parameters:
 * - fast_period: Fast SMA period (e.g., 10)
 * - mid_period: Mid SMA period (e.g., 20)
 * - slow_period: Slow SMA period (e.g., 50)
 *
 * Typical usage:
 *   TripleSmaStrategy strategy(10, 20, 50);
 *
 * References:
 * - https://www.investopedia.com/articles/active-trading/052014/how-use-moving-average-buy-stocks.asp
 */
class TripleSmaStrategy : public AbstractStrategy {
    // ...
};
```

## 🚀 Deployment Guide

### Production Deployment

Guia completo para deployment em produção.

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      LOAD BALANCER                      │
│                     (Nginx / HAProxy)                   │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Backend API 1  │     │  Backend API 2  │
│   (FastAPI)     │     │   (FastAPI)     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │    PostgreSQL         │
         │  (Master + Replicas)  │
         └───────────────────────┘
```

#### 1. Docker Build

Dockerfiles otimizados para produção.

**Backend Dockerfile:**

```dockerfile
# Dockerfile.backend
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    g++ \
    cmake \
    make \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy source
COPY . .

# Build C++ engine
RUN mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc) && \
    make install

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built artifacts
COPY --from=builder /app/build/nexus_bindings*.so /app/
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY backend/python /app/backend/python

ENV PYTHONPATH=/app
ENV LD_LIBRARY_PATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.python.src.presentation.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile:**

```dockerfile
# Dockerfile.frontend
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    qt6-base-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY frontend /app/frontend

ENV PYTHONPATH=/app
ENV BACKEND_URL=http://backend:8000

CMD ["python", "frontend/src/main.py"]
```

#### 2. Docker Compose

docker-compose para orquestrar todos os serviços.

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # PostgreSQL (Master)
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: nexus_engine
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis (Cache)
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Backend API (2 replicas)
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
    deploy:
      replicas: 2
    environment:
      DATABASE_URL: postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/nexus_engine
      REDIS_URL: redis://redis:6379
      ALPHA_VANTAGE_API_KEY: ${ALPHA_VANTAGE_API_KEY}
      FINNHUB_API_KEY: ${FINNHUB_API_KEY}
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx (Load Balancer)
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend

  # Prometheus
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=15d'

  # Loki
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/loki-config.yml:ro
      - loki_data:/loki

  # Tempo
  tempo:
    image: grafana/tempo:latest
    ports:
      - "3200:3200"
      - "4317:4317"  # OTLP gRPC
    volumes:
      - ./tempo-config.yml:/etc/tempo/tempo-config.yml:ro
      - tempo_data:/var/tempo

  # Grafana
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus
      - loki
      - tempo

volumes:
  postgres_data:
  prometheus_data:
  loki_data:
  tempo_data:
  grafana_data:
```

#### 3. Nginx Configuration

```nginx
# nginx.conf
upstream backend {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    server_name nexus.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name nexus.example.com;

    # SSL certificates
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # API endpoints
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts (backtests podem ser longos)
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # WebSocket (para live trading)
    location /ws/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Static files
    location /static/ {
        alias /app/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

#### 4. Deploy to Production

**Usando Docker Compose:**

```bash
# 1. Configure environment variables
cp .env.example .env.prod
nano .env.prod  # Editar com valores de produção

# 2. Build images
docker-compose -f docker-compose.prod.yml build

# 3. Start services
docker-compose -f docker-compose.prod.yml up -d

# 4. Run migrations
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head

# 5. Check health
docker-compose -f docker-compose.prod.yml ps
curl http://localhost/api/v1/health

# 6. View logs
docker-compose -f docker-compose.prod.yml logs -f backend
```

**Usando Kubernetes:**

Também manifests Kubernetes para produção em larga escala.

```bash
# Aplicar manifests
kubectl apply -f k8s/namespace.yml
kubectl apply -f k8s/configmap.yml
kubectl apply -f k8s/secrets.yml
kubectl apply -f k8s/postgres.yml
kubectl apply -f k8s/redis.yml
kubectl apply -f k8s/backend.yml
kubectl apply -f k8s/ingress.yml

# Verificar status
kubectl get pods -n nexus-engine
kubectl get svc -n nexus-engine

# Logs
kubectl logs -f -n nexus-engine deployment/backend
```

#### 5. Monitoring

Dashboards Grafana para monitorar produção.

**Acessar Grafana:**

```
http://localhost:3000
Username: admin
Password: (ver GRAFANA_PASSWORD no .env)
```

**Dashboards incluídos:**

1. **System Overview**
   - CPU, Memory, Disk usage
   - Network I/O
   - Container health

2. **Application Metrics**
   - Request rate, latency, errors
   - Backtest duration distribution
   - Active backtests gauge

3. **Database Metrics**
   - Connection pool usage
   - Query latency
   - Slow queries

4. **Business Metrics**
   - Strategies created per day
   - Backtests executed per hour
   - Most used strategies

#### 6. Backup & Recovery

Script de backup automatizado.

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"

# Backup PostgreSQL
docker-compose exec -T postgres pg_dump -U nexus_user nexus_engine | gzip > $BACKUP_DIR/postgres_$DATE.sql.gz

# Backup uploaded files
tar -czf $BACKUP_DIR/files_$DATE.tar.gz /app/uploads

# Backup Grafana dashboards
docker-compose exec -T grafana grafana-cli admin data-migration backup > $BACKUP_DIR/grafana_$DATE.json

# Cleanup old backups (> 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.json" -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Agendar backups (cron):**

```bash
# Editar crontab
crontab -e

# Adicionar linha (backup diário às 2 AM)
0 2 * * * /path/to/backup.sh >> /var/log/nexus_backup.log 2>&1
```

**Restore from backup:**

```bash
# Restaurar PostgreSQL
gunzip < postgres_20240115_020000.sql.gz | docker-compose exec -T postgres psql -U nexus_user nexus_engine

# Restaurar files
tar -xzf files_20240115_020000.tar.gz -C /
```

#### 7. Performance Tuning

Configurações otimizadas para produção.

**PostgreSQL tuning (postgresql.conf):**

```ini
# Connections
max_connections = 100

# Memory
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 64MB

# WAL
wal_buffers = 16MB
checkpoint_completion_target = 0.9
max_wal_size = 4GB

# Query Planning
random_page_cost = 1.1  # Para SSD
effective_io_concurrency = 200

# Logging
log_min_duration_statement = 1000  # Log queries > 1s
```

**FastAPI tuning:**

```python
# main.py
app = FastAPI(
    title="Nexus Engine API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Increase worker count (gunicorn)
# gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

#### 8. Security Checklist

Checklist de segurança:

- [ ] HTTPS habilitado com certificado válido
- [ ] Environment variables não commitadas no Git
- [ ] Database com usuário non-root
- [ ] API rate limiting configurado
- [ ] JWT tokens com expiration
- [ ] SQL injection protection (via ORM)
- [ ] CORS configurado corretamente
- [ ] Secrets usando Docker Secrets ou Kubernetes Secrets
- [ ] Firewall configurado (apenas portas necessárias)
- [ ] Logs de acesso habilitados
- [ ] Backup automático agendado
- [ ] Monitoring e alerting configurados

## 🎓 Advanced Topics

### Walk-Forward Analysis

Suporte para walk-forward analysis (validação out-of-sample).

```python
from backend.python.src.application.services.walk_forward_service import WalkForwardService

# Configurar walk-forward
wf_service = WalkForwardService(
    strategy_id=strategy_id,
    symbol=Symbol("AAPL"),
    total_period=TimeRange(
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2024, 12, 31)
    ),
    in_sample_months=12,    # Otimizar em 12 meses
    out_sample_months=3,    # Testar em 3 meses
    optimization_metric='sharpe_ratio'
)

# Executar
result = wf_service.run_walk_forward()

# Resultados
print(f"In-Sample Sharpe: {result.in_sample_sharpe:.2f}")
print(f"Out-Sample Sharpe: {result.out_sample_sharpe:.2f}")
print(f"Degradation: {result.degradation:.1%}")
```

### Multi-Asset Portfolio

Suporte para portfolios multi-asset.

```python
from backend.python.src.domain.entities.portfolio import Portfolio

# Criar portfolio
portfolio = Portfolio(
    name="Tech Portfolio",
    initial_capital=100000.0,
    allocation={
        'AAPL': 0.25,
        'GOOGL': 0.25,
        'MSFT': 0.25,
        'NVDA': 0.25
    }
)

# Executar backtest de portfolio
result = portfolio_backtest_service.execute(
    portfolio=portfolio,
    time_range=TimeRange(...),
    rebalance_frequency='monthly'
)
```

## 📚 Resources

### Documentation

- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **API Reference**: [API.md](API.md)
- **Observability**: [OBSERVABILITY.md](OBSERVABILITY.md)
- **This Guide**: [GUIDE.md](GUIDE.md)

### External Resources

**Trading & Backtesting:**
- https://www.investopedia.com/articles/active-trading/101014/basics-algorithmic-trading-concepts-and-examples.asp
- https://www.quantstart.com/articles/Beginners-Guide-to-Quantitative-Trading

**Technical Analysis:**
- https://www.investopedia.com/technical-analysis-4689657
- https://school.stockcharts.com/doku.php

**Python Libraries:**
- Pandas: https://pandas.pydata.org/docs/
- NumPy: https://numpy.org/doc/
- PyQt6: https://www.riverbankcomputing.com/static/Docs/PyQt6/

**C++ Libraries:**
- PyBind11: https://pybind11.readthedocs.io/
- GoogleTest: https://google.github.io/googletest/

---

**Guia para que você possa:**
- ✅ Setup em minutos
- ✅ Criar estratégias rapidamente
- ✅ Deploy em produção com confiança
- ✅ Monitorar e otimizar performance

**Happy trading!** 🚀📈