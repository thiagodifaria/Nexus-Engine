"""
Prometheus metrics exporter.

Implementei exportador de métricas customizadas para Prometheus.
Decidi usar Counter, Gauge e Histogram para diferentes tipos de métricas.

Referências:
- Prometheus Python Client: https://github.com/prometheus/client_python
- Metric Types: https://prometheus.io/docs/concepts/metric_types/
"""

from prometheus_client import Counter, Gauge, Histogram, Summary, start_http_server
from typing import Optional

from config.settings import get_settings


class PrometheusMetrics:
    """
    Exportador de métricas Prometheus.

    Implementei métricas customizadas para monitorar:
    - Performance do backtest engine
    - Trades executados
    - Chamadas de API externa
    - Latência do C++ engine
    """

    def __init__(self):
        """Inicializo métricas Prometheus."""

        # Backtest metrics
        self.backtests_total = Counter(
            'nexus_backtests_total',
            'Total number of backtests executed',
            ['strategy_type', 'status']
        )

        self.backtest_duration_seconds = Histogram(
            'nexus_backtest_duration_seconds',
            'Backtest execution time in seconds',
            ['strategy_type'],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        )

        # Trade metrics
        self.trades_total = Counter(
            'nexus_trades_total',
            'Total number of trades executed',
            ['symbol', 'side']
        )

        self.trade_pnl = Summary(
            'nexus_trade_pnl',
            'Trade profit and loss',
            ['symbol']
        )

        # API metrics
        self.api_calls_total = Counter(
            'nexus_api_calls_total',
            'Total API calls to external services',
            ['api_name', 'status']
        )

        self.api_latency_seconds = Histogram(
            'nexus_api_latency_seconds',
            'API call latency',
            ['api_name'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
        )

        # C++ Engine metrics
        self.cpp_engine_latency_ns = Histogram(
            'nexus_cpp_engine_latency_nanoseconds',
            'C++ engine latency in nanoseconds',
            ['operation'],
            buckets=[100, 500, 1000, 5000, 10000, 50000, 100000]
        )

        self.signals_generated_total = Counter(
            'nexus_signals_generated_total',
            'Total trading signals generated',
            ['strategy_type', 'signal_type']
        )

        # System metrics
        self.active_strategies = Gauge(
            'nexus_active_strategies',
            'Number of active strategies'
        )

        self.cache_hit_rate = Gauge(
            'nexus_cache_hit_rate',
            'Market data cache hit rate percentage'
        )

    def record_backtest(self, strategy_type: str, status: str, duration: float) -> None:
        """
        Registro execução de backtest.

        Args:
            strategy_type: Tipo da estratégia
            status: completed, failed
            duration: Duração em segundos
        """
        self.backtests_total.labels(strategy_type=strategy_type, status=status).inc()
        self.backtest_duration_seconds.labels(strategy_type=strategy_type).observe(duration)

    def record_trade(self, symbol: str, side: str, pnl: Optional[float] = None) -> None:
        """
        Registro trade executado.

        Args:
            symbol: Símbolo do ativo
            side: BUY ou SELL
            pnl: Profit/Loss (se aplicável)
        """
        self.trades_total.labels(symbol=symbol, side=side).inc()
        if pnl is not None:
            self.trade_pnl.labels(symbol=symbol).observe(pnl)

    def record_api_call(self, api_name: str, status: str, latency: float) -> None:
        """
        Registro chamada de API externa.

        Args:
            api_name: Nome da API (finnhub, alpha_vantage, etc)
            status: success, error
            latency: Latência em segundos
        """
        self.api_calls_total.labels(api_name=api_name, status=status).inc()
        self.api_latency_seconds.labels(api_name=api_name).observe(latency)

    def record_cpp_latency(self, operation: str, latency_ns: float) -> None:
        """
        Registro latência do C++ engine.

        Args:
            operation: Nome da operação (signal_generation, backtest_run, etc)
            latency_ns: Latência em nanossegundos
        """
        self.cpp_engine_latency_ns.labels(operation=operation).observe(latency_ns)

    def record_signal(self, strategy_type: str, signal_type: str) -> None:
        """
        Registro sinal de trading gerado.

        Args:
            strategy_type: Tipo da estratégia
            signal_type: BUY, SELL, HOLD
        """
        self.signals_generated_total.labels(
            strategy_type=strategy_type,
            signal_type=signal_type
        ).inc()

    def update_active_strategies(self, count: int) -> None:
        """Atualizo número de estratégias ativas."""
        self.active_strategies.set(count)

    def update_cache_hit_rate(self, rate: float) -> None:
        """
        Atualizo taxa de cache hit.

        Args:
            rate: Taxa entre 0.0 e 100.0
        """
        self.cache_hit_rate.set(rate)


# Singleton instance
_metrics: Optional[PrometheusMetrics] = None


def get_metrics() -> PrometheusMetrics:
    """Retorno singleton de métricas."""
    global _metrics
    if _metrics is None:
        _metrics = PrometheusMetrics()
    return _metrics


def start_metrics_server(port: Optional[int] = None) -> None:
    """
    Inicio servidor HTTP para Prometheus scraping.

    Args:
        port: Porta (default: configuração)
    """
    settings = get_settings()
    port = port or settings.prometheus_port
    start_http_server(port)
    print(f"Prometheus metrics server started on port {port}")