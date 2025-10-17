"""
Dashboard View.

Implementei view principal do dashboard com métricas, backtests e estratégias.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QGroupBox,
    QGridLayout, QPushButton, QHeaderView
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from presentation.viewmodels.dashboard_vm import DashboardViewModel


class DashboardView(QWidget):
    """
    View de dashboard.

    Implementei interface com cards de métricas, tabela de backtests
    recentes e lista de estratégias ativas.
    """

    def __init__(self):
        """Inicializo view."""
        super().__init__()
        self.viewmodel = DashboardViewModel()
        self._init_ui()
        self._connect_signals()

        # Carrego dados iniciais
        self.viewmodel.load_dashboard_data()

        # Inicio refresh automático (30s)
        self.viewmodel.start_auto_refresh(30000)

    def _init_ui(self) -> None:
        """Crio interface."""
        main_layout = QVBoxLayout()

        # Header
        header = QLabel("Dashboard")
        header_font = QFont()
        header_font.setPointSize(18)
        header_font.setBold(True)
        header.setFont(header_font)
        main_layout.addWidget(header)

        # Metrics cards
        metrics_group = self._create_metrics_section()
        main_layout.addWidget(metrics_group)

        # Content layout (backtests + strategies)
        content_layout = QHBoxLayout()

        # Recent backtests
        backtests_group = self._create_backtests_section()
        content_layout.addWidget(backtests_group, stretch=2)

        # Active strategies
        strategies_group = self._create_strategies_section()
        content_layout.addWidget(strategies_group, stretch=1)

        main_layout.addLayout(content_layout)

        # Refresh button
        refresh_button = QPushButton("Refresh Dashboard")
        refresh_button.clicked.connect(self.viewmodel.load_dashboard_data)
        main_layout.addWidget(refresh_button)

        self.setLayout(main_layout)

    def _create_metrics_section(self) -> QGroupBox:
        """
        Crio seção de métricas.

        Returns:
            GroupBox com cards de métricas
        """
        group = QGroupBox("Key Metrics")
        layout = QGridLayout()

        # Crio cards de métricas (inicialmente vazios)
        self.total_backtests_label = self._create_metric_card("Total Backtests", "0")
        self.total_strategies_label = self._create_metric_card("Total Strategies", "0")
        self.avg_return_label = self._create_metric_card("Avg Return", "0.0%")
        self.avg_sharpe_label = self._create_metric_card("Avg Sharpe", "0.0")
        self.total_trades_label = self._create_metric_card("Total Trades", "0")
        self.win_rate_label = self._create_metric_card("Win Rate", "0.0%")

        # Adiciono cards ao grid
        layout.addWidget(self.total_backtests_label, 0, 0)
        layout.addWidget(self.total_strategies_label, 0, 1)
        layout.addWidget(self.avg_return_label, 0, 2)
        layout.addWidget(self.avg_sharpe_label, 1, 0)
        layout.addWidget(self.total_trades_label, 1, 1)
        layout.addWidget(self.win_rate_label, 1, 2)

        group.setLayout(layout)
        return group

    def _create_metric_card(self, title: str, value: str) -> QLabel:
        """
        Crio card de métrica.

        Args:
            title: Título da métrica
            value: Valor inicial

        Returns:
            Label com formatação de card
        """
        label = QLabel(f"{title}\n{value}")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                background-color: #2d2d30;
                border: 1px solid #3d3d3d;
                border-radius: 8px;
                padding: 20px;
                font-size: 14px;
            }
        """)
        label.setMinimumHeight(100)
        return label

    def _create_backtests_section(self) -> QGroupBox:
        """
        Crio seção de backtests recentes.

        Returns:
            GroupBox com tabela de backtests
        """
        group = QGroupBox("Recent Backtests")
        layout = QVBoxLayout()

        # Tabela de backtests
        self.backtests_table = QTableWidget()
        self.backtests_table.setColumnCount(5)
        self.backtests_table.setHorizontalHeaderLabels([
            "Strategy", "Symbols", "Return %", "Sharpe", "Date"
        ])
        self.backtests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.backtests_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.backtests_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.backtests_table)
        group.setLayout(layout)
        return group

    def _create_strategies_section(self) -> QGroupBox:
        """
        Crio seção de estratégias ativas.

        Returns:
            GroupBox com tabela de estratégias
        """
        group = QGroupBox("Active Strategies")
        layout = QVBoxLayout()

        # Tabela de estratégias
        self.strategies_table = QTableWidget()
        self.strategies_table.setColumnCount(3)
        self.strategies_table.setHorizontalHeaderLabels([
            "Name", "Type", "Status"
        ])
        self.strategies_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.strategies_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.strategies_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        layout.addWidget(self.strategies_table)
        group.setLayout(layout)
        return group

    def _connect_signals(self) -> None:
        """Conecto signals do ViewModel."""
        self.viewmodel.metrics_loaded.connect(self._on_metrics_loaded)
        self.viewmodel.recent_backtests_loaded.connect(self._on_backtests_loaded)
        self.viewmodel.active_strategies_loaded.connect(self._on_strategies_loaded)
        self.viewmodel.error_occurred.connect(self._on_error)

    def _on_metrics_loaded(self, metrics: dict) -> None:
        """
        Handler quando métricas são carregadas.

        Args:
            metrics: Dict com métricas
        """
        # Atualizo cards
        self.total_backtests_label.setText(
            f"Total Backtests\n{metrics['total_backtests']}"
        )
        self.total_strategies_label.setText(
            f"Total Strategies\n{metrics['total_strategies']}"
        )
        self.avg_return_label.setText(
            f"Avg Return\n{metrics['avg_return']:.1f}%"
        )
        self.avg_sharpe_label.setText(
            f"Avg Sharpe\n{metrics['avg_sharpe']:.2f}"
        )
        self.total_trades_label.setText(
            f"Total Trades\n{metrics['total_trades']}"
        )
        self.win_rate_label.setText(
            f"Win Rate\n{metrics['win_rate']:.1f}%"
        )

    def _on_backtests_loaded(self, backtests: list) -> None:
        """
        Handler quando backtests são carregados.

        Args:
            backtests: Lista de backtests
        """
        self.backtests_table.setRowCount(len(backtests))

        for row, backtest in enumerate(backtests):
            self.backtests_table.setItem(
                row, 0, QTableWidgetItem(backtest["strategy"])
            )
            self.backtests_table.setItem(
                row, 1, QTableWidgetItem(", ".join(backtest["symbols"]))
            )
            self.backtests_table.setItem(
                row, 2, QTableWidgetItem(f"{backtest['return']:.1f}%")
            )
            self.backtests_table.setItem(
                row, 3, QTableWidgetItem(f"{backtest['sharpe']:.2f}")
            )
            self.backtests_table.setItem(
                row, 4, QTableWidgetItem(backtest["date"])
            )

    def _on_strategies_loaded(self, strategies: list) -> None:
        """
        Handler quando estratégias são carregadas.

        Args:
            strategies: Lista de estratégias
        """
        self.strategies_table.setRowCount(len(strategies))

        for row, strategy in enumerate(strategies):
            self.strategies_table.setItem(
                row, 0, QTableWidgetItem(strategy["name"])
            )
            self.strategies_table.setItem(
                row, 1, QTableWidgetItem(strategy["type"])
            )

            status_item = QTableWidgetItem(strategy["status"])
            if strategy["status"] == "active":
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.yellow)

            self.strategies_table.setItem(row, 2, status_item)

    def _on_error(self, error: str) -> None:
        """
        Handler quando erro ocorre.

        Args:
            error: Mensagem de erro
        """
        # TODO: Mostrar erro em dialog
        print(f"Dashboard error: {error}")

    def closeEvent(self, event) -> None:
        """Handler quando view é fechada."""
        self.viewmodel.stop_auto_refresh()
        super().closeEvent(event)