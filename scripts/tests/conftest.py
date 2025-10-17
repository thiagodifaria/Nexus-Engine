"""
Pytest Configuration and Fixtures
Implementei este arquivo para fornecer fixtures globais e configuração de testes
Decidi criar fixtures reutilizáveis para database, mock adapters, sample data
"""

import pytest
import os
import sys
from typing import Dict, Any, Generator
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, MagicMock
import pandas as pd
import numpy as np

# Add project root to path
# Implementei este bloco para garantir que imports funcionem
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importações do projeto
from backend.python.src.domain.entities.strategy import Strategy, StrategyType
from backend.python.src.domain.entities.backtest import Backtest, BacktestStatus
from backend.python.src.domain.value_objects import Symbol, TimeRange, StrategyParameters


# ============================================================================
# Configuration Hooks
# ============================================================================

def pytest_configure(config):
    """
    Implementei este hook para configurar ambiente de testes
    """
    # Set test environment
    os.environ['NEXUS_ENV'] = 'test'
    os.environ['NEXUS_LOG_LEVEL'] = 'DEBUG'

    # Register custom markers
    config.addinivalue_line(
        "markers", "unit: Unit tests with mocked dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests with real components"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests"
    )


def pytest_collection_modifyitems(config, items):
    """
    Implementei este hook para modificar items de teste coletados
    Decidi adicionar markers automaticamente baseado em paths
    """
    for item in items:
        # Add marker based on test path
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)

        # Add fast/slow marker based on test name
        if "slow" in item.name.lower():
            item.add_marker(pytest.mark.slow)
        else:
            item.add_marker(pytest.mark.fast)


# ============================================================================
# Session-scoped Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    Implementei este fixture para fornecer configuração de testes
    """
    return {
        'database_url': 'postgresql://test_user:test_pass@localhost:5433/nexus_test',
        'alpha_vantage_api_key': 'TEST_API_KEY_ALPHA_VANTAGE',
        'finnhub_api_key': 'TEST_API_KEY_FINNHUB',
        'prometheus_port': 9091,
        'log_level': 'DEBUG',
        'max_retries': 3,
        'timeout_seconds': 30
    }


@pytest.fixture(scope="session")
def sample_symbols() -> list[Symbol]:
    """
    Implementei este fixture para fornecer símbolos de teste
    """
    return [
        Symbol(value="AAPL"),
        Symbol(value="GOOGL"),
        Symbol(value="MSFT"),
        Symbol(value="TSLA"),
        Symbol(value="AMZN")
    ]


# ============================================================================
# Function-scoped Fixtures - Sample Data
# ============================================================================

@pytest.fixture
def sample_market_data() -> pd.DataFrame:
    """
    Implementei este fixture para fornecer dados de mercado realistas
    Decidi criar 252 dias de trading (1 ano)
    """
    dates = pd.date_range('2024-01-01', periods=252, freq='B')

    # Generate realistic price data with trend and noise
    base_price = 100.0
    trend = np.linspace(0, 10, 252)  # Uptrend
    noise = np.random.normal(0, 2, 252)
    close_prices = base_price + trend + noise

    df = pd.DataFrame({
        'timestamp': dates,
        'open': close_prices * np.random.uniform(0.98, 1.02, 252),
        'high': close_prices * np.random.uniform(1.01, 1.05, 252),
        'low': close_prices * np.random.uniform(0.95, 0.99, 252),
        'close': close_prices,
        'volume': np.random.randint(1000000, 5000000, 252)
    })

    return df


@pytest.fixture
def sample_intraday_data() -> pd.DataFrame:
    """
    Implementei este fixture para fornecer dados intraday (1 dia, 1min)
    """
    # 6.5 hours = 390 minutes (9:30 AM - 4:00 PM)
    timestamps = pd.date_range('2024-01-02 09:30', periods=390, freq='1min')

    base_price = 100.0
    noise = np.random.normal(0, 0.5, 390)
    close_prices = base_price + noise

    df = pd.DataFrame({
        'timestamp': timestamps,
        'open': close_prices * np.random.uniform(0.999, 1.001, 390),
        'high': close_prices * np.random.uniform(1.001, 1.003, 390),
        'low': close_prices * np.random.uniform(0.997, 0.999, 390),
        'close': close_prices,
        'volume': np.random.randint(1000, 10000, 390)
    })

    return df


@pytest.fixture
def sample_strategy() -> Strategy:
    """
    Implementei este fixture para fornecer estratégia de exemplo
    """
    return Strategy(
        id=uuid4(),
        name="Test SMA Crossover",
        strategy_type=StrategyType.SMA_CROSSOVER,
        parameters=StrategyParameters(
            params={
                "fast_period": 50,
                "slow_period": 200
            }
        ),
        is_active=True,
        created_at=datetime.now()
    )


@pytest.fixture
def sample_rsi_strategy() -> Strategy:
    """
    Implementei este fixture para fornecer estratégia RSI
    """
    return Strategy(
        id=uuid4(),
        name="Test RSI Strategy",
        strategy_type=StrategyType.RSI_STRATEGY,
        parameters=StrategyParameters(
            params={
                "period": 14,
                "oversold": 30,
                "overbought": 70
            }
        ),
        is_active=True,
        created_at=datetime.now()
    )


@pytest.fixture
def sample_backtest(sample_strategy: Strategy) -> Backtest:
    """
    Implementei este fixture para fornecer backtest de exemplo
    """
    return Backtest(
        id=uuid4(),
        strategy_id=sample_strategy.id,
        symbol=Symbol(value="AAPL"),
        time_range=TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        ),
        status=BacktestStatus.COMPLETED,
        results={
            'total_return': 0.15,
            'sharpe_ratio': 1.5,
            'max_drawdown': -0.12,
            'win_rate': 0.60,
            'total_trades': 50
        },
        created_at=datetime.now()
    )


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_alpha_vantage_adapter(sample_market_data: pd.DataFrame) -> Mock:
    """
    Implementei este fixture para mockar AlphaVantageAdapter
    """
    mock = Mock()
    mock.get_daily.return_value = sample_market_data
    mock.get_intraday.return_value = sample_market_data.head(100)
    return mock


@pytest.fixture
def mock_finnhub_adapter() -> Mock:
    """
    Implementei este fixture para mockar FinnhubAdapter
    """
    mock = Mock()
    mock.get_quote.return_value = {
        'c': 100.50,
        'h': 101.00,
        'l': 99.50,
        'o': 100.00,
        'pc': 99.75,
        't': int(datetime.now().timestamp())
    }
    mock.connect_websocket.return_value = True
    return mock


@pytest.fixture
def mock_strategy_repository(sample_strategy: Strategy) -> Mock:
    """
    Implementei este fixture para mockar StrategyRepository
    """
    mock = Mock()
    mock.create.return_value = sample_strategy
    mock.get_by_id.return_value = sample_strategy
    mock.list_all.return_value = [sample_strategy]
    mock.update.return_value = sample_strategy
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_backtest_repository(sample_backtest: Backtest) -> Mock:
    """
    Implementei este fixture para mockar BacktestRepository
    """
    mock = Mock()
    mock.create.return_value = sample_backtest
    mock.get_by_id.return_value = sample_backtest
    mock.list_all.return_value = [sample_backtest]
    mock.update.return_value = sample_backtest
    mock.delete.return_value = True
    return mock


@pytest.fixture
def mock_cpp_engine() -> Mock:
    """
    Implementei este fixture para mockar C++ Engine
    """
    mock = Mock()

    # Mock backtest results
    mock.run_backtest.return_value = {
        'total_return': 0.15,
        'sharpe_ratio': 1.5,
        'sortino_ratio': 1.8,
        'max_drawdown': -0.12,
        'calmar_ratio': 1.25,
        'win_rate': 0.60,
        'profit_factor': 1.6,
        'total_trades': 50,
        'profitable_trades': 30,
        'losing_trades': 20,
        'avg_trade_return': 0.003,
        'avg_profit': 0.008,
        'avg_loss': -0.005,
        'execution_time_ns': 1500000
    }

    # Mock strategy performance
    mock.calculate_indicators.return_value = {
        'sma_fast': [100, 101, 102],
        'sma_slow': [98, 99, 100],
        'signals': [0, 1, 0]  # 0=hold, 1=buy, -1=sell
    }

    return mock


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="function")
def test_database(test_config: Dict[str, Any]) -> Generator:
    """
    Implementei este fixture para fornecer database de teste isolado
    Decidi criar/dropar schema para cada teste
    """
    # TODO: Implementar setup de database de teste
    # from sqlalchemy import create_engine
    # from backend.python.src.infrastructure.database.session import Base

    # engine = create_engine(test_config['database_url'])
    # Base.metadata.create_all(engine)

    # yield engine

    # Base.metadata.drop_all(engine)
    # engine.dispose()

    pytest.skip("Database tests require PostgreSQL test instance")


# ============================================================================
# Utility Functions for Tests
# ============================================================================

def create_sample_trades(num_trades: int = 10) -> list[Dict[str, Any]]:
    """
    Implementei esta função helper para criar trades de exemplo
    """
    trades = []
    for i in range(num_trades):
        is_profitable = i % 3 != 0  # 66% win rate

        trade = {
            'id': uuid4(),
            'symbol': 'AAPL',
            'entry_time': datetime.now() - timedelta(days=10-i),
            'exit_time': datetime.now() - timedelta(days=9-i),
            'entry_price': 100.0 + i,
            'exit_price': (100.0 + i) * (1.05 if is_profitable else 0.98),
            'quantity': 100,
            'side': 'LONG',
            'pnl': 500.0 if is_profitable else -200.0
        }
        trades.append(trade)

    return trades


def assert_dataframe_equal(df1: pd.DataFrame, df2: pd.DataFrame, check_exact: bool = False):
    """
    Implementei esta função helper para comparar DataFrames em testes
    """
    pd.testing.assert_frame_equal(df1, df2, check_exact=check_exact)


# ============================================================================
# Performance Testing Utilities
# ============================================================================

@pytest.fixture
def performance_threshold():
    """
    Implementei este fixture para definir thresholds de performance
    """
    return {
        'backtest_execution_ms': 100,
        'strategy_calculation_ms': 10,
        'data_fetch_ms': 500,
        'database_query_ms': 50
    }


# ============================================================================
# Cleanup
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_after_test():
    """
    Implementei este fixture para limpar após cada teste
    """
    yield

    # Cleanup code here (if needed)
    # - Clear caches
    # - Reset singletons
    # - Close connections
    pass