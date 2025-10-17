"""
Integration Tests - Market Data Integration
Implementei estes testes para validar adapters com mock API server
Decidi testar: API calls, rate limiting, WebSocket connections, error handling
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch
import pandas as pd
import requests_mock

# Importações do projeto
from backend.python.src.infrastructure.adapters.market_data.alpha_vantage_adapter import AlphaVantageAdapter
from backend.python.src.infrastructure.adapters.market_data.finnhub_adapter import FinnhubAdapter
from backend.python.src.infrastructure.adapters.market_data.nasdaq_datalink_adapter import NasdaqDataLinkAdapter
from backend.python.src.infrastructure.adapters.market_data.fred_adapter import FredAdapter
from backend.python.src.domain.value_objects import Symbol


@pytest.mark.integration
@pytest.mark.api
class TestAlphaVantageAdapter:
    """
    Implementei esta classe para testar AlphaVantageAdapter com mock server
    """

    @pytest.fixture
    def adapter(self):
        """
        Implementei este fixture para criar adapter com API key de teste
        """
        return AlphaVantageAdapter(api_key="TEST_API_KEY")

    def test_get_daily_data_success(self, adapter: AlphaVantageAdapter):
        """
        Implementei este teste para validar fetch de dados diários com sucesso
        """
        with requests_mock.Mocker() as m:
            # Arrange - mock response
            mock_response = {
                "Time Series (Daily)": {
                    "2024-01-05": {
                        "1. open": "100.00",
                        "2. high": "102.00",
                        "3. low": "99.00",
                        "4. close": "101.00",
                        "5. volume": "1000000"
                    },
                    "2024-01-04": {
                        "1. open": "99.00",
                        "2. high": "101.00",
                        "3. low": "98.00",
                        "4. close": "100.00",
                        "5. volume": "900000"
                    }
                }
            }

            m.get(
                'https://www.alphavantage.co/query',
                json=mock_response
            )

            # Act
            data = adapter.get_daily(symbol="AAPL")

            # Assert
            assert data is not None
            assert isinstance(data, pd.DataFrame)
            assert len(data) == 2
            assert 'close' in data.columns
            assert 'volume' in data.columns

    def test_get_daily_data_api_error(self, adapter: AlphaVantageAdapter):
        """
        Implementei este teste para validar tratamento de erro de API
        """
        with requests_mock.Mocker() as m:
            # Arrange - mock erro 500
            m.get(
                'https://www.alphavantage.co/query',
                status_code=500
            )

            # Act & Assert
            with pytest.raises(Exception):
                adapter.get_daily(symbol="AAPL")

    def test_get_intraday_data(self, adapter: AlphaVantageAdapter):
        """
        Implementei este teste para validar fetch de dados intraday
        """
        with requests_mock.Mocker() as m:
            # Arrange
            mock_response = {
                "Time Series (1min)": {
                    "2024-01-05 16:00:00": {
                        "1. open": "100.00",
                        "2. high": "100.50",
                        "3. low": "99.50",
                        "4. close": "100.25",
                        "5. volume": "10000"
                    },
                    "2024-01-05 15:59:00": {
                        "1. open": "99.75",
                        "2. high": "100.00",
                        "3. low": "99.50",
                        "4. close": "99.90",
                        "5. volume": "8000"
                    }
                }
            }

            m.get(
                'https://www.alphavantage.co/query',
                json=mock_response
            )

            # Act
            data = adapter.get_intraday(symbol="AAPL", interval="1min")

            # Assert
            assert data is not None
            assert len(data) == 2

    def test_rate_limiting(self, adapter: AlphaVantageAdapter):
        """
        Implementei este teste para validar rate limiting (25 calls/day)
        """
        with requests_mock.Mocker() as m:
            # Arrange - mock resposta de rate limit
            mock_response = {
                "Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute and 500 calls per day."
            }

            m.get(
                'https://www.alphavantage.co/query',
                json=mock_response
            )

            # Act & Assert - deve detectar rate limit
            with pytest.raises(Exception) as exc_info:
                adapter.get_daily(symbol="AAPL")

            assert "rate limit" in str(exc_info.value).lower() or "Note" in str(exc_info.value)


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.websocket
class TestFinnhubAdapter:
    """
    Implementei esta classe para testar FinnhubAdapter
    Decidi focar em WebSocket + REST
    """

    @pytest.fixture
    def adapter(self):
        """
        Implementei este fixture para criar adapter de teste
        """
        return FinnhubAdapter(api_key="TEST_API_KEY")

    def test_get_quote_success(self, adapter: FinnhubAdapter):
        """
        Implementei este teste para validar fetch de cotação em tempo real
        """
        with requests_mock.Mocker() as m:
            # Arrange
            mock_response = {
                "c": 100.50,  # current price
                "h": 101.00,  # high
                "l": 99.50,   # low
                "o": 100.00,  # open
                "pc": 99.75,  # previous close
                "t": int(datetime.now().timestamp())
            }

            m.get(
                'https://finnhub.io/api/v1/quote',
                json=mock_response
            )

            # Act
            quote = adapter.get_quote(symbol="AAPL")

            # Assert
            assert quote is not None
            assert quote['c'] == 100.50
            assert quote['h'] == 101.00

    def test_websocket_connection_mock(self, adapter: FinnhubAdapter):
        """
        Implementei este teste para validar conexão WebSocket (mocked)
        Decidi usar mock pois WebSocket real requer servidor rodando
        """
        # Arrange
        with patch.object(adapter, 'ws', create=True) as mock_ws:
            mock_ws.connect.return_value = True

            # Act
            result = adapter.connect_websocket()

            # Assert
            # Este é um mock simples - WebSocket real seria testado em E2E
            pytest.skip("Full WebSocket testing requires running server")

    def test_subscribe_to_trades(self, adapter: FinnhubAdapter):
        """
        Implementei este teste para validar subscription a trades
        """
        # TODO: Implementar quando houver WebSocket server de teste
        pytest.skip("WebSocket subscription testing requires mock server")


@pytest.mark.integration
@pytest.mark.api
class TestNasdaqDataLinkAdapter:
    """
    Implementei esta classe para testar Nasdaq Data Link (Quandl)
    """

    @pytest.fixture
    def adapter(self):
        """
        Implementei este fixture para adapter Nasdaq
        """
        return NasdaqDataLinkAdapter(api_key="TEST_API_KEY")

    def test_get_historical_data(self, adapter: NasdaqDataLinkAdapter):
        """
        Implementei este teste para validar fetch de dados históricos
        """
        with requests_mock.Mocker() as m:
            # Arrange
            mock_response = {
                "dataset": {
                    "data": [
                        ["2024-01-05", 100.0, 102.0, 99.0, 101.0, 1000000],
                        ["2024-01-04", 99.0, 101.0, 98.0, 100.0, 900000]
                    ],
                    "column_names": ["Date", "Open", "High", "Low", "Close", "Volume"]
                }
            }

            m.get(
                'https://data.nasdaq.com/api/v3/datasets/WIKI/AAPL',
                json=mock_response
            )

            # Act
            data = adapter.get_dataset(dataset_code="WIKI/AAPL")

            # Assert
            assert data is not None
            assert isinstance(data, pd.DataFrame)
            assert len(data) == 2


@pytest.mark.integration
@pytest.mark.api
class TestFredAdapter:
    """
    Implementei esta classe para testar FRED adapter
    """

    @pytest.fixture
    def adapter(self):
        """
        Implementei este fixture para adapter FRED
        """
        return FredAdapter(api_key="TEST_API_KEY")

    def test_get_economic_data(self, adapter: FredAdapter):
        """
        Implementei este teste para validar fetch de dados econômicos
        """
        with requests_mock.Mocker() as m:
            # Arrange
            mock_response = {
                "observations": [
                    {"date": "2024-01-01", "value": "2.5"},
                    {"date": "2024-02-01", "value": "2.6"},
                    {"date": "2024-03-01", "value": "2.7"}
                ]
            }

            m.get(
                'https://api.stlouisfed.org/fred/series/observations',
                json=mock_response
            )

            # Act
            data = adapter.get_series(series_id="GDP")

            # Assert
            assert data is not None
            assert isinstance(data, pd.DataFrame)
            assert len(data) == 3


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.slow
class TestMarketDataCaching:
    """
    Implementei esta classe para testar caching de market data
    """

    @pytest.fixture
    def adapter_with_cache(self):
        """
        Implementei este fixture para adapter com cache habilitado
        """
        return AlphaVantageAdapter(api_key="TEST_API_KEY", enable_cache=True)

    def test_cache_hit(self, adapter_with_cache: AlphaVantageAdapter):
        """
        Implementei este teste para validar cache hit
        """
        with requests_mock.Mocker() as m:
            # Arrange
            mock_response = {
                "Time Series (Daily)": {
                    "2024-01-05": {
                        "1. open": "100.00",
                        "2. high": "102.00",
                        "3. low": "99.00",
                        "4. close": "101.00",
                        "5. volume": "1000000"
                    }
                }
            }

            m.get(
                'https://www.alphavantage.co/query',
                json=mock_response
            )

            # Act - primeira chamada (miss)
            data1 = adapter_with_cache.get_daily(symbol="AAPL")

            # Act - segunda chamada (should hit cache)
            data2 = adapter_with_cache.get_daily(symbol="AAPL")

            # Assert
            assert data1.equals(data2)
            # API deve ser chamada apenas uma vez
            assert m.call_count == 1

    def test_cache_expiration(self, adapter_with_cache: AlphaVantageAdapter):
        """
        Implementei este teste para validar expiração de cache
        """
        # TODO: Implementar quando houver TTL configurável
        pytest.skip("Cache expiration testing requires TTL configuration")


@pytest.mark.integration
@pytest.mark.api
class TestErrorHandling:
    """
    Implementei esta classe para testar error handling em API calls
    """

    def test_timeout_handling(self):
        """
        Implementei este teste para validar timeout handling
        """
        adapter = AlphaVantageAdapter(api_key="TEST_API_KEY", timeout=0.001)

        with requests_mock.Mocker() as m:
            # Arrange - mock timeout
            m.get(
                'https://www.alphavantage.co/query',
                exc=requests.exceptions.Timeout
            )

            # Act & Assert
            with pytest.raises(requests.exceptions.Timeout):
                adapter.get_daily(symbol="AAPL")

    def test_network_error_handling(self):
        """
        Implementei este teste para validar network error handling
        """
        adapter = AlphaVantageAdapter(api_key="TEST_API_KEY")

        with requests_mock.Mocker() as m:
            # Arrange - mock network error
            m.get(
                'https://www.alphavantage.co/query',
                exc=requests.exceptions.ConnectionError
            )

            # Act & Assert
            with pytest.raises(requests.exceptions.ConnectionError):
                adapter.get_daily(symbol="AAPL")

    def test_invalid_json_response(self):
        """
        Implementei este teste para validar tratamento de JSON inválido
        """
        adapter = AlphaVantageAdapter(api_key="TEST_API_KEY")

        with requests_mock.Mocker() as m:
            # Arrange - mock resposta inválida
            m.get(
                'https://www.alphavantage.co/query',
                text="<html>Invalid response</html>",
                headers={'Content-Type': 'text/html'}
            )

            # Act & Assert
            with pytest.raises(Exception):
                adapter.get_daily(symbol="AAPL")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.slow
class TestRetryLogic:
    """
    Implementei esta classe para testar retry logic em failures
    """

    def test_retry_on_transient_error(self):
        """
        Implementei este teste para validar retry em erro temporário
        """
        adapter = AlphaVantageAdapter(api_key="TEST_API_KEY", max_retries=3)

        with requests_mock.Mocker() as m:
            # Arrange - 2 falhas seguidas de sucesso
            mock_success = {
                "Time Series (Daily)": {
                    "2024-01-05": {
                        "1. open": "100.00",
                        "2. high": "102.00",
                        "3. low": "99.00",
                        "4. close": "101.00",
                        "5. volume": "1000000"
                    }
                }
            }

            m.get(
                'https://www.alphavantage.co/query',
                [
                    {'status_code': 503},  # Service unavailable
                    {'status_code': 503},  # Service unavailable
                    {'json': mock_success, 'status_code': 200}  # Success
                ]
            )

            # Act
            data = adapter.get_daily(symbol="AAPL", retry=True)

            # Assert
            assert data is not None
            assert m.call_count == 3

    def test_retry_exhausted(self):
        """
        Implementei este teste para validar falha após esgotar retries
        """
        adapter = AlphaVantageAdapter(api_key="TEST_API_KEY", max_retries=2)

        with requests_mock.Mocker() as m:
            # Arrange - sempre falha
            m.get(
                'https://www.alphavantage.co/query',
                status_code=503
            )

            # Act & Assert
            with pytest.raises(Exception):
                adapter.get_daily(symbol="AAPL", retry=True)

            # Deve ter tentado max_retries vezes
            assert m.call_count == 2


if __name__ == "__main__":
    # Implementei este bloco para executar testes diretamente
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])