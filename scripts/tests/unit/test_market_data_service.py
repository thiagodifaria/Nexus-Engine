"""
Unit Tests - Market Data Service
Implementei estes testes para validar o MarketDataService com mocks
Decidi testar: fetch_daily, fetch_intraday, retry logic, error handling
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

# Importações do projeto
from backend.python.src.infrastructure.adapters.market_data.alpha_vantage_adapter import AlphaVantageAdapter
from backend.python.src.infrastructure.adapters.market_data.finnhub_adapter import FinnhubAdapter
from backend.python.src.application.services.market_data_service import MarketDataService
from backend.python.src.domain.value_objects import Symbol, TimeRange


class TestMarketDataService:
    """
    Implementei esta classe de testes para validar MarketDataService
    Decidi usar mocks para evitar chamadas reais de API
    """

    @pytest.fixture
    def mock_alpha_vantage(self) -> Mock:
        """
        Implementei este fixture para mockar AlphaVantageAdapter
        Decidi retornar DataFrames realistas
        """
        mock = Mock(spec=AlphaVantageAdapter)

        # Mock para dados diários
        mock.get_daily.return_value = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5),
            'open': [100.0, 101.0, 102.0, 103.0, 104.0],
            'high': [102.0, 103.0, 104.0, 105.0, 106.0],
            'low': [99.0, 100.0, 101.0, 102.0, 103.0],
            'close': [101.0, 102.0, 103.0, 104.0, 105.0],
            'volume': [1000000, 1100000, 1200000, 1300000, 1400000]
        })

        # Mock para dados intraday
        mock.get_intraday.return_value = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01 09:30', periods=10, freq='1min'),
            'open': [100.0] * 10,
            'high': [101.0] * 10,
            'low': [99.0] * 10,
            'close': [100.5] * 10,
            'volume': [10000] * 10
        })

        return mock

    @pytest.fixture
    def mock_finnhub(self) -> Mock:
        """
        Implementei este fixture para mockar FinnhubAdapter
        """
        mock = Mock(spec=FinnhubAdapter)

        # Mock para real-time quote
        mock.get_quote.return_value = {
            'c': 100.50,  # current price
            'h': 101.00,  # high
            'l': 99.50,   # low
            'o': 100.00,  # open
            'pc': 99.75,  # previous close
            't': int(datetime.now().timestamp())
        }

        return mock

    @pytest.fixture
    def service(self, mock_alpha_vantage: Mock, mock_finnhub: Mock) -> MarketDataService:
        """
        Implementei este fixture para criar serviço com mocks injetados
        """
        return MarketDataService(
            alpha_vantage=mock_alpha_vantage,
            finnhub=mock_finnhub
        )

    def test_fetch_daily_data_success(self, service: MarketDataService, mock_alpha_vantage: Mock):
        """
        Implementei este teste para validar fetch de dados diários com sucesso
        """
        # Arrange
        symbol = Symbol(value="AAPL")
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 1, 5)
        time_range = TimeRange(start_date=start_date, end_date=end_date)

        # Act
        result = service.fetch_daily_data(symbol, time_range)

        # Assert
        assert result is not None
        assert len(result) == 5
        assert 'close' in result.columns
        assert 'volume' in result.columns
        mock_alpha_vantage.get_daily.assert_called_once_with("AAPL")

    def test_fetch_intraday_data_success(self, service: MarketDataService, mock_alpha_vantage: Mock):
        """
        Implementei este teste para validar fetch de dados intraday
        """
        # Arrange
        symbol = Symbol(value="AAPL")
        start_date = datetime(2024, 1, 1, 9, 30)
        end_date = datetime(2024, 1, 1, 16, 0)
        time_range = TimeRange(start_date=start_date, end_date=end_date)
        interval = "1min"

        # Act
        result = service.fetch_intraday_data(symbol, time_range, interval)

        # Assert
        assert result is not None
        assert len(result) == 10
        mock_alpha_vantage.get_intraday.assert_called_once_with("AAPL", interval)

    def test_fetch_real_time_quote_success(self, service: MarketDataService, mock_finnhub: Mock):
        """
        Implementei este teste para validar cotação em tempo real
        """
        # Arrange
        symbol = Symbol(value="AAPL")

        # Act
        result = service.fetch_real_time_quote(symbol)

        # Assert
        assert result is not None
        assert 'c' in result
        assert result['c'] == 100.50
        mock_finnhub.get_quote.assert_called_once_with("AAPL")

    def test_fetch_daily_data_with_retry(self, service: MarketDataService, mock_alpha_vantage: Mock):
        """
        Implementei este teste para validar retry logic em caso de falha temporária
        Decidi simular 2 falhas antes do sucesso
        """
        # Arrange
        symbol = Symbol(value="AAPL")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5)
        )

        # Mock com 2 falhas seguidas de sucesso
        mock_alpha_vantage.get_daily.side_effect = [
            Exception("API rate limit"),
            Exception("Network timeout"),
            pd.DataFrame({
                'timestamp': pd.date_range('2024-01-01', periods=5),
                'close': [100, 101, 102, 103, 104]
            })
        ]

        # Act
        result = service.fetch_daily_data(symbol, time_range, max_retries=3)

        # Assert
        assert result is not None
        assert len(result) == 5
        assert mock_alpha_vantage.get_daily.call_count == 3

    def test_fetch_daily_data_exceeds_max_retries(self, service: MarketDataService, mock_alpha_vantage: Mock):
        """
        Implementei este teste para validar falha após esgotar retries
        """
        # Arrange
        symbol = Symbol(value="AAPL")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5)
        )

        # Mock sempre falha
        mock_alpha_vantage.get_daily.side_effect = Exception("API error")

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            service.fetch_daily_data(symbol, time_range, max_retries=3)

        assert "API error" in str(exc_info.value)
        assert mock_alpha_vantage.get_daily.call_count == 3

    def test_fetch_multiple_symbols_batch(self, service: MarketDataService, mock_alpha_vantage: Mock):
        """
        Implementei este teste para validar fetch em lote de múltiplos símbolos
        """
        # Arrange
        symbols = [Symbol(value="AAPL"), Symbol(value="GOOGL"), Symbol(value="MSFT")]
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5)
        )

        # Act
        results = service.fetch_multiple_symbols(symbols, time_range)

        # Assert
        assert len(results) == 3
        assert "AAPL" in results
        assert "GOOGL" in results
        assert "MSFT" in results
        assert mock_alpha_vantage.get_daily.call_count == 3

    def test_invalid_symbol_format(self, service: MarketDataService):
        """
        Implementei este teste para validar rejeição de símbolo inválido
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            Symbol(value="")

        assert "Symbol cannot be empty" in str(exc_info.value)

    def test_invalid_time_range(self, service: MarketDataService):
        """
        Implementei este teste para validar rejeição de range inválido
        """
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            TimeRange(
                start_date=datetime(2024, 1, 10),
                end_date=datetime(2024, 1, 1)  # End before start
            )

        assert "End date must be after start date" in str(exc_info.value)

    def test_cache_behavior(self, service: MarketDataService, mock_alpha_vantage: Mock):
        """
        Implementei este teste para validar cache de dados
        Decidi verificar que chamadas repetidas usam cache
        """
        # Arrange
        symbol = Symbol(value="AAPL")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5)
        )

        # Act - primeira chamada
        result1 = service.fetch_daily_data(symbol, time_range, use_cache=True)

        # Act - segunda chamada (deve usar cache)
        result2 = service.fetch_daily_data(symbol, time_range, use_cache=True)

        # Assert
        assert result1.equals(result2)
        # API deve ser chamada apenas uma vez
        mock_alpha_vantage.get_daily.assert_called_once()

    def test_data_validation(self, service: MarketDataService, mock_alpha_vantage: Mock):
        """
        Implementei este teste para validar que dados inválidos são rejeitados
        """
        # Arrange
        symbol = Symbol(value="AAPL")
        time_range = TimeRange(
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 5)
        )

        # Mock retorna dados inválidos (preços negativos)
        mock_alpha_vantage.get_daily.return_value = pd.DataFrame({
            'timestamp': pd.date_range('2024-01-01', periods=5),
            'close': [-100, -101, -102, -103, -104]  # Preços negativos!
        })

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            service.fetch_daily_data(symbol, time_range, validate=True)

        assert "Invalid price data" in str(exc_info.value)


class TestMarketDataServiceIntegration:
    """
    Implementei estes testes de integração entre componentes
    Decidi testar fluxo completo sem mocks de infraestrutura
    """

    @pytest.fixture
    def integration_service(self) -> MarketDataService:
        """
        Implementei fixture com componentes reais (mas offline)
        """
        # TODO: Implementar quando houver mock server
        pytest.skip("Integration tests require mock API server")

    def test_full_workflow_daily_to_database(self, integration_service: MarketDataService):
        """
        Implementei teste de workflow completo: fetch → validate → save
        """
        # TODO: Implementar quando houver database de teste
        pytest.skip("Requires test database setup")


if __name__ == "__main__":
    # Implementei este bloco para executar testes diretamente
    pytest.main([__file__, "-v", "--tb=short"])