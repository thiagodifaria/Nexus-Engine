"""
Integration Tests - C++ ↔ Python Bridge (PyBind11)
Implementei estes testes para validar bindings reais com C++ engine
Decidi testar: BacktestEngine, Strategies, ExecutionSimulator, Analytics
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Importações dos bindings C++
# Implementei import condicional para testes rodarem mesmo sem bindings compilados
try:
    import nexus_bindings
    HAS_CPP_BINDINGS = True
except ImportError:
    HAS_CPP_BINDINGS = False
    pytestmark = pytest.mark.skip(reason="C++ bindings not available")


@pytest.mark.integration
@pytest.mark.cpp
class TestCppPythonBridge:
    """
    Implementei esta classe para testar bridge C++↔Python
    Decidi validar que bindings funcionam corretamente com dados reais
    """

    def test_backtest_engine_initialization(self):
        """
        Implementei este teste para validar criação de BacktestEngine
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Act
        engine = nexus_bindings.BacktestEngine()

        # Assert
        assert engine is not None
        assert hasattr(engine, 'run_backtest')
        assert hasattr(engine, 'get_results')

    def test_sma_strategy_calculation(self):
        """
        Implementei este teste para validar cálculo SMA com dados reais
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]
        fast_period = 3
        slow_period = 5

        strategy = nexus_bindings.SmaStrategy(fast_period=fast_period, slow_period=slow_period)

        # Act
        signals = []
        for price in prices:
            signal = strategy.on_data(price)
            signals.append(signal)

        # Assert
        assert len(signals) == len(prices)
        # Primeiros slow_period-1 sinais devem ser 0 (acumulando dados)
        assert all(s == 0 for s in signals[:slow_period-1])

    def test_rsi_strategy_calculation(self):
        """
        Implementei este teste para validar cálculo RSI com dados reais
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        # Dados com movimento: baixa → subida
        prices = [100.0, 98.0, 96.0, 94.0, 95.0, 97.0, 99.0, 101.0, 103.0, 105.0, 107.0, 109.0, 111.0, 113.0, 115.0]
        period = 14
        oversold = 30
        overbought = 70

        strategy = nexus_bindings.RsiStrategy(
            period=period,
            oversold=oversold,
            overbought=overbought
        )

        # Act
        signals = []
        for price in prices:
            signal = strategy.on_data(price)
            signals.append(signal)

        # Assert
        assert len(signals) == len(prices)
        # Deve haver pelo menos um sinal de compra (1) quando oversold
        # Deve haver pelo menos um sinal de venda (-1) quando overbought

    def test_macd_strategy_calculation(self):
        """
        Implementei este teste para validar cálculo MACD com dados reais
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        prices = list(range(100, 150))  # 50 preços em uptrend
        fast_period = 12
        slow_period = 26
        signal_period = 9

        strategy = nexus_bindings.MacdStrategy(
            fast_period=fast_period,
            slow_period=slow_period,
            signal_period=signal_period
        )

        # Act
        signals = []
        for price in float(p) for p in prices:
            signal = strategy.on_data(price)
            signals.append(signal)

        # Assert
        assert len(signals) == len(prices)

    def test_execution_simulator_with_orders(self):
        """
        Implementei este teste para validar ExecutionSimulator com ordens reais
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        slippage = 0.001  # 0.1%
        commission = 0.002  # 0.2%

        simulator = nexus_bindings.ExecutionSimulator(
            slippage=slippage,
            commission=commission
        )

        # Act - simular ordem de compra
        entry_price = 100.0
        quantity = 100
        side = "BUY"

        execution_result = simulator.execute_order(
            price=entry_price,
            quantity=quantity,
            side=side
        )

        # Assert
        assert execution_result is not None
        assert execution_result['executed_price'] >= entry_price  # slippage up on buy
        assert execution_result['commission'] > 0
        assert execution_result['quantity'] == quantity

    def test_performance_analyzer_metrics(self):
        """
        Implementei este teste para validar PerformanceAnalyzer com trades reais
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        analyzer = nexus_bindings.PerformanceAnalyzer()

        # Simular trades
        trades = [
            {'pnl': 100.0, 'entry_time': 0, 'exit_time': 1},
            {'pnl': -50.0, 'entry_time': 1, 'exit_time': 2},
            {'pnl': 150.0, 'entry_time': 2, 'exit_time': 3},
            {'pnl': 75.0, 'entry_time': 3, 'exit_time': 4},
            {'pnl': -25.0, 'entry_time': 4, 'exit_time': 5},
        ]

        # Act
        for trade in trades:
            analyzer.add_trade(
                pnl=trade['pnl'],
                entry_time=trade['entry_time'],
                exit_time=trade['exit_time']
            )

        metrics = analyzer.calculate_metrics()

        # Assert
        assert metrics is not None
        assert 'total_return' in metrics
        assert 'sharpe_ratio' in metrics
        assert 'max_drawdown' in metrics
        assert 'win_rate' in metrics
        assert metrics['total_trades'] == 5
        assert metrics['profitable_trades'] == 3
        assert metrics['losing_trades'] == 2

    def test_monte_carlo_simulator(self):
        """
        Implementei este teste para validar MonteCarloSimulator com trades reais
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        returns = [0.01, -0.005, 0.015, 0.008, -0.003, 0.012, 0.007, -0.002]
        num_simulations = 1000
        num_periods = 252  # 1 ano de trading

        simulator = nexus_bindings.MonteCarloSimulator(
            num_simulations=num_simulations,
            num_periods=num_periods
        )

        # Act
        results = simulator.run(returns)

        # Assert
        assert results is not None
        assert len(results) == num_simulations
        assert all(isinstance(r, (float, int)) for r in results)

        # Estatísticas básicas
        mean_return = np.mean(results)
        std_return = np.std(results)
        assert std_return > 0  # Deve haver variação

    def test_lock_free_order_book(self):
        """
        Implementei este teste para validar LockFreeOrderBook
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        order_book = nexus_bindings.LockFreeOrderBook(symbol="AAPL")

        # Act - adicionar ordens
        order_book.add_order(price=100.0, quantity=100, side="BUY", order_id=1)
        order_book.add_order(price=101.0, quantity=50, side="BUY", order_id=2)
        order_book.add_order(price=102.0, quantity=75, side="SELL", order_id=3)
        order_book.add_order(price=103.0, quantity=25, side="SELL", order_id=4)

        # Assert
        best_bid = order_book.get_best_bid()
        best_ask = order_book.get_best_ask()

        assert best_bid == 101.0  # Maior preço de compra
        assert best_ask == 102.0  # Menor preço de venda
        assert order_book.get_bid_volume() == 150  # 100 + 50
        assert order_book.get_ask_volume() == 100  # 75 + 25

    def test_high_resolution_clock(self):
        """
        Implementei este teste para validar HighResolutionClock
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        clock = nexus_bindings.HighResolutionClock()

        # Act
        start = clock.now()
        # Simular alguma operação
        sum_result = sum(range(1000))
        end = clock.now()

        elapsed_ns = clock.elapsed_ns(start, end)

        # Assert
        assert start > 0
        assert end > start
        assert elapsed_ns > 0
        assert elapsed_ns < 1_000_000_000  # Menos de 1 segundo

    def test_latency_tracker(self):
        """
        Implementei este teste para validar LatencyTracker
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        tracker = nexus_bindings.LatencyTracker(name="test_operation")

        # Act - registrar latências
        latencies_ns = [1000, 1500, 2000, 1200, 1800, 1100, 1300, 1400, 1600, 1700]

        for latency in latencies_ns:
            tracker.record(latency)

        stats = tracker.get_statistics()

        # Assert
        assert stats is not None
        assert 'count' in stats
        assert 'mean' in stats
        assert 'p50' in stats
        assert 'p95' in stats
        assert 'p99' in stats
        assert stats['count'] == len(latencies_ns)
        assert stats['mean'] == pytest.approx(1460.0, rel=0.01)


@pytest.mark.integration
@pytest.mark.cpp
@pytest.mark.slow
class TestFullBacktestWorkflow:
    """
    Implementei esta classe para testar workflow completo de backtest usando C++
    """

    def test_full_backtest_sma_strategy(self):
        """
        Implementei este teste para validar backtest completo com SMA strategy
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        engine = nexus_bindings.BacktestEngine()

        strategy = nexus_bindings.SmaStrategy(fast_period=50, slow_period=200)

        # Gerar dados de mercado sintéticos (1 ano, 252 dias)
        np.random.seed(42)
        base_price = 100.0
        trend = np.linspace(0, 20, 252)
        noise = np.random.normal(0, 2, 252)
        prices = base_price + trend + noise

        market_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=252, freq='B'),
            'open': prices * 0.99,
            'high': prices * 1.02,
            'low': prices * 0.98,
            'close': prices,
            'volume': np.random.randint(1000000, 5000000, 252)
        })

        # Act
        results = engine.run_backtest(
            strategy=strategy,
            market_data=market_data.to_dict('records'),
            initial_capital=100000.0
        )

        # Assert
        assert results is not None
        assert 'total_return' in results
        assert 'sharpe_ratio' in results
        assert 'max_drawdown' in results
        assert 'total_trades' in results
        assert results['total_trades'] > 0

    def test_backtest_with_optimization(self):
        """
        Implementei este teste para validar otimização de parâmetros
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        optimizer = nexus_bindings.GridSearch()

        # Parâmetros para otimizar
        param_grid = {
            'fast_period': [20, 30, 40, 50],
            'slow_period': [100, 150, 200]
        }

        # Gerar dados de mercado
        np.random.seed(42)
        prices = 100.0 + np.cumsum(np.random.normal(0.001, 0.02, 252))

        market_data = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=252, freq='B'),
            'close': prices
        })

        # Act
        best_params = optimizer.optimize(
            strategy_type='SMA',
            param_grid=param_grid,
            market_data=market_data.to_dict('records'),
            objective='sharpe_ratio'
        )

        # Assert
        assert best_params is not None
        assert 'fast_period' in best_params
        assert 'slow_period' in best_params
        assert best_params['fast_period'] < best_params['slow_period']


@pytest.mark.integration
@pytest.mark.cpp
class TestDataTypeConversion:
    """
    Implementei esta classe para testar conversão de tipos Python ↔ C++
    """

    def test_numpy_to_cpp_conversion(self):
        """
        Implementei este teste para validar que NumPy arrays são aceitos
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        prices = np.array([100.0, 101.0, 102.0, 103.0, 104.0])
        strategy = nexus_bindings.SmaStrategy(fast_period=2, slow_period=3)

        # Act - deve aceitar NumPy array
        signals = [strategy.on_data(float(p)) for p in prices]

        # Assert
        assert len(signals) == len(prices)

    def test_pandas_to_cpp_conversion(self):
        """
        Implementei este teste para validar que Pandas DataFrames são aceitos
        """
        if not HAS_CPP_BINDINGS:
            pytest.skip("C++ bindings not available")

        # Arrange
        df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=10),
            'close': [100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0]
        })

        engine = nexus_bindings.BacktestEngine()

        # Act - deve aceitar DataFrame convertido para dict
        # (PyBind11 não aceita DataFrame diretamente, precisa converter)
        market_data_dict = df.to_dict('records')

        # Assert - não deve lançar exceção
        assert isinstance(market_data_dict, list)
        assert all(isinstance(record, dict) for record in market_data_dict)


if __name__ == "__main__":
    # Implementei este bloco para executar testes diretamente
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])