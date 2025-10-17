"""
Fetch Market Data Use Case.

Implementei use case para buscar dados de mercado de múltiplas fontes.
Decidi usar strategy pattern para selecionar fonte apropriada.

Referências:
- Clean Architecture: Use Cases layer
"""

from typing import List, Optional
from datetime import datetime

from domain.value_objects.symbol import Symbol
from domain.value_objects.time_range import TimeRange
from infrastructure.adapters.finnhub_adapter import FinnhubAdapter
from infrastructure.adapters.alpha_vantage_adapter import AlphaVantageAdapter
from infrastructure.telemetry.tempo_tracer import TempoTracer
from infrastructure.telemetry.prometheus_metrics import PrometheusMetrics


class FetchMarketDataUseCase:
    """
    Use case para buscar dados de mercado.

    Implementei seleção automática de fonte baseado em disponibilidade
    e tipo de dados (real-time vs histórico).
    """

    def __init__(
        self,
        tracer: Optional[TempoTracer] = None,
        metrics: Optional[PrometheusMetrics] = None,
    ):
        """
        Construtor.

        Args:
            tracer: Tracer para observabilidade
            metrics: Métricas Prometheus
        """
        self._tracer = tracer or TempoTracer()
        self._metrics = metrics or PrometheusMetrics()

        # Inicializo adapters
        self._finnhub = FinnhubAdapter()
        self._alpha_vantage = AlphaVantageAdapter()

    def fetch_historical(
        self,
        symbol: Symbol,
        time_range: TimeRange,
        interval: str = "1d",
        source: str = "auto",
    ) -> List[dict]:
        """
        Busco dados históricos.

        Args:
            symbol: Símbolo
            time_range: Período
            interval: Intervalo (1d, 1h, etc)
            source: Fonte de dados (auto, finnhub, alpha_vantage)

        Returns:
            Lista de barras OHLCV

        Raises:
            ValueError: Se parâmetros inválidos
            RuntimeError: Se todas as fontes falharem
        """
        with self._tracer.start_span("fetch_historical_market_data"):
            # Valido inputs
            if not symbol:
                raise ValueError("symbol cannot be empty")

            # Seleciono fonte
            if source == "auto":
                source = self._select_best_source_for_historical(interval)

            # Busco dados
            try:
                if source == "finnhub":
                    data = self._fetch_from_finnhub(symbol, time_range, interval)
                elif source == "alpha_vantage":
                    data = self._fetch_from_alpha_vantage(symbol, time_range, interval)
                else:
                    raise ValueError(f"Unknown source: {source}")

                # Incremento métrica
                self._metrics.api_calls_total.labels(provider=source).inc()

                return data

            except Exception as e:
                # Se falhar, tento fonte alternativa
                if source != "alpha_vantage":
                    try:
                        data = self._fetch_from_alpha_vantage(
                            symbol, time_range, interval
                        )
                        self._metrics.api_calls_total.labels(
                            provider="alpha_vantage"
                        ).inc()
                        return data
                    except Exception:
                        pass

                raise RuntimeError(f"Failed to fetch market data: {e}")

    def fetch_realtime(
        self,
        symbol: Symbol,
        callback: callable,
    ) -> None:
        """
        Busco dados real-time via WebSocket.

        Args:
            symbol: Símbolo
            callback: Função callback para receber atualizações

        Raises:
            ValueError: Se parâmetros inválidos
            RuntimeError: Se falha ao conectar
        """
        with self._tracer.start_span("fetch_realtime_market_data"):
            # Valido inputs
            if not symbol:
                raise ValueError("symbol cannot be empty")

            if not callback:
                raise ValueError("callback cannot be None")

            try:
                # Uso Finnhub WebSocket para real-time
                self._finnhub.subscribe_realtime(symbol, callback)

                # Incremento métrica
                self._metrics.api_calls_total.labels(
                    provider="finnhub_websocket"
                ).inc()

            except Exception as e:
                raise RuntimeError(f"Failed to subscribe to real-time data: {e}")

    def unsubscribe_realtime(self, symbol: Symbol) -> None:
        """
        Cancelo subscrição real-time.

        Args:
            symbol: Símbolo
        """
        try:
            self._finnhub.unsubscribe_realtime(symbol)
        except Exception as e:
            print(f"Error unsubscribing: {e}")

    def _select_best_source_for_historical(self, interval: str) -> str:
        """
        Seleciono melhor fonte para dados históricos.

        Args:
            interval: Intervalo dos dados

        Returns:
            Nome da fonte
        """
        # Alpha Vantage é melhor para dados diários (rate limits mais generosos)
        if interval in ["1d", "daily"]:
            return "alpha_vantage"

        # Finnhub é melhor para intraday
        return "finnhub"

    def _fetch_from_finnhub(
        self,
        symbol: Symbol,
        time_range: TimeRange,
        interval: str,
    ) -> List[dict]:
        """
        Busco dados do Finnhub.

        Args:
            symbol: Símbolo
            time_range: Período
            interval: Intervalo

        Returns:
            Lista de barras OHLCV
        """
        # Converto interval para resolution do Finnhub
        resolution_map = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "1h": "60",
            "1d": "D",
            "daily": "D",
        }
        resolution = resolution_map.get(interval, "D")

        data = self._finnhub.get_historical_data(
            symbol,
            time_range.start,
            time_range.end,
            resolution,
        )

        return self._normalize_data_format(data)

    def _fetch_from_alpha_vantage(
        self,
        symbol: Symbol,
        time_range: TimeRange,
        interval: str,
    ) -> List[dict]:
        """
        Busco dados do Alpha Vantage.

        Args:
            symbol: Símbolo
            time_range: Período
            interval: Intervalo

        Returns:
            Lista de barras OHLCV
        """
        data = self._alpha_vantage.get_historical_data(
            symbol,
            time_range.start,
            time_range.end,
            interval,
        )

        return self._normalize_data_format(data)

    def _normalize_data_format(self, data: List[dict]) -> List[dict]:
        """
        Normalizo formato dos dados de diferentes fontes.

        Args:
            data: Dados brutos

        Returns:
            Dados normalizados
        """
        # Garanto que todos os dados tenham mesmo formato
        normalized = []

        for bar in data:
            normalized.append({
                "timestamp": bar.get("timestamp") or bar.get("t"),
                "open": float(bar.get("open") or bar.get("o", 0)),
                "high": float(bar.get("high") or bar.get("h", 0)),
                "low": float(bar.get("low") or bar.get("l", 0)),
                "close": float(bar.get("close") or bar.get("c", 0)),
                "volume": float(bar.get("volume") or bar.get("v", 0)),
            })

        return normalized

    def get_supported_symbols(self, source: str = "finnhub") -> List[str]:
        """
        Listo símbolos suportados.

        Args:
            source: Fonte de dados

        Returns:
            Lista de símbolos
        """
        try:
            if source == "finnhub":
                return self._finnhub.get_supported_symbols()
            elif source == "alpha_vantage":
                return self._alpha_vantage.get_supported_symbols()
            else:
                raise ValueError(f"Unknown source: {source}")

        except Exception as e:
            print(f"Error fetching supported symbols: {e}")
            return []