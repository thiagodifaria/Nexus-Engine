"""
Alpha Vantage API Adapter para dados históricos.

Implementei adapter para Alpha Vantage REST API.
Decidi usar para backtests históricos com rate limit handling.

Referências:
- Alpha Vantage API: https://www.alphavantage.co/documentation/
"""

import time
from typing import List
from datetime import datetime

from alpha_vantage.timeseries import TimeSeries

from config.settings import get_settings
from domain.value_objects.symbol import Symbol
from domain.value_objects.time_range import TimeRange
from domain.repositories.market_data_repository import MarketDataBar, MarketDataAPIError


class AlphaVantageAdapter:
    """
    Adapter para Alpha Vantage API (dados históricos).

    Implementei com rate limit handling porque free tier tem 25 calls/day.
    Uso throttling para evitar exceder limite.

    Referência: https://www.alphavantage.co/documentation/
    """

    def __init__(self):
        """Inicializo adapter Alpha Vantage."""
        settings = get_settings()
        self._api_key = settings.alpha_vantage_api_key

        if not self._api_key:
            raise ValueError("ALPHA_VANTAGE_API_KEY not configured")

        # Cliente Alpha Vantage
        self._ts = TimeSeries(key=self._api_key, output_format="pandas")

        # Rate limiting (25 calls/day free tier)
        self._last_call_time = 0
        self._min_interval_seconds = 12  # ~5 calls/min (safe margin)

    def _throttle(self) -> None:
        """
        Implemento throttling para respeitar rate limits.

        Decidi usar delay fixo para simplificar e ser conservador.
        """
        elapsed = time.time() - self._last_call_time
        if elapsed < self._min_interval_seconds:
            sleep_time = self._min_interval_seconds - elapsed
            print(f"Rate limiting: sleeping {sleep_time:.1f}s")
            time.sleep(sleep_time)
        self._last_call_time = time.time()

    def get_daily(
        self, symbol: Symbol, outputsize: str = "compact"
    ) -> List[MarketDataBar]:
        """
        Busco dados diários.

        Args:
            symbol: Símbolo do ativo
            outputsize: 'compact' (100 dias) ou 'full' (20+ anos)

        Returns:
            Lista de barras OHLCV

        Raises:
            MarketDataAPIError: Se API falhar
        """
        try:
            self._throttle()

            # Busco dados diários
            data, meta_data = self._ts.get_daily(
                symbol=symbol.value, outputsize=outputsize
            )

            # Converto DataFrame para MarketDataBar
            bars = []
            for timestamp, row in data.iterrows():
                bars.append(
                    MarketDataBar(
                        symbol=symbol.value,
                        timestamp=timestamp.to_pydatetime(),
                        open=float(row["1. open"]),
                        high=float(row["2. high"]),
                        low=float(row["3. low"]),
                        close=float(row["4. close"]),
                        volume=float(row["5. volume"]),
                    )
                )

            # Ordeno por timestamp crescente
            bars.sort(key=lambda x: x.timestamp)
            return bars

        except Exception as e:
            raise MarketDataAPIError("AlphaVantage", f"Failed to fetch daily data: {e}")

    def get_intraday(
        self, symbol: Symbol, interval: str = "5min"
    ) -> List[MarketDataBar]:
        """
        Busco dados intraday.

        Args:
            symbol: Símbolo
            interval: 1min, 5min, 15min, 30min, 60min

        Returns:
            Lista de barras OHLCV

        Raises:
            MarketDataAPIError: Se API falhar
        """
        try:
            self._throttle()

            data, meta_data = self._ts.get_intraday(
                symbol=symbol.value, interval=interval, outputsize="full"
            )

            bars = []
            for timestamp, row in data.iterrows():
                bars.append(
                    MarketDataBar(
                        symbol=symbol.value,
                        timestamp=timestamp.to_pydatetime(),
                        open=float(row["1. open"]),
                        high=float(row["2. high"]),
                        low=float(row["3. low"]),
                        close=float(row["4. close"]),
                        volume=float(row["5. volume"]),
                    )
                )

            bars.sort(key=lambda x: x.timestamp)
            return bars

        except Exception as e:
            raise MarketDataAPIError(
                "AlphaVantage", f"Failed to fetch intraday data: {e}"
            )