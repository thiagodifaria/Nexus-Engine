"""
Live Metrics Dashboard Widget.

Implementei widget para dashboard de métricas em tempo real.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import pyqtgraph as pg
from typing import Dict, List


class LiveMetricsDashboard(QWidget):
    """
    Widget de dashboard de métricas live.

    Implementei gauges e charts para visualização de métricas
    Prometheus em tempo real.
    """

    def __init__(self):
        """Inicializo widget."""
        super().__init__()
        self._init_ui()
        self._metric_labels: Dict[str, QLabel] = {}
        self._metric_charts: Dict[str, pg.PlotWidget] = {}
        self._metric_history: Dict[str, List[float]] = {}

    def _init_ui(self) -> None:
        """Crio interface."""
        main_layout = QVBoxLayout()

        # Gauges section (valores atuais)
        gauges_group = self._create_gauges_section()
        main_layout.addWidget(gauges_group)

        # Charts section (histórico)
        charts_group = self._create_charts_section()
        main_layout.addWidget(charts_group)

        self.setLayout(main_layout)

    def _create_gauges_section(self) -> QGroupBox:
        """
        Crio seção de gauges.

        Returns:
            GroupBox com gauges
        """
        group = QGroupBox("Current Metrics")
        layout = QGridLayout()

        # Crio labels para métricas
        metrics = [
            ("nexus_backtests_total", "Total Backtests"),
            ("nexus_trades_total", "Total Trades"),
            ("nexus_api_calls_total", "API Calls"),
            ("nexus_cpp_engine_latency_ns", "Engine Latency (ns)"),
        ]

        for i, (metric_key, metric_label) in enumerate(metrics):
            row = i // 2
            col = i % 2

            metric_widget = self._create_metric_gauge(metric_label)
            self._metric_labels[metric_key] = metric_widget
            layout.addWidget(metric_widget, row, col)

        group.setLayout(layout)
        return group

    def _create_metric_gauge(self, label: str) -> QLabel:
        """
        Crio gauge de métrica.

        Args:
            label: Label da métrica

        Returns:
            QLabel formatado como gauge
        """
        widget = QLabel(f"{label}\n0")
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        widget.setStyleSheet("""
            QLabel {
                background-color: #2d2d30;
                border: 2px solid #007acc;
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        widget.setMinimumHeight(100)
        return widget

    def _create_charts_section(self) -> QGroupBox:
        """
        Crio seção de charts.

        Returns:
            GroupBox com charts
        """
        group = QGroupBox("Metrics History")
        layout = QGridLayout()

        # Crio charts para métricas
        metrics = [
            ("nexus_backtests_total", "Backtests"),
            ("nexus_trades_total", "Trades"),
            ("nexus_api_calls_total", "API Calls"),
            ("nexus_cpp_engine_latency_ns", "Latency (ns)"),
        ]

        for i, (metric_key, metric_label) in enumerate(metrics):
            row = i // 2
            col = i % 2

            chart = self._create_metric_chart(metric_label)
            self._metric_charts[metric_key] = chart
            self._metric_history[metric_key] = []

            layout.addWidget(chart, row, col)

        group.setLayout(layout)
        return group

    def _create_metric_chart(self, title: str) -> pg.PlotWidget:
        """
        Crio chart de métrica.

        Args:
            title: Título do chart

        Returns:
            PlotWidget configurado
        """
        chart = pg.PlotWidget()
        chart.setBackground("#1e1e1e")
        chart.showGrid(x=True, y=True, alpha=0.3)
        chart.setTitle(title, color="#cccccc", size="11pt")

        # Estilos
        styles = {"color": "#cccccc", "font-size": "9px"}
        chart.getAxis("left").setTextPen(pg.mkPen(**styles))
        chart.getAxis("bottom").setTextPen(pg.mkPen(**styles))

        chart.setMinimumHeight(150)

        return chart

    def update_metric(self, metric_name: str, value: float) -> None:
        """
        Atualizo métrica.

        Args:
            metric_name: Nome da métrica
            value: Valor atual
        """
        # Atualizo gauge
        if metric_name in self._metric_labels:
            label = self._metric_labels[metric_name]
            metric_display = metric_name.replace("nexus_", "").replace("_", " ").title()

            # Formato valor
            if "latency" in metric_name:
                formatted_value = f"{value:,.0f} ns"
            else:
                formatted_value = f"{value:,.0f}"

            label.setText(f"{metric_display}\n{formatted_value}")

        # Atualizo histórico e chart
        if metric_name in self._metric_history:
            history = self._metric_history[metric_name]
            history.append(value)

            # Limito a 100 pontos
            if len(history) > 100:
                history.pop(0)

            # Atualizo chart
            if metric_name in self._metric_charts:
                chart = self._metric_charts[metric_name]
                chart.plot(
                    history,
                    pen=pg.mkPen(color="#007acc", width=2),
                    clear=True
                )

    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """
        Atualizo múltiplas métricas.

        Args:
            metrics: Dict com metric_name -> value
        """
        for metric_name, value in metrics.items():
            self.update_metric(metric_name, value)

    def clear_metrics(self) -> None:
        """Limpo todas as métricas."""
        for metric_name, label in self._metric_labels.items():
            metric_display = metric_name.replace("nexus_", "").replace("_", " ").title()
            label.setText(f"{metric_display}\n0")

        for metric_name, chart in self._metric_charts.items():
            self._metric_history[metric_name] = []
            chart.clear()
