"""
Observability View.

Implementei view para observabilidade com métricas Prometheus.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QTextEdit, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from presentation.viewmodels.observability_vm import ObservabilityViewModel
from presentation.widgets.charts.live_metrics_dashboard import LiveMetricsDashboard


class ObservabilityView(QWidget):
    """
    View de observabilidade.

    Implementei interface para visualizar métricas Prometheus
    em tempo real com charts e gauges.
    """

    def __init__(self):
        """Inicializo view."""
        super().__init__()
        self.viewmodel = ObservabilityViewModel()
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Crio interface."""
        main_layout = QVBoxLayout()

        # Header com status de conexão
        header_layout = QHBoxLayout()

        header = QLabel("Observability - Prometheus Metrics")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        header_layout.addWidget(header)

        header_layout.addStretch()

        self.status_label = QLabel("Disconnected")
        self.status_label.setStyleSheet("color: red; font-weight: bold;")
        header_layout.addWidget(self.status_label)

        main_layout.addLayout(header_layout)

        # Connection controls
        connection_layout = QHBoxLayout()

        connection_layout.addWidget(QLabel("Prometheus URL:"))

        self.prometheus_url_input = QLineEdit()
        self.prometheus_url_input.setText("http://localhost:9090")
        connection_layout.addWidget(self.prometheus_url_input)

        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._on_connect_clicked)
        connection_layout.addWidget(self.connect_button)

        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self._on_disconnect_clicked)
        self.disconnect_button.setEnabled(False)
        connection_layout.addWidget(self.disconnect_button)

        main_layout.addLayout(connection_layout)

        # Metrics dashboard
        self.metrics_dashboard = LiveMetricsDashboard()
        main_layout.addWidget(self.metrics_dashboard)

        # Custom query section
        query_group = self._create_query_section()
        main_layout.addWidget(query_group)

        self.setLayout(main_layout)

    def _create_query_section(self) -> QGroupBox:
        """
        Crio seção de query customizada.

        Returns:
            GroupBox com controles de query
        """
        group = QGroupBox("Custom PromQL Query")
        layout = QVBoxLayout()

        # Query input
        input_layout = QHBoxLayout()

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter PromQL query (e.g., rate(nexus_api_calls_total[5m]))")
        input_layout.addWidget(self.query_input)

        execute_button = QPushButton("Execute")
        execute_button.clicked.connect(self._on_execute_query_clicked)
        input_layout.addWidget(execute_button)

        layout.addLayout(input_layout)

        # Results text
        self.query_results = QTextEdit()
        self.query_results.setReadOnly(True)
        self.query_results.setMaximumHeight(150)
        layout.addWidget(self.query_results)

        group.setLayout(layout)
        return group

    def _connect_signals(self) -> None:
        """Conecto signals do ViewModel."""
        self.viewmodel.connection_status_changed.connect(
            self._on_connection_status_changed
        )
        self.viewmodel.metrics_loaded.connect(self._on_metrics_loaded)
        self.viewmodel.error_occurred.connect(self._on_error)

    def _on_connect_clicked(self) -> None:
        """Handler do botão Connect."""
        # TODO: Usar URL do input (recriar cliente)
        self.viewmodel.connect_to_prometheus()

    def _on_disconnect_clicked(self) -> None:
        """Handler do botão Disconnect."""
        self.viewmodel.disconnect_from_prometheus()

    def _on_execute_query_clicked(self) -> None:
        """Handler do botão Execute Query."""
        query = self.query_input.text().strip()

        if not query:
            self.query_results.setText("Please enter a PromQL query")
            return

        result = self.viewmodel.query_custom_promql(query)

        if result:
            import json
            formatted = json.dumps(result, indent=2)
            self.query_results.setText(formatted)
        else:
            self.query_results.setText("Query returned no results or error occurred")

    def _on_connection_status_changed(self, connected: bool) -> None:
        """
        Handler quando status de conexão muda.

        Args:
            connected: Se está conectado
        """
        if connected:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)
            self.prometheus_url_input.setEnabled(False)

            # Inicio refresh automático (5s)
            self.viewmodel.start_auto_refresh(5000)

        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)
            self.prometheus_url_input.setEnabled(True)

            # Limpo métricas
            self.metrics_dashboard.clear_metrics()

    def _on_metrics_loaded(self, metrics: dict) -> None:
        """
        Handler quando métricas são carregadas.

        Args:
            metrics: Dict com métricas
        """
        self.metrics_dashboard.update_metrics(metrics)

    def _on_error(self, error: str) -> None:
        """
        Handler quando erro ocorre.

        Args:
            error: Mensagem de erro
        """
        # TODO: Mostrar erro em dialog
        print(f"Observability error: {error}")
        self.query_results.setText(f"Error: {error}")

    def closeEvent(self, event) -> None:
        """Handler quando view é fechada."""
        if self.viewmodel.is_connected:
            self.viewmodel.disconnect_from_prometheus()
        super().closeEvent(event)