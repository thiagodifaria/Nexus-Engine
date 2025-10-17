"""
Observability ViewModel.

Implementei ViewModel para observabilidade com queries Prometheus.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from application.services.prometheus_client import PrometheusClient


class ObservabilityViewModel(QObject):
    """
    ViewModel para observabilidade.

    Implementei carregamento de métricas Prometheus com refresh automático.
    """

    # Signals
    metrics_loaded = pyqtSignal(dict)
    metric_history_loaded = pyqtSignal(str, list)  # metric_name, data_points
    connection_status_changed = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)

    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        """
        Construtor.

        Args:
            prometheus_url: URL do Prometheus
        """
        super().__init__()
        self._prometheus_client = PrometheusClient(prometheus_url)
        self._is_connected = False

        # Timer para refresh automático
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._auto_refresh)

        # Métricas monitoradas
        self._monitored_metrics = [
            "nexus_backtests_total",
            "nexus_trades_total",
            "nexus_api_calls_total",
            "nexus_cpp_engine_latency_ns",
        ]

    def connect_to_prometheus(self) -> None:
        """Conecto ao Prometheus."""
        try:
            is_healthy = self._prometheus_client.health_check()

            if is_healthy:
                self._is_connected = True
                self.connection_status_changed.emit(True)
                self.load_current_metrics()
            else:
                self._is_connected = False
                self.connection_status_changed.emit(False)
                self.error_occurred.emit("Prometheus is not healthy")

        except Exception as e:
            self._is_connected = False
            self.connection_status_changed.emit(False)
            self.error_occurred.emit(str(e))

    def disconnect_from_prometheus(self) -> None:
        """Desconecto do Prometheus."""
        self.stop_auto_refresh()
        self._is_connected = False
        self.connection_status_changed.emit(False)

    def load_current_metrics(self) -> None:
        """Carrego valores atuais das métricas."""
        if not self._is_connected:
            self.error_occurred.emit("Not connected to Prometheus")
            return

        try:
            metrics_data = {}

            for metric_name in self._monitored_metrics:
                value = self._prometheus_client.get_metric_current_value(metric_name)
                metrics_data[metric_name] = value if value is not None else 0.0

            self.metrics_loaded.emit(metrics_data)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def load_metric_history(
        self,
        metric_name: str,
        duration_minutes: int = 60,
    ) -> None:
        """
        Carrego histórico de uma métrica.

        Args:
            metric_name: Nome da métrica
            duration_minutes: Duração em minutos
        """
        if not self._is_connected:
            self.error_occurred.emit("Not connected to Prometheus")
            return

        try:
            history = self._prometheus_client.get_metric_history(
                metric_name,
                duration_minutes,
            )

            self.metric_history_loaded.emit(metric_name, history)

        except Exception as e:
            self.error_occurred.emit(str(e))

    def query_custom_promql(self, query: str) -> Optional[Dict]:
        """
        Executo query PromQL customizada.

        Args:
            query: Query PromQL

        Returns:
            Resultado da query ou None
        """
        if not self._is_connected:
            self.error_occurred.emit("Not connected to Prometheus")
            return None

        try:
            return self._prometheus_client.query_instant(query)

        except Exception as e:
            self.error_occurred.emit(str(e))
            return None

    def get_available_metrics(self) -> List[str]:
        """
        Listo todas as métricas disponíveis.

        Returns:
            Lista de nomes de métricas
        """
        if not self._is_connected:
            return []

        try:
            return self._prometheus_client.get_all_metrics()

        except Exception as e:
            self.error_occurred.emit(str(e))
            return []

    def start_auto_refresh(self, interval_ms: int = 5000) -> None:
        """
        Inicio refresh automático.

        Args:
            interval_ms: Intervalo em milissegundos (padrão: 5s)
        """
        if not self._is_connected:
            return

        self._refresh_timer.start(interval_ms)

    def stop_auto_refresh(self) -> None:
        """Paro refresh automático."""
        self._refresh_timer.stop()

    def _auto_refresh(self) -> None:
        """Handler para refresh automático."""
        self.load_current_metrics()

    @property
    def is_connected(self) -> bool:
        """Retorno status de conexão."""
        return self._is_connected

    def get_nexus_specific_metrics(self) -> Dict[str, str]:
        """
        Retorno mapeamento de métricas específicas do Nexus.

        Returns:
            Dict com metric_name -> descrição
        """
        return {
            "nexus_backtests_total": "Total de backtests executados",
            "nexus_trades_total": "Total de trades executados",
            "nexus_api_calls_total": "Total de chamadas API",
            "nexus_cpp_engine_latency_ns": "Latência do engine C++ (ns)",
        }