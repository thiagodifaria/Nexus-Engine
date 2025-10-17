"""
Unit Tests - Strategy Service
Implementei estes testes para validar o StrategyService com mocked repositories
Decidi testar: create, update, delete, list, parameter validation
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, patch, MagicMock
from uuid import uuid4

# Importações do projeto
from backend.python.src.domain.entities.strategy import Strategy, StrategyType
from backend.python.src.domain.repositories.strategy_repository import IStrategyRepository
from backend.python.src.application.services.strategy_service import StrategyService
from backend.python.src.domain.value_objects import StrategyParameters


class TestStrategyService:
    """
    Implementei esta classe para testar StrategyService
    Decidi mockar o repositório para isolamento total
    """

    @pytest.fixture
    def mock_repository(self) -> Mock:
        """
        Implementei este fixture para mockar IStrategyRepository
        """
        mock = Mock(spec=IStrategyRepository)

        # Mock de estratégia exemplo
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

        # Mock behaviors
        mock.create.return_value = sample_strategy
        mock.get_by_id.return_value = sample_strategy
        mock.list_all.return_value = [sample_strategy]
        mock.update.return_value = sample_strategy
        mock.delete.return_value = True

        return mock

    @pytest.fixture
    def service(self, mock_repository: Mock) -> StrategyService:
        """
        Implementei este fixture para criar serviço com repository mockado
        """
        return StrategyService(repository=mock_repository)

    def test_create_strategy_success(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar criação de estratégia com sucesso
        """
        # Arrange
        name = "RSI Mean Reversion"
        strategy_type = StrategyType.RSI_STRATEGY
        parameters = StrategyParameters(
            params={
                "period": 14,
                "oversold": 30,
                "overbought": 70
            }
        )

        # Act
        result = service.create_strategy(
            name=name,
            strategy_type=strategy_type,
            parameters=parameters
        )

        # Assert
        assert result is not None
        assert result.name == "SMA Crossover 50/200"  # Mock retorna sample
        mock_repository.create.assert_called_once()

    def test_create_strategy_invalid_parameters(self, service: StrategyService):
        """
        Implementei este teste para validar rejeição de parâmetros inválidos
        """
        # Arrange
        name = "Invalid Strategy"
        strategy_type = StrategyType.SMA_CROSSOVER

        # Parâmetros inválidos: fast > slow
        invalid_params = StrategyParameters(
            params={
                "fast_period": 200,
                "slow_period": 50  # Erro: slow deve ser > fast
            }
        )

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.create_strategy(
                name=name,
                strategy_type=strategy_type,
                parameters=invalid_params,
                validate=True
            )

        assert "fast_period must be less than slow_period" in str(exc_info.value)

    def test_get_strategy_by_id_success(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar busca de estratégia por ID
        """
        # Arrange
        strategy_id = uuid4()

        # Act
        result = service.get_strategy(strategy_id)

        # Assert
        assert result is not None
        assert result.name == "SMA Crossover 50/200"
        mock_repository.get_by_id.assert_called_once_with(strategy_id)

    def test_get_strategy_not_found(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar comportamento quando estratégia não existe
        """
        # Arrange
        strategy_id = uuid4()
        mock_repository.get_by_id.return_value = None

        # Act
        result = service.get_strategy(strategy_id)

        # Assert
        assert result is None
        mock_repository.get_by_id.assert_called_once_with(strategy_id)

    def test_list_all_strategies(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar listagem de todas as estratégias
        """
        # Act
        result = service.list_strategies()

        # Assert
        assert result is not None
        assert len(result) == 1
        assert result[0].name == "SMA Crossover 50/200"
        mock_repository.list_all.assert_called_once()

    def test_list_active_strategies_only(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar filtro de estratégias ativas
        """
        # Arrange
        active_strategy = Strategy(
            id=uuid4(),
            name="Active Strategy",
            strategy_type=StrategyType.RSI_STRATEGY,
            parameters=StrategyParameters(params={"period": 14}),
            is_active=True,
            created_at=datetime.now()
        )

        inactive_strategy = Strategy(
            id=uuid4(),
            name="Inactive Strategy",
            strategy_type=StrategyType.MACD_STRATEGY,
            parameters=StrategyParameters(params={"fast": 12}),
            is_active=False,
            created_at=datetime.now()
        )

        mock_repository.list_all.return_value = [active_strategy, inactive_strategy]

        # Act
        result = service.list_strategies(active_only=True)

        # Assert
        assert len(result) == 1
        assert result[0].name == "Active Strategy"
        assert result[0].is_active is True

    def test_update_strategy_success(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar atualização de estratégia
        """
        # Arrange
        strategy_id = uuid4()
        new_parameters = StrategyParameters(
            params={
                "fast_period": 20,
                "slow_period": 50
            }
        )

        # Act
        result = service.update_strategy(
            strategy_id=strategy_id,
            parameters=new_parameters
        )

        # Assert
        assert result is not None
        mock_repository.update.assert_called_once()

    def test_update_strategy_not_found(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar update de estratégia inexistente
        """
        # Arrange
        strategy_id = uuid4()
        mock_repository.get_by_id.return_value = None

        new_parameters = StrategyParameters(params={"fast_period": 20})

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.update_strategy(
                strategy_id=strategy_id,
                parameters=new_parameters
            )

        assert "Strategy not found" in str(exc_info.value)

    def test_delete_strategy_success(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar deleção de estratégia
        """
        # Arrange
        strategy_id = uuid4()

        # Act
        result = service.delete_strategy(strategy_id)

        # Assert
        assert result is True
        mock_repository.delete.assert_called_once_with(strategy_id)

    def test_delete_strategy_with_active_backtests(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar que não se pode deletar estratégia com backtests ativos
        """
        # Arrange
        strategy_id = uuid4()

        # Mock repositório indicando que há backtests ativos
        mock_repository.has_active_backtests.return_value = True

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.delete_strategy(strategy_id, force=False)

        assert "Cannot delete strategy with active backtests" in str(exc_info.value)
        mock_repository.delete.assert_not_called()

    def test_delete_strategy_force(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar deleção forçada mesmo com backtests
        """
        # Arrange
        strategy_id = uuid4()
        mock_repository.has_active_backtests.return_value = True

        # Act
        result = service.delete_strategy(strategy_id, force=True)

        # Assert
        assert result is True
        mock_repository.delete.assert_called_once_with(strategy_id)

    def test_activate_strategy(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar ativação de estratégia
        """
        # Arrange
        strategy_id = uuid4()

        # Act
        result = service.activate_strategy(strategy_id)

        # Assert
        assert result is not None
        mock_repository.update.assert_called_once()

    def test_deactivate_strategy(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar desativação de estratégia
        """
        # Arrange
        strategy_id = uuid4()

        # Act
        result = service.deactivate_strategy(strategy_id)

        # Assert
        assert result is not None
        mock_repository.update.assert_called_once()

    def test_validate_sma_crossover_parameters(self, service: StrategyService):
        """
        Implementei este teste para validar parâmetros específicos de SMA Crossover
        """
        # Valid parameters
        valid_params = StrategyParameters(
            params={
                "fast_period": 50,
                "slow_period": 200
            }
        )

        # Act & Assert - should not raise
        is_valid = service.validate_parameters(StrategyType.SMA_CROSSOVER, valid_params)
        assert is_valid is True

        # Invalid parameters (missing slow_period)
        invalid_params = StrategyParameters(
            params={
                "fast_period": 50
            }
        )

        # Act & Assert - should raise
        with pytest.raises(ValueError) as exc_info:
            service.validate_parameters(StrategyType.SMA_CROSSOVER, invalid_params)

        assert "Missing required parameter: slow_period" in str(exc_info.value)

    def test_validate_rsi_strategy_parameters(self, service: StrategyService):
        """
        Implementei este teste para validar parâmetros específicos de RSI Strategy
        """
        # Valid parameters
        valid_params = StrategyParameters(
            params={
                "period": 14,
                "oversold": 30,
                "overbought": 70
            }
        )

        # Act & Assert - should not raise
        is_valid = service.validate_parameters(StrategyType.RSI_STRATEGY, valid_params)
        assert is_valid is True

        # Invalid parameters (oversold > overbought)
        invalid_params = StrategyParameters(
            params={
                "period": 14,
                "oversold": 80,  # Erro!
                "overbought": 70
            }
        )

        # Act & Assert - should raise
        with pytest.raises(ValueError) as exc_info:
            service.validate_parameters(StrategyType.RSI_STRATEGY, invalid_params)

        assert "oversold must be less than overbought" in str(exc_info.value)

    def test_validate_macd_strategy_parameters(self, service: StrategyService):
        """
        Implementei este teste para validar parâmetros específicos de MACD Strategy
        """
        # Valid parameters
        valid_params = StrategyParameters(
            params={
                "fast_period": 12,
                "slow_period": 26,
                "signal_period": 9
            }
        )

        # Act & Assert - should not raise
        is_valid = service.validate_parameters(StrategyType.MACD_STRATEGY, valid_params)
        assert is_valid is True

    def test_clone_strategy(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar clonagem de estratégia
        Decidi que clone deve ter novo ID e nome "[Original] (Copy)"
        """
        # Arrange
        strategy_id = uuid4()

        # Mock retorna estratégia clonada
        cloned_strategy = Strategy(
            id=uuid4(),  # Novo ID
            name="SMA Crossover 50/200 (Copy)",
            strategy_type=StrategyType.SMA_CROSSOVER,
            parameters=StrategyParameters(params={"fast_period": 50, "slow_period": 200}),
            is_active=False,  # Clone começa inativo
            created_at=datetime.now()
        )
        mock_repository.clone.return_value = cloned_strategy

        # Act
        result = service.clone_strategy(strategy_id)

        # Assert
        assert result is not None
        assert "(Copy)" in result.name
        assert result.is_active is False
        mock_repository.clone.assert_called_once_with(strategy_id)

    def test_get_strategy_performance_stats(self, service: StrategyService, mock_repository: Mock):
        """
        Implementei este teste para validar estatísticas de performance
        """
        # Arrange
        strategy_id = uuid4()

        # Mock retorna estatísticas
        mock_stats = {
            "total_backtests": 10,
            "avg_return": 0.15,
            "win_rate": 0.60,
            "sharpe_ratio": 1.5,
            "max_drawdown": -0.12
        }
        mock_repository.get_performance_stats.return_value = mock_stats

        # Act
        result = service.get_performance_stats(strategy_id)

        # Assert
        assert result is not None
        assert result["total_backtests"] == 10
        assert result["avg_return"] == 0.15
        assert result["win_rate"] == 0.60
        mock_repository.get_performance_stats.assert_called_once_with(strategy_id)


class TestStrategyParameterValidation:
    """
    Implementei esta classe para testar validações detalhadas de parâmetros
    Decidi separar para melhor organização
    """

    def test_parameter_type_validation(self):
        """
        Implementei este teste para validar tipos de parâmetros
        """
        # Valid: all integers
        valid = StrategyParameters(
            params={
                "fast_period": 50,
                "slow_period": 200
            }
        )
        assert valid.params["fast_period"] == 50

        # Invalid: string instead of int
        with pytest.raises(ValueError):
            StrategyParameters(
                params={
                    "fast_period": "fifty"  # Should be int
                }
            )

    def test_parameter_range_validation(self):
        """
        Implementei este teste para validar ranges de valores
        """
        # Valid ranges
        valid = StrategyParameters(
            params={
                "period": 14,  # Valid: 2-200
                "oversold": 30,  # Valid: 0-100
                "overbought": 70  # Valid: 0-100
            }
        )

        # Invalid: period too small
        with pytest.raises(ValueError) as exc_info:
            StrategyParameters(
                params={"period": 1},  # Min is 2
                validation_rules={"period": {"min": 2, "max": 200}}
            )

        assert "period must be >= 2" in str(exc_info.value)


if __name__ == "__main__":
    # Implementei este bloco para executar testes diretamente
    pytest.main([__file__, "-v", "--tb=short"])