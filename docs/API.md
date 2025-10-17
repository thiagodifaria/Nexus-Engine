# 🔌 Nexus Engine - API Reference

## 📋 Visão Geral

Três níveis de APIs no Nexus Engine:

1. **C++ Engine API**: API nativa de alto desempenho (via PyBind11)
2. **Python Backend API**: API de aplicação (Use Cases e Services)
3. **REST API**: API HTTP para comunicação Frontend ↔ Backend (FastAPI)

Decidi documentar todas as três porque cada uma serve um propósito diferente:
- C++ API: Para estratégias de máxima performance
- Python API: Para lógica de negócio e orquestração
- REST API: Para interface com frontend

## 🚀 C++ Engine API (PyBind11 Bindings)

### Visão Geral

Bindings PyBind11 que expõem todo o C++ engine ao Python. Decidi manter API simples e Pythonic.

```python
import nexus_bindings as nexus
```

### 📊 Strategy Classes

#### SmaStrategy

Estratégia de cruzamento de médias móveis (Simple Moving Average Crossover).

```python
class SmaStrategy(AbstractStrategy):
    """
    Estratégia baseada em cruzamento de SMAs

    Sinal BUY: Quando fast_sma cruza acima de slow_sma
    Sinal SELL: Quando fast_sma cruza abaixo de slow_sma
    """

    def __init__(self, fast_period: int, slow_period: int):
        """
        Args:
            fast_period: Período da média rápida (ex: 50)
            slow_period: Período da média lenta (ex: 200)

        Raises:
            ValueError: Se fast_period >= slow_period
        """
```

**Exemplo de uso:**

```python
# Criar estratégia SMA 50/200
strategy = nexus.SmaStrategy(fast_period=50, slow_period=200)

# Processar dados tick-by-tick
prices = [100.0, 101.0, 102.0, ...]
signals = []

for price in prices:
    signal = strategy.on_data(price)
    signals.append(signal)

# Obter valores das SMAs
current_fast_sma = strategy.get_fast_sma()
current_slow_sma = strategy.get_slow_sma()

print(f"Fast SMA: {current_fast_sma:.2f}")
print(f"Slow SMA: {current_slow_sma:.2f}")
```

**Métodos:**

| Método | Descrição | Retorno |
|--------|-----------|---------|
| `on_data(price: float)` | Processa novo preço e gera sinal | `SignalType` (BUY/SELL/HOLD) |
| `get_fast_sma()` | Retorna valor atual da SMA rápida | `float` |
| `get_slow_sma()` | Retorna valor atual da SMA lenta | `float` |

#### RsiStrategy

Estratégia de mean reversion baseada em RSI (Relative Strength Index).

```python
class RsiStrategy(AbstractStrategy):
    """
    Estratégia baseada em RSI para mean reversion

    Sinal BUY: Quando RSI < oversold (ex: 30)
    Sinal SELL: Quando RSI > overbought (ex: 70)
    """

    def __init__(self, period: int = 14, oversold: float = 30.0, overbought: float = 70.0):
        """
        Args:
            period: Período do RSI (padrão: 14)
            oversold: Threshold de oversold (padrão: 30)
            overbought: Threshold de overbought (padrão: 70)
        """
```

**Exemplo de uso:**

```python
# Criar estratégia RSI com parâmetros customizados
strategy = nexus.RsiStrategy(period=14, oversold=25, overbought=75)

# Processar dados
for price in prices:
    signal = strategy.on_data(price)
    if signal == nexus.SignalType.BUY:
        print(f"BUY signal at {price:.2f}, RSI: {strategy.get_rsi():.2f}")
    elif signal == nexus.SignalType.SELL:
        print(f"SELL signal at {price:.2f}, RSI: {strategy.get_rsi():.2f}")

# Obter valor atual do RSI
current_rsi = strategy.get_rsi()
```

**Métodos:**

| Método | Descrição | Retorno |
|--------|-----------|---------|
| `on_data(price: float)` | Processa novo preço | `SignalType` |
| `get_rsi()` | Retorna RSI atual (0-100) | `float` |

#### MacdStrategy

Estratégia baseada em MACD (Moving Average Convergence Divergence).

```python
class MacdStrategy(AbstractStrategy):
    """
    Estratégia baseada em MACD

    Sinal BUY: Quando MACD cruza acima da signal line
    Sinal SELL: Quando MACD cruza abaixo da signal line
    """

    def __init__(
        self,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ):
        """
        Args:
            fast_period: Período da EMA rápida (padrão: 12)
            slow_period: Período da EMA lenta (padrão: 26)
            signal_period: Período da signal line (padrão: 9)
        """
```

**Exemplo de uso:**

```python
# Criar estratégia MACD com parâmetros padrão
strategy = nexus.MacdStrategy()

# Ou com parâmetros customizados
strategy = nexus.MacdStrategy(fast_period=10, slow_period=20, signal_period=7)

# Processar dados
for price in prices:
    signal = strategy.on_data(price)

# Obter componentes do MACD
macd_line = strategy.get_macd_line()
signal_line = strategy.get_signal_line()
histogram = strategy.get_histogram()

print(f"MACD: {macd_line:.4f}")
print(f"Signal: {signal_line:.4f}")
print(f"Histogram: {histogram:.4f}")
```

**Métodos:**

| Método | Descrição | Retorno |
|--------|-----------|---------|
| `on_data(price: float)` | Processa novo preço | `SignalType` |
| `get_macd_line()` | Retorna valor da MACD line | `float` |
| `get_signal_line()` | Retorna valor da signal line | `float` |
| `get_histogram()` | Retorna MACD - Signal | `float` |

### 🎯 SignalType Enum

Enum para tipos de sinais:

```python
class SignalType(Enum):
    """
    Tipos de sinais que estratégias podem emitir
    """
    BUY = 1   # Sinal de compra
    SELL = -1 # Sinal de venda
    HOLD = 0  # Sinal neutro (sem ação)
```

### 🏭 BacktestEngine

Engine de backtesting que executa estratégias em dados históricos.

```python
class BacktestEngine:
    """
    Engine de backtesting de alto desempenho

    Processa dados históricos e simula execução de estratégia
    com latências sub-microsegundo
    """

    def __init__(self):
        """Cria nova instância do engine"""

    def run(
        self,
        strategy: AbstractStrategy,
        prices: List[float],
        timestamps: List[datetime],
        initial_capital: float = 100000.0
    ) -> BacktestResult:
        """
        Executa backtest completo

        Args:
            strategy: Instância da estratégia
            prices: Lista de preços históricos
            timestamps: Lista de timestamps correspondentes
            initial_capital: Capital inicial (padrão: $100,000)

        Returns:
            BacktestResult com métricas e trades

        Raises:
            ValueError: Se len(prices) != len(timestamps)
            ValueError: Se initial_capital <= 0
        """
```

**Exemplo de uso:**

```python
import nexus_bindings as nexus
import pandas as pd
from datetime import datetime

# Carregar dados históricos
df = pd.read_csv('AAPL_daily.csv')
prices = df['close'].tolist()
timestamps = pd.to_datetime(df['date']).tolist()

# Criar estratégia
strategy = nexus.SmaStrategy(fast_period=50, slow_period=200)

# Criar engine e executar
engine = nexus.BacktestEngine()
result = engine.run(
    strategy=strategy,
    prices=prices,
    timestamps=timestamps,
    initial_capital=100000.0
)

# Acessar resultados
print(f"Total Return: {result.total_return:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
print(f"Max Drawdown: {result.max_drawdown:.2%}")
print(f"Total Trades: {result.total_trades}")
print(f"Win Rate: {result.win_rate:.2%}")

# Acessar equity curve
equity = result.equity_curve
dates = result.timestamps

# Plot (usando matplotlib ou PyQtGraph)
import matplotlib.pyplot as plt
plt.plot(dates, equity)
plt.title('Equity Curve')
plt.show()

# Acessar trades individuais
for trade in result.trades:
    print(f"{trade.entry_date}: {trade.signal_type} at {trade.entry_price:.2f}")
    print(f"  Exit: {trade.exit_date} at {trade.exit_price:.2f}")
    print(f"  P&L: ${trade.pnl:.2f} ({trade.return_pct:.2%})")
```

### 📈 BacktestResult

Estrutura de resultados com todas as métricas essenciais.

```python
class BacktestResult:
    """
    Resultado de backtest com métricas de performance
    """

    # Métricas de retorno
    total_return: float          # Retorno total (ex: 0.15 = 15%)
    annualized_return: float     # Retorno anualizado

    # Métricas de risco
    sharpe_ratio: float          # Sharpe ratio
    sortino_ratio: float         # Sortino ratio (downside risk)
    max_drawdown: float          # Drawdown máximo (negativo)
    calmar_ratio: float          # Calmar ratio (return / max_drawdown)

    # Métricas de trades
    total_trades: int            # Número total de trades
    winning_trades: int          # Número de trades lucrativos
    losing_trades: int           # Número de trades com prejuízo
    win_rate: float              # Taxa de acerto (0-1)

    # Métricas de P&L
    avg_win: float               # P&L médio de trades ganhos
    avg_loss: float              # P&L médio de trades perdidos
    profit_factor: float         # Total win / Total loss
    recovery_factor: float       # Total return / Max drawdown

    # Dados brutos
    equity_curve: List[float]    # Curva de equity
    timestamps: List[datetime]   # Timestamps correspondentes
    trades: List[Trade]          # Lista de todos os trades
```

**Acessando métricas:**

```python
result = engine.run(...)

# Métricas principais
print(f"Total Return: {result.total_return:.2%}")
print(f"Annualized: {result.annualized_return:.2%}")
print(f"Sharpe: {result.sharpe_ratio:.2f}")
print(f"Sortino: {result.sortino_ratio:.2f}")
print(f"Max DD: {result.max_drawdown:.2%}")
print(f"Calmar: {result.calmar_ratio:.2f}")

# Estatísticas de trades
print(f"\nTrades: {result.total_trades}")
print(f"Wins: {result.winning_trades} ({result.win_rate:.1%})")
print(f"Losses: {result.losing_trades}")
print(f"Avg Win: ${result.avg_win:.2f}")
print(f"Avg Loss: ${result.avg_loss:.2f}")
print(f"Profit Factor: {result.profit_factor:.2f}")

# Equity final
final_equity = result.equity_curve[-1]
print(f"\nFinal Equity: ${final_equity:,.2f}")
```

### 💹 Trade

Estrutura para representar trade individual.

```python
class Trade:
    """
    Representa um trade completo (entry + exit)
    """

    trade_id: int                # ID único do trade
    signal_type: SignalType      # BUY ou SELL

    # Entry
    entry_date: datetime         # Data/hora de entrada
    entry_price: float           # Preço de entrada
    quantity: float              # Quantidade (shares)

    # Exit
    exit_date: datetime          # Data/hora de saída
    exit_price: float            # Preço de saída

    # P&L
    pnl: float                   # Profit & Loss em $
    return_pct: float            # Retorno percentual

    # Duration
    duration_bars: int           # Duração em bars
    duration_days: float         # Duração em dias
```

### 📊 PerformanceAnalyzer

Analisador de performance que calcula métricas adicionais.

```python
class PerformanceAnalyzer:
    """
    Analisador avançado de performance

    Calcula métricas adicionais não computadas pelo BacktestEngine
    """

    def __init__(self):
        """Cria nova instância do analyzer"""

    def analyze(
        self,
        trades: List[Trade],
        equity_curve: List[float]
    ) -> PerformanceMetrics:
        """
        Analisa performance detalhada

        Args:
            trades: Lista de trades
            equity_curve: Curva de equity

        Returns:
            PerformanceMetrics com análise detalhada
        """
```

**Exemplo de uso:**

```python
# Executar backtest
result = engine.run(strategy, prices, timestamps)

# Análise adicional
analyzer = nexus.PerformanceAnalyzer()
metrics = analyzer.analyze(result.trades, result.equity_curve)

# Métricas adicionais
print(f"Kelly Criterion: {metrics.kelly_criterion:.2%}")
print(f"Risk of Ruin: {metrics.risk_of_ruin:.2%}")
print(f"Consecutive Wins: {metrics.max_consecutive_wins}")
print(f"Consecutive Losses: {metrics.max_consecutive_losses}")
print(f"Avg Trade Duration: {metrics.avg_trade_duration_days:.1f} days")
```

### 🎲 MonteCarloSimulator

Simulador Monte Carlo para análise de robustez.

```python
class MonteCarloSimulator:
    """
    Simulador Monte Carlo para validação de estratégias

    Reamostra trades históricos para gerar distribuição de resultados possíveis
    """

    def __init__(self):
        """Cria nova instância do simulator"""

    def run_simulation(
        self,
        trades: List[Trade],
        num_simulations: int = 1000,
        num_trades_per_simulation: Optional[int] = None
    ) -> SimulationResult:
        """
        Executa simulação Monte Carlo

        Args:
            trades: Trades históricos para reamostrar
            num_simulations: Número de simulações (padrão: 1000)
            num_trades_per_simulation: Trades por simulação (padrão: len(trades))

        Returns:
            SimulationResult com distribuições e intervalos de confiança
        """
```

**Exemplo de uso:**

```python
# Executar backtest
result = engine.run(strategy, prices, timestamps)

# Simulação Monte Carlo
simulator = nexus.MonteCarloSimulator()
mc_result = simulator.run_simulation(
    trades=result.trades,
    num_simulations=10000
)

# Intervalos de confiança
print(f"Expected Return:")
print(f"  5th percentile: {mc_result.return_p5:.2%}")
print(f"  50th percentile: {mc_result.return_p50:.2%}")
print(f"  95th percentile: {mc_result.return_p95:.2%}")

print(f"\nMax Drawdown:")
print(f"  5th percentile: {mc_result.drawdown_p5:.2%}")
print(f"  50th percentile: {mc_result.drawdown_p50:.2%}")
print(f"  95th percentile: {mc_result.drawdown_p95:.2%}")

# Probabilidade de profit
print(f"\nProb of Profit: {mc_result.prob_profit:.1%}")
print(f"Prob of Loss > 10%: {mc_result.prob_loss_gt_10pct:.1%}")

# Visualizar distribuição
import matplotlib.pyplot as plt

plt.figure(figsize=(12, 5))

plt.subplot(1, 2, 1)
plt.hist(mc_result.return_distribution, bins=50, alpha=0.7)
plt.axvline(mc_result.return_p5, color='r', linestyle='--', label='5th percentile')
plt.axvline(mc_result.return_p95, color='g', linestyle='--', label='95th percentile')
plt.title('Return Distribution')
plt.legend()

plt.subplot(1, 2, 2)
plt.hist(mc_result.drawdown_distribution, bins=50, alpha=0.7)
plt.title('Drawdown Distribution')

plt.tight_layout()
plt.show()
```

### 🔧 StrategyOptimizer

Otimizador de parâmetros com Grid Search e Genetic Algorithm.

```python
class StrategyOptimizer:
    """
    Otimizador de parâmetros de estratégias

    Suporta dois algoritmos:
    - Grid Search: Busca exaustiva (melhor para 2-3 parâmetros)
    - Genetic Algorithm: Busca heurística (melhor para 5+ parâmetros)
    """

    def __init__(self):
        """Cria nova instância do optimizer"""

    def optimize_grid_search(
        self,
        strategy_type: str,  # "sma", "rsi", "macd"
        prices: List[float],
        timestamps: List[datetime],
        parameter_grid: Dict[str, List[Any]],
        metric: str = "sharpe_ratio",  # Métrica para otimizar
        initial_capital: float = 100000.0
    ) -> OptimizationResult:
        """
        Otimiza via grid search

        Args:
            strategy_type: Tipo da estratégia
            prices: Dados históricos
            timestamps: Timestamps
            parameter_grid: Grid de parâmetros
            metric: Métrica para maximizar
            initial_capital: Capital inicial

        Returns:
            OptimizationResult com melhores parâmetros
        """

    def optimize_genetic_algorithm(
        self,
        strategy_type: str,
        prices: List[float],
        timestamps: List[datetime],
        parameter_ranges: Dict[str, Tuple[float, float]],
        population_size: int = 50,
        num_generations: int = 100,
        mutation_rate: float = 0.1,
        metric: str = "sharpe_ratio",
        initial_capital: float = 100000.0
    ) -> OptimizationResult:
        """
        Otimiza via algoritmo genético

        Args:
            strategy_type: Tipo da estratégia
            prices: Dados históricos
            timestamps: Timestamps
            parameter_ranges: Ranges de parâmetros
            population_size: Tamanho da população
            num_generations: Número de gerações
            mutation_rate: Taxa de mutação
            metric: Métrica para maximizar
            initial_capital: Capital inicial

        Returns:
            OptimizationResult com melhores parâmetros
        """
```

**Exemplo: Grid Search**

```python
# Definir grid de parâmetros
parameter_grid = {
    'fast_period': [20, 30, 40, 50, 60],
    'slow_period': [100, 150, 200, 250, 300]
}

# Otimizar
optimizer = nexus.StrategyOptimizer()
result = optimizer.optimize_grid_search(
    strategy_type='sma',
    prices=prices,
    timestamps=timestamps,
    parameter_grid=parameter_grid,
    metric='sharpe_ratio'
)

# Melhores parâmetros
print(f"Best Parameters: {result.best_parameters}")
print(f"Best Sharpe: {result.best_metric_value:.2f}")

# Histórico de otimização
for step in result.optimization_history:
    print(f"{step.parameters} → {step.metric_value:.2f}")

# Criar estratégia com parâmetros ótimos
optimal_strategy = nexus.SmaStrategy(
    fast_period=result.best_parameters['fast_period'],
    slow_period=result.best_parameters['slow_period']
)
```

**Exemplo: Genetic Algorithm**

```python
# Definir ranges de parâmetros
parameter_ranges = {
    'fast_period': (10, 100),
    'slow_period': (100, 300)
}

# Otimizar
result = optimizer.optimize_genetic_algorithm(
    strategy_type='sma',
    prices=prices,
    timestamps=timestamps,
    parameter_ranges=parameter_ranges,
    population_size=100,
    num_generations=50,
    metric='sortino_ratio'
)

print(f"Best Parameters: {result.best_parameters}")
print(f"Best Sortino: {result.best_metric_value:.2f}")
print(f"Generations: {len(result.optimization_history)}")
```

## 🐍 Python Backend API

### Application Layer - Use Cases

Use cases como entry points da aplicação.

#### RunBacktestUseCase

```python
class RunBacktestUseCase:
    """
    Use case para executar backtest completo

    Orquestra: Strategy → Market Data → C++ Engine → Persistence → Telemetry
    """

    def execute(
        self,
        strategy_id: UUID,
        symbol: Symbol,
        time_range: TimeRange,
        initial_capital: float = 100000.0
    ) -> BacktestResult:
        """
        Executa backtest

        Args:
            strategy_id: ID da estratégia
            symbol: Símbolo para backtest
            time_range: Range de datas
            initial_capital: Capital inicial

        Returns:
            BacktestResult com métricas e trades

        Raises:
            StrategyNotFoundError: Se estratégia não existe
            MarketDataError: Se falha ao buscar dados
            ValidationError: Se parâmetros inválidos
        """
```

**Exemplo de uso:**

```python
from backend.python.src.application.use_cases.run_backtest import RunBacktestUseCase
from backend.python.src.domain.value_objects import Symbol, TimeRange
from datetime import datetime

# Injetar dependências (normalmente via DI container)
use_case = RunBacktestUseCase(
    strategy_repository=strategy_repo,
    backtest_repository=backtest_repo,
    market_data_service=market_data_service,
    cpp_bridge=cpp_bridge,
    telemetry=telemetry
)

# Executar backtest
result = use_case.execute(
    strategy_id=UUID('...'),
    symbol=Symbol('AAPL'),
    time_range=TimeRange(
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31)
    ),
    initial_capital=100000.0
)

print(f"Return: {result.total_return:.2%}")
print(f"Sharpe: {result.sharpe_ratio:.2f}")
```

#### CreateStrategyUseCase

```python
class CreateStrategyUseCase:
    """
    Use case para criar nova estratégia
    """

    def execute(
        self,
        name: str,
        strategy_type: StrategyType,
        parameters: StrategyParameters,
        validate: bool = True
    ) -> Strategy:
        """
        Cria estratégia

        Args:
            name: Nome da estratégia
            strategy_type: Tipo (SMA, RSI, MACD)
            parameters: Parâmetros
            validate: Se deve validar parâmetros

        Returns:
            Strategy criada com ID

        Raises:
            ValidationError: Se parâmetros inválidos
            DuplicateNameError: Se nome já existe
        """
```

#### OptimizeStrategyUseCase

```python
class OptimizeStrategyUseCase:
    """
    Use case para otimizar parâmetros de estratégia
    """

    def execute(
        self,
        strategy_id: UUID,
        symbol: Symbol,
        time_range: TimeRange,
        parameter_ranges: Dict[str, Tuple[float, float]],
        algorithm: str = "genetic",  # "grid" ou "genetic"
        metric: str = "sharpe_ratio"
    ) -> OptimizationResult:
        """
        Otimiza estratégia

        Args:
            strategy_id: ID da estratégia base
            symbol: Símbolo para otimização
            time_range: Range de datas
            parameter_ranges: Ranges de parâmetros
            algorithm: Algoritmo de otimização
            metric: Métrica para maximizar

        Returns:
            OptimizationResult com melhores parâmetros
        """
```

### Application Layer - Services

#### MarketDataService

```python
class MarketDataService:
    """
    Service para buscar dados de mercado

    Abstrai múltiplos providers (AlphaVantage, Finnhub, YFinance)
    """

    def fetch_daily(
        self,
        symbol: Symbol,
        time_range: TimeRange
    ) -> pd.DataFrame:
        """
        Busca dados diários

        Args:
            symbol: Símbolo
            time_range: Range de datas

        Returns:
            DataFrame com colunas: timestamp, open, high, low, close, volume

        Raises:
            MarketDataError: Se falha ao buscar
        """

    def fetch_intraday(
        self,
        symbol: Symbol,
        interval: str = "1min"
    ) -> pd.DataFrame:
        """
        Busca dados intraday

        Args:
            symbol: Símbolo
            interval: Intervalo (1min, 5min, 15min, 30min, 1h)

        Returns:
            DataFrame com dados intraday
        """
```

#### StrategyService

```python
class StrategyService:
    """
    Service para gerenciar estratégias
    """

    def create_strategy(
        self,
        name: str,
        strategy_type: StrategyType,
        parameters: StrategyParameters
    ) -> Strategy:
        """Cria estratégia"""

    def get_strategy(self, strategy_id: UUID) -> Strategy:
        """Busca estratégia por ID"""

    def list_strategies(
        self,
        strategy_type: Optional[StrategyType] = None
    ) -> List[Strategy]:
        """Lista todas as estratégias (opcionalmente filtradas por tipo)"""

    def update_strategy(
        self,
        strategy_id: UUID,
        parameters: StrategyParameters
    ) -> Strategy:
        """Atualiza parâmetros"""

    def delete_strategy(self, strategy_id: UUID) -> None:
        """Deleta estratégia"""

    def clone_strategy(
        self,
        strategy_id: UUID,
        new_name: str
    ) -> Strategy:
        """Clona estratégia existente"""
```

## 🌐 REST API (FastAPI)

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

Autenticação via JWT (futuramente OAuth2).

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'

# Response
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer",
  "expires_in": 3600
}

# Usar token em requests
curl -X GET http://localhost:8000/api/v1/strategies \
  -H "Authorization: Bearer eyJhbGc..."
```

### 📊 Strategies Endpoints

#### POST /strategies

Cria nova estratégia.

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/strategies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "name": "My SMA Strategy",
    "strategy_type": "sma_crossover",
    "parameters": {
      "fast_period": 50,
      "slow_period": 200
    }
  }'
```

**Response (201 Created):**

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "My SMA Strategy",
  "strategy_type": "sma_crossover",
  "parameters": {
    "fast_period": 50,
    "slow_period": 200
  },
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

**Validações:**
- `name`: Obrigatório, 3-100 caracteres
- `strategy_type`: Enum válido (sma_crossover, rsi_mean_reversion, macd_crossover)
- `parameters`: Deve ser válido para o strategy_type

#### GET /strategies

Lista todas as estratégias.

**Request:**

```bash
curl -X GET http://localhost:8000/api/v1/strategies \
  -H "Authorization: Bearer TOKEN"

# Com filtro por tipo
curl -X GET "http://localhost:8000/api/v1/strategies?strategy_type=sma_crossover" \
  -H "Authorization: Bearer TOKEN"
```

**Response (200 OK):**

```json
{
  "strategies": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "name": "My SMA Strategy",
      "strategy_type": "sma_crossover",
      "parameters": {
        "fast_period": 50,
        "slow_period": 200
      },
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 1
}
```

#### GET /strategies/{id}

Busca estratégia por ID.

**Response (200 OK):** Objeto Strategy

**Response (404 Not Found):**

```json
{
  "detail": "Strategy not found"
}
```

#### PUT /strategies/{id}

Atualiza parâmetros de estratégia.

**Request:**

```bash
curl -X PUT http://localhost:8000/api/v1/strategies/{id} \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "parameters": {
      "fast_period": 40,
      "slow_period": 180
    }
  }'
```

#### DELETE /strategies/{id}

Deleta estratégia.

**Response (204 No Content)**

### 🎯 Backtests Endpoints

#### POST /backtests

Cria e executa backtest.

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/backtests \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "strategy_id": "123e4567-e89b-12d3-a456-426614174000",
    "symbol": "AAPL",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "initial_capital": 100000.0
  }'
```

**Response (201 Created):**

```json
{
  "id": "987fcdeb-51a2-43f7-8e9f-123456789abc",
  "strategy_id": "123e4567-e89b-12d3-a456-426614174000",
  "symbol": "AAPL",
  "start_date": "2024-01-01",
  "end_date": "2024-12-31",
  "initial_capital": 100000.0,
  "status": "completed",
  "results": {
    "total_return": 0.1532,
    "annualized_return": 0.1532,
    "sharpe_ratio": 1.85,
    "sortino_ratio": 2.34,
    "max_drawdown": -0.1245,
    "calmar_ratio": 1.23,
    "total_trades": 24,
    "winning_trades": 15,
    "losing_trades": 9,
    "win_rate": 0.625,
    "avg_win": 1250.50,
    "avg_loss": -780.30,
    "profit_factor": 2.41,
    "recovery_factor": 1.23
  },
  "equity_curve": [100000.0, 101500.0, ...],
  "trades": [...],
  "created_at": "2024-01-15T10:35:00Z",
  "completed_at": "2024-01-15T10:35:03Z"
}
```

**Validações:**
- `strategy_id`: Deve existir
- `symbol`: Formato válido (apenas letras)
- `start_date < end_date`
- `initial_capital > 0`

#### GET /backtests

Lista backtests.

**Query Parameters:**
- `strategy_id` (opcional): Filtrar por estratégia
- `symbol` (opcional): Filtrar por símbolo
- `limit` (padrão: 20): Número de resultados
- `offset` (padrão: 0): Paginação

**Response (200 OK):**

```json
{
  "backtests": [...],
  "total": 150,
  "limit": 20,
  "offset": 0
}
```

#### GET /backtests/{id}

Busca backtest por ID (inclui resultados completos).

#### GET /backtests/{id}/equity-curve

Retorna apenas equity curve (otimizado para charting).

**Response (200 OK):**

```json
{
  "timestamps": ["2024-01-01T00:00:00Z", ...],
  "equity": [100000.0, 101500.0, ...]
}
```

#### GET /backtests/{id}/trades

Retorna trades do backtest (paginado).

### 📈 Market Data Endpoints

#### GET /market-data/daily

Busca dados diários.

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/market-data/daily?symbol=AAPL&start_date=2024-01-01&end_date=2024-12-31" \
  -H "Authorization: Bearer TOKEN"
```

**Response (200 OK):**

```json
{
  "symbol": "AAPL",
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "open": 180.50,
      "high": 185.20,
      "low": 179.80,
      "close": 184.30,
      "volume": 52000000
    },
    ...
  ]
}
```

#### GET /market-data/intraday

Busca dados intraday.

**Query Parameters:**
- `symbol`: Símbolo
- `interval`: 1min, 5min, 15min, 30min, 1h

### 🔧 Optimization Endpoints

#### POST /optimizations

Inicia otimização de parâmetros.

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/optimizations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "strategy_id": "123e4567-e89b-12d3-a456-426614174000",
    "symbol": "AAPL",
    "start_date": "2024-01-01",
    "end_date": "2024-12-31",
    "parameter_ranges": {
      "fast_period": [10, 100],
      "slow_period": [100, 300]
    },
    "algorithm": "genetic",
    "metric": "sharpe_ratio",
    "population_size": 50,
    "num_generations": 100
  }'
```

**Response (202 Accepted):**

```json
{
  "optimization_id": "abc-123",
  "status": "running",
  "progress": 0,
  "estimated_time_remaining": 300
}
```

#### GET /optimizations/{id}

Consulta status de otimização.

**Response (200 OK):**

```json
{
  "optimization_id": "abc-123",
  "status": "completed",
  "progress": 100,
  "best_parameters": {
    "fast_period": 45,
    "slow_period": 185
  },
  "best_metric_value": 2.15,
  "optimization_history": [...]
}
```

### ⚠️ Error Responses

Respostas de erro padronizadas:

**400 Bad Request:**

```json
{
  "error": "validation_error",
  "detail": "Invalid parameters",
  "fields": {
    "fast_period": "Must be less than slow_period"
  }
}
```

**401 Unauthorized:**

```json
{
  "error": "unauthorized",
  "detail": "Invalid or expired token"
}
```

**404 Not Found:**

```json
{
  "error": "not_found",
  "detail": "Strategy not found"
}
```

**500 Internal Server Error:**

```json
{
  "error": "internal_error",
  "detail": "An unexpected error occurred",
  "trace_id": "abc123"  # Para debug
}
```

## 📚 References

**PyBind11 Documentation:**
- https://pybind11.readthedocs.io/

**FastAPI Documentation:**
- https://fastapi.tiangolo.com/

**Domain-Driven Design:**
- https://martinfowler.com/bliki/DomainDrivenDesign.html

---

**Implementei esta API priorizando:**
- ✅ Type safety (Pydantic schemas)
- ✅ Validação automática
- ✅ Documentação auto-gerada (Swagger)
- ✅ Performance (async/await)
- ✅ Developer experience (exemplos claros)

**Esta API está production-ready!** 🚀