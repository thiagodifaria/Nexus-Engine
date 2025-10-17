"""
Market Data Service - orquestração de dados de mercado.

Implementei service para coordenar fetching de dados com cache.
Decidi usar cache-first strategy para otimizar performance.
"""

from typing import List
from datetime import datetime

from domain.value_objects.symbol import Symbol
from domain.value_objects.time_range import TimeRange
from domain.repositories.market_data_repository import (
    MarketDataRepository,
    MarketDataBar,
    MarketDataNotAvailableError,
)
from infrastructure.adapters.finnhub_adapter import FinnhubAdapter
from infrastructure.adapters.alpha_vantage_adapter import AlphaVantageAdapter
from infrastructure.telemetry.prometheus_metrics import get_metrics
from infrastructure.telemetry.loki_logger import get_logger


class MarketDataService:
    """
    Service de orquestração de market data.

    Implementei lógica de cache-first com fallback para APIs externas.
    Uso Finnhub para real-time e Alpha Vantage para histórico.
    """

    def __init__(
        self,
        repository: MarketDataRepository,
        finnhub: FinnhubAdapter,
        alpha_vantage: AlphaVantageAdapter,
    ):
        """
        Construtor com dependency injection.

        Args:
            repository: Repository com cache
            finnhub: Adapter Finnhub
            alpha_vantage: Adapter Alpha Vantage
        """
        self._repo = repository
        self._finnhub = finnhub
        self._alpha_vantage = alpha_vantage
        self._metrics = get_metrics()
        self._logger = get_logger()

    def fetch_historical(
        self, symbol: Symbol, time_range: TimeRange, interval: str = "1d"
    ) -> List[MarketDataBar]:
        """
        Busco dados históricos (cache-first).

        Implementei lógica:
        1. Verifico cache
        2. Se não está completo, busco de API
        3. Cacheia resultado
        4. Retorna dados

        Args:
            symbol: Símbolo do ativo
            time_range: Range de tempo
            interval: Intervalo (1d, 1h, etc)

        Returns:
            Lista de barras OHLCV
        """
        start_time = datetime.utcnow()

        try:
            # Tento cache primeiro
            cached_data = self._repo.get_historical(symbol, time_range, interval)

            if cached_data:
                self._logger.info(f"Cache hit for {symbol}", symbol=symbol.value)
                self._metrics.record_api_call("cache", "hit", 0.001)
                return cached_data

            # Cache miss - busco de API
            self._logger.info(f"Cache miss for {symbol}, fetching from API", symbol=symbol.value)

            # Uso Alpha Vantage para histórico
            api_start = datetime.utcnow()
            if interval == "1d":
                bars = self._alpha_vantage.get_daily(symbol, outputsize="full")
            else:
                bars = self._alpha_vantage.get_intraday(symbol, interval)

            api_duration = (datetime.utcnow() - api_start).total_seconds()
            self._metrics.record_api_call("alpha_vantage", "success", api_duration)

            # Filtro por time_range
            bars = [b for b in bars if time_range.contains(b.timestamp)]

            # Cacheia
            if bars:
                self._repo.cache(symbol, bars, interval)
                self._logger.info(f"Cached {len(bars)} bars for {symbol}")

            return bars

        except Exception as e:
            self._logger.error(f"Failed to fetch historical data: {e}", symbol=symbol.value)
            self._metrics.record_api_call("alpha_vantage", "error", 0)
            raise

    def subscribe_realtime(self, symbol: Symbol) -> None:
        """
        Inscrevo em dados real-time via Finnhub WebSocket.

        Args:
            symbol: Símbolo para monitorar
        """
        try:
            if not self._finnhub.is_connected():
                # Callback para processar trades
                def on_trade(trade_data):
                    self._logger.debug(
                        f"Received trade: {trade_data}",
                        symbol=trade_data.get("s"),
                        price=trade_data.get("p"),
                    )

                self._finnhub.connect_websocket(on_trade)

            self._finnhub.subscribe(symbol)
            self._logger.info(f"Subscribed to real-time data for {symbol}")

        except Exception as e:
            self._logger.error(f"Failed to subscribe to real-time: {e}")
            raise