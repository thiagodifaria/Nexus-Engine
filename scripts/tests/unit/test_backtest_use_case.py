"""
Unit Tests - Backtest Use Case
Implementei estes testes para validar o BacktestUseCase com workflow completo
Decidi testar: execute, validation, C++ engine interaction, result persistence
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock, call
from uuid import uuid4, UUID
import pandas as pd
import numpy as np

# Importações do projeto
from backend.python.src.application.use_cases.backtest_use_case import BacktestUseCase
from backend.python.src.domain.entities.strategy import Strategy, StrategyType
from backend.python.src.domain.entities.backtest import Backtest, BacktestStatus
from backend.python.src.domain.repositories.strategy_repository import IStrategyRepository
from backend.python.src.domain.repositories.backtest_repository import IBacktestRepository
from backend.python.src.infrastructure.adapters.market_data.alpha_vantage_adapter import AlphaVantageAdapter
from backend.python.src.domain.value_objects import Symbol, TimeRange, StrategyParameters


class TestBacktestUseCase:
    """
    Implementei esta classe para testar BacktestUseCase end-to-end
    Decidi mockar repositories e C++ engine
    """

    @pytest.fixture
    def mock_strategy_repository(self) -> Mock:
        """
        Implementei este fixture para mockar strategy repository
        """
        mock = Mock(spec=IStrategyRepository)

        sample_strategy = Strategy(
            id=uuid4(),
            name="SMA Crossover 50/200",
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

        mock.get_by_id.return_value = sample_strategy
        return mock

    @pytest.fixture
    def mock_backtest_repository(self) -> Mock:
        """
        Implementei este fixture para mockar backtest repository
        """
        mock = Mock(spec=IBacktestRepository)

        sample_backtest = Backtest(
            id=uuid4(),
            strategy_id=uuid4(),
            symbol=Symbol(value="AAPL"),
            time_range=TimeRange(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31)
            ),
            status=BacktestStatus.COMPLETED,
            created_at=datetime.now()
        )

        mock.create.return_value = sample_backtest
        mock.get_by_id.return_value = sample_backtest
        mock.update.return_value = sample_backtest
        return mock

    @pytest.fixture
    def mock_market_data_adapter(self) -> Mock:
        """
        Implementei este fixture para mockar market data adapter
        """
        mock = Mock(spec=AlphaVantageAdapter)

        # Mock retorna dados de mercado realistas
        mock.get_daily.return_value = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=252, freq='B'),  # 252 trading days
            'open': np.random.uniform(100, 110, 252),
            'high': np.random.uniform(105, 115, 252),
            'low': np.random.uniform(95, 105, 252),
            'close': np.random.uniform(100, 110, 252),
            'volume': np.random.randint(1000000, 5000000, 252)
        })

        return mock

    @pytest.fixture
    def mock_cpp_engine(self) -> Mock:
        """
        Implementei este fixture para mockar C++ engine bindings
        """
        mock = Mock()

        # Mock de resultados do backtest
        mock.run_backtest.return_value = {
            'total_return': 0.15,
            'sharpe_ratio': 1.5,
            'max_drawdown': -0.12,
            'win_rate': 0.60,
            'total_trades': 50,
            'profitable_trades': 30,
            'losing_trades': 20,
            'avg_trade_return': 0.003,
            'avg_profit': 0.008,
            'avg_loss': -0.005,
            'execution_time_ns': 1500000  # 1.5ms
        }

        return mock

    @pytest.fixture
    def use_case(
        self,
        mock_strategy_repository: Mock,
        mock_backtest_repository: Mock,
        mock_market_data_adapter: Mock,
        mock_cpp_engine: Mock
    ) -> BacktestUseCase:
        """
        Implementei este fixture para criar use case com todos os mocks
        """
        return BacktestUseCase(
            strategy_repository=mock_strategy_repository,
            backtest_repository=mock_backtest_repository,
            market_data_adapter=mock_market_data_adapter,
            cpp_engine=mock_cpp_engine
        )

    def test_execute_backtest_success(
        self,
        use_case: BacktestUseCase,
        mock_strategy_repository: Mock,
        mock_backtest_repository: Mock,
        mock_market_data_adapter: Mock,
        mock_cpp_engine: Mock
    ):
        """
        Implementei este teste para validar execução completa de backtest com sucesso
        """
        # Arrange
        strategy_id = uuid4()
        symbol = Symbol(value="AAPL")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        # Act
        result = use_case.execute(
            strategy_id=strategy_id,
            symbol=symbol,
            time_range=time_range
        )

        # Assert
        assert result is not None
        assert result.status == BacktestStatus.COMPLETED

        # Verificar que todos os componentes foram chamados corretamente
        mock_strategy_repository.get_by_id.assert_called_once_with(strategy_id)
        mock_market_data_adapter.get_daily.assert_called_once_with("AAPL")
        mock_cpp_engine.run_backtest.assert_called_once()
        mock_backtest_repository.create.assert_called_once()
        mock_backtest_repository.update.assert_called()

    def test_execute_backtest_strategy_not_found(
        self,
        use_case: BacktestUseCase,
        mock_strategy_repository: Mock
    ):
        """
        Implementei este teste para validar falha quando estratégia não existe
        """
        # Arrange
        strategy_id = uuid4()
        mock_strategy_repository.get_by_id.return_value = None

        symbol = Symbol(value="AAPL")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                strategy_id=strategy_id,
                symbol=symbol,
                time_range=time_range
            )

        assert "Strategy not found" in str(exc_info.value)

    def test_execute_backtest_invalid_time_range(
        self,
        use_case: BacktestUseCase
    ):
        """
        Implementei este teste para validar rejeição de time range inválido
        """
        # Arrange
        strategy_id = uuid4()
        symbol = Symbol(value="AAPL")

        # Time range inválido: end antes de start
        invalid_time_range = TimeRange(
            start_date=datetime(2024, 12, 31),
            end_date=datetime(2024, 1, 1)
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                strategy_id=strategy_id,
                symbol=symbol,
                time_range=invalid_time_range
            )

        assert "End date must be after start date" in str(exc_info.value)

    def test_execute_backtest_no_market_data(
        self,
        use_case: BacktestUseCase,
        mock_market_data_adapter: Mock
    ):
        """
        Implementei este teste para validar falha quando não há dados de mercado
        """
        # Arrange
        strategy_id = uuid4()
        symbol = Symbol(value="INVALID")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        # Mock retorna DataFrame vazio
        mock_market_data_adapter.get_daily.return_value = pd.DataFrame()

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            use_case.execute(
                strategy_id=strategy_id,
                symbol=symbol,
                time_range=time_range
            )

        assert "No market data available" in str(exc_info.value)

    def test_execute_backtest_cpp_engine_failure(
        self,
        use_case: BacktestUseCase,
        mock_cpp_engine: Mock,
        mock_backtest_repository: Mock
    ):
        """
        Implementei este teste para validar tratamento de erro no C++ engine
        """
        # Arrange
        strategy_id = uuid4()
        symbol = Symbol(value="AAPL")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        # Mock C++ engine lança exceção
        mock_cpp_engine.run_backtest.side_effect = RuntimeError("C++ engine crashed")

        # Act & Assert
        with pytest.raises(RuntimeError) as exc_info:
            use_case.execute(
                strategy_id=strategy_id,
                symbol=symbol,
                time_range=time_range
            )

        assert "C++ engine crashed" in str(exc_info.value)

        # Verificar que backtest foi marcado como FAILED
        update_calls = mock_backtest_repository.update.call_args_list
        assert any(
            call_args[0][0].status == BacktestStatus.FAILED
            for call_args in update_calls
        )

    def test_backtest_status_progression(
        self,
        use_case: BacktestUseCase,
        mock_backtest_repository: Mock
    ):
        """
        Implementei este teste para validar progressão correta de status do backtest
        Decidi que deve ser: PENDING → RUNNING → COMPLETED
        """
        # Arrange
        strategy_id = uuid4()
        symbol = Symbol(value="AAPL")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        # Act
        use_case.execute(
            strategy_id=strategy_id,
            symbol=symbol,
            time_range=time_range
        )

        # Assert - verificar sequência de updates
        update_calls = mock_backtest_repository.update.call_args_list
        statuses = [call_args[0][0].status for call_args in update_calls]

        expected_statuses = [
            BacktestStatus.RUNNING,
            BacktestStatus.COMPLETED
        ]

        assert statuses == expected_statuses

    def test_backtest_results_persistence(
        self,
        use_case: BacktestUseCase,
        mock_backtest_repository: Mock,
        mock_cpp_engine: Mock
    ):
        """
        Implementei este teste para validar que resultados são persistidos corretamente
        """
        # Arrange
        strategy_id = uuid4()
        symbol = Symbol(value="AAPL")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        expected_results = {
            'total_return': 0.15,
            'sharpe_ratio': 1.5,
            'max_drawdown': -0.12,
            'win_rate': 0.60
        }

        mock_cpp_engine.run_backtest.return_value = expected_results

        # Act
        result = use_case.execute(
            strategy_id=strategy_id,
            symbol=symbol,
            time_range=time_range
        )

        # Assert - verificar que update foi chamado com resultados corretos
        final_update_call = mock_backtest_repository.update.call_args_list[-1]
        updated_backtest = final_update_call[0][0]

        assert updated_backtest.results['total_return'] == 0.15
        assert updated_backtest.results['sharpe_ratio'] == 1.5
        assert updated_backtest.results['max_drawdown'] == -0.12

    def test_get_backtest_by_id(
        self,
        use_case: BacktestUseCase,
        mock_backtest_repository: Mock
    ):
        """
        Implementei este teste para validar busca de backtest por ID
        """
        # Arrange
        backtest_id = uuid4()

        # Act
        result = use_case.get_backtest(backtest_id)

        # Assert
        assert result is not None
        mock_backtest_repository.get_by_id.assert_called_once_with(backtest_id)

    def test_list_backtests_by_strategy(
        self,
        use_case: BacktestUseCase,
        mock_backtest_repository: Mock
    ):
        """
        Implementei este teste para validar listagem de backtests por estratégia
        """
        # Arrange
        strategy_id = uuid4()

        mock_backtests = [
            Backtest(
                id=uuid4(),
                strategy_id=strategy_id,
                symbol=Symbol(value="AAPL"),
                time_range=TimeRange(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 12, 31)
                ),
                status=BacktestStatus.COMPLETED,
                created_at=datetime.now()
            ),
            Backtest(
                id=uuid4(),
                strategy_id=strategy_id,
                symbol=Symbol(value="GOOGL"),
                time_range=TimeRange(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 12, 31)
                ),
                status=BacktestStatus.COMPLETED,
                created_at=datetime.now()
            )
        ]

        mock_backtest_repository.list_by_strategy.return_value = mock_backtests

        # Act
        result = use_case.list_backtests(strategy_id=strategy_id)

        # Assert
        assert len(result) == 2
        assert all(bt.strategy_id == strategy_id for bt in result)
        mock_backtest_repository.list_by_strategy.assert_called_once_with(strategy_id)

    def test_delete_backtest(
        self,
        use_case: BacktestUseCase,
        mock_backtest_repository: Mock
    ):
        """
        Implementei este teste para validar deleção de backtest
        """
        # Arrange
        backtest_id = uuid4()
        mock_backtest_repository.delete.return_value = True

        # Act
        result = use_case.delete_backtest(backtest_id)

        # Assert
        assert result is True
        mock_backtest_repository.delete.assert_called_once_with(backtest_id)

    def test_cancel_running_backtest(
        self,
        use_case: BacktestUseCase,
        mock_backtest_repository: Mock,
        mock_cpp_engine: Mock
    ):
        """
        Implementei este teste para validar cancelamento de backtest em execução
        """
        # Arrange
        backtest_id = uuid4()

        running_backtest = Backtest(
            id=backtest_id,
            strategy_id=uuid4(),
            symbol=Symbol(value="AAPL"),
            time_range=TimeRange(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31)
            ),
            status=BacktestStatus.RUNNING,
            created_at=datetime.now()
        )

        mock_backtest_repository.get_by_id.return_value = running_backtest

        # Act
        result = use_case.cancel_backtest(backtest_id)

        # Assert
        assert result is True
        mock_cpp_engine.cancel_backtest.assert_called_once_with(backtest_id)
        mock_backtest_repository.update.assert_called_once()

        # Verificar que status foi atualizado para CANCELLED
        updated_backtest = mock_backtest_repository.update.call_args[0][0]
        assert updated_backtest.status == BacktestStatus.CANCELLED

    def test_backtest_performance_metrics_calculation(
        self,
        use_case: BacktestUseCase,
        mock_cpp_engine: Mock
    ):
        """
        Implementei este teste para validar cálculo correto de métricas de performance
        """
        # Arrange
        strategy_id = uuid4()
        symbol = Symbol(value="AAPL")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        # Mock retorna métricas detalhadas
        detailed_results = {
            'total_return': 0.15,
            'sharpe_ratio': 1.5,
            'sortino_ratio': 1.8,
            'max_drawdown': -0.12,
            'calmar_ratio': 1.25,
            'win_rate': 0.60,
            'profit_factor': 1.6,
            'total_trades': 50,
            'avg_trade_duration_days': 5.5
        }

        mock_cpp_engine.run_backtest.return_value = detailed_results

        # Act
        result = use_case.execute(
            strategy_id=strategy_id,
            symbol=symbol,
            time_range=time_range
        )

        # Assert
        assert result.results['sharpe_ratio'] == 1.5
        assert result.results['sortino_ratio'] == 1.8
        assert result.results['profit_factor'] == 1.6

    def test_backtest_with_multiple_symbols(
        self,
        use_case: BacktestUseCase,
        mock_market_data_adapter: Mock,
        mock_cpp_engine: Mock
    ):
        """
        Implementei este teste para validar backtest com múltiplos símbolos
        """
        # Arrange
        strategy_id = uuid4()
        symbols = [Symbol(value="AAPL"), Symbol(value="GOOGL"), Symbol(value="MSFT")]
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31)
        )

        # Act
        results = use_case.execute_batch(
            strategy_id=strategy_id,
            symbols=symbols,
            time_range=time_range
        )

        # Assert
        assert len(results) == 3
        assert mock_market_data_adapter.get_daily.call_count == 3
        assert mock_cpp_engine.run_backtest.call_count == 3


class TestBacktestValidation:
    """
    Implementei esta classe para testar validações específicas de backtest
    Decidi separar para melhor organização
    """

    def test_validate_sufficient_data_points(self):
        """
        Implementei este teste para validar que há dados suficientes
        Decidi que mínimo é 30 dias de dados
        """
        # Insufficient data
        insufficient_df = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=20),
            'close': np.random.uniform(100, 110, 20)
        })

        with pytest.raises(ValueError) as exc_info:
            BacktestUseCase.validate_market_data(insufficient_df, min_days=30)

        assert "Insufficient data points" in str(exc_info.value)

    def test_validate_no_missing_data(self):
        """
        Implementei este teste para validar ausência de dados faltantes
        """
        # Data with NaN
        df_with_nan = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=100),
            'close': [100.0] * 50 + [np.nan] * 50
        })

        with pytest.raises(ValueError) as exc_info:
            BacktestUseCase.validate_market_data(df_with_nan, allow_nan=False)

        assert "Missing data detected" in str(exc_info.value)


if __name__ == "__main__":
    # Implementei este bloco para executar testes diretamente
    pytest.main([__file__, "-v", "--tb=short"])