"""
Live Trading View.

Implementei view para live trading com chart em tempo real e gestão de posições.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QLineEdit, QTableWidget,
    QTableWidgetItem, QGroupBox, QHeaderView, QDoubleSpinBox,
    QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from presentation.viewmodels.live_trading_vm import LiveTradingViewModel
from presentation.widgets.charts.candlestick_chart import CandlestickChart


class LiveTradingView(QWidget):
    """
    View de live trading.

    Implementei interface com chart em tempo real, tabela de posições
    e controles de ordem.
    """

    def __init__(self):
        """Inicializo view."""
        super().__init__()
        self.viewmodel = LiveTradingViewModel()
        self._init_ui()
        self._connect_signals()

    def _init_ui(self) -> None:
        """Crio interface."""
        main_layout = QVBoxLayout()

        # Header com status de conexão
        header_layout = QHBoxLayout()

        header = QLabel("Live Trading")
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
        connection_group = self._create_connection_controls()
        main_layout.addWidget(connection_group)

        # Content layout (chart + positions)
        content_layout = QHBoxLayout()

        # Chart section
        chart_group = self._create_chart_section()
        content_layout.addWidget(chart_group, stretch=2)

        # Right panel (orders + positions)
        right_panel = QVBoxLayout()

        orders_group = self._create_orders_section()
        right_panel.addWidget(orders_group)

        positions_group = self._create_positions_section()
        right_panel.addWidget(positions_group)

        content_layout.addLayout(right_panel, stretch=1)

        main_layout.addLayout(content_layout)

        self.setLayout(main_layout)

    def _create_connection_controls(self) -> QGroupBox:
        """
        Crio controles de conexão.

        Returns:
            GroupBox com controles
        """
        group = QGroupBox("Connection")
        layout = QHBoxLayout()

        # Strategy selector
        layout.addWidget(QLabel("Strategy:"))
        self.strategy_combo = QComboBox()
        self.strategy_combo.addItems([
            "SMA Crossover",
            "RSI Mean Reversion",
            "MACD Momentum",
        ])
        layout.addWidget(self.strategy_combo)

        # Symbols input
        layout.addWidget(QLabel("Symbols:"))
        self.symbols_input = QLineEdit()
        self.symbols_input.setPlaceholderText("AAPL, GOOGL, MSFT")
        self.symbols_input.setText("AAPL")
        layout.addWidget(self.symbols_input)

        # Connect button
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self.connect_button)

        # Disconnect button
        self.disconnect_button = QPushButton("Disconnect")
        self.disconnect_button.clicked.connect(self._on_disconnect_clicked)
        self.disconnect_button.setEnabled(False)
        layout.addWidget(self.disconnect_button)

        group.setLayout(layout)
        return group

    def _create_chart_section(self) -> QGroupBox:
        """
        Crio seção de chart.

        Returns:
            GroupBox com chart
        """
        group = QGroupBox("Price Chart")
        layout = QVBoxLayout()

        # Candlestick chart
        self.chart = CandlestickChart()
        self.chart.set_title("Real-Time Price")
        layout.addWidget(self.chart)

        group.setLayout(layout)
        return group

    def _create_orders_section(self) -> QGroupBox:
        """
        Crio seção de ordens.

        Returns:
            GroupBox com controles de ordem
        """
        group = QGroupBox("Place Order")
        layout = QFormLayout()

        # Symbol selector
        self.order_symbol_combo = QComboBox()
        layout.addRow("Symbol:", self.order_symbol_combo)

        # Order type
        self.order_type_combo = QComboBox()
        self.order_type_combo.addItems(["BUY", "SELL"])
        layout.addRow("Type:", self.order_type_combo)

        # Quantity
        self.quantity_spin = QDoubleSpinBox()
        self.quantity_spin.setDecimals(0)
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(10000)
        self.quantity_spin.setValue(100)
        layout.addRow("Quantity:", self.quantity_spin)

        # Place order button
        place_button = QPushButton("Place Order")
        place_button.clicked.connect(self._on_place_order_clicked)
        layout.addRow(place_button)

        group.setLayout(layout)
        return group

    def _create_positions_section(self) -> QGroupBox:
        """
        Crio seção de posições.

        Returns:
            GroupBox com tabela de posições
        """
        group = QGroupBox("Open Positions")
        layout = QVBoxLayout()

        # Tabela de posições
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(5)
        self.positions_table.setHorizontalHeaderLabels([
            "Symbol", "Qty", "Avg Price", "Current", "P&L %"
        ])
        self.positions_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.positions_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.positions_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )

        layout.addWidget(self.positions_table)
        group.setLayout(layout)
        return group

    def _connect_signals(self) -> None:
        """Conecto signals do ViewModel."""
        self.viewmodel.connection_status_changed.connect(
            self._on_connection_status_changed
        )
        self.viewmodel.price_updated.connect(self._on_price_updated)
        self.viewmodel.positions_updated.connect(self._on_positions_updated)
        self.viewmodel.order_executed.connect(self._on_order_executed)
        self.viewmodel.error_occurred.connect(self._on_error)

    def _on_connect_clicked(self) -> None:
        """Handler do botão Connect."""
        strategy_id = "str-001"  # TODO: Obter ID real da estratégia selecionada
        symbols = [s.strip() for s in self.symbols_input.text().split(",")]

        self.viewmodel.connect(strategy_id, symbols)

    def _on_disconnect_clicked(self) -> None:
        """Handler do botão Disconnect."""
        self.viewmodel.disconnect()

    def _on_place_order_clicked(self) -> None:
        """Handler do botão Place Order."""
        symbol = self.order_symbol_combo.currentText()
        order_type = self.order_type_combo.currentText()
        quantity = self.quantity_spin.value()

        self.viewmodel.place_order(symbol, order_type, quantity)

    def _on_connection_status_changed(self, connected: bool, message: str) -> None:
        """
        Handler quando status de conexão muda.

        Args:
            connected: Se está conectado
            message: Mensagem de status
        """
        if connected:
            self.status_label.setText("Connected")
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
            self.connect_button.setEnabled(False)
            self.disconnect_button.setEnabled(True)

            # Populo combo de símbolos nas ordens
            symbols = [s.strip() for s in self.symbols_input.text().split(",")]
            self.order_symbol_combo.clear()
            self.order_symbol_combo.addItems(symbols)

        else:
            self.status_label.setText("Disconnected")
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
            self.connect_button.setEnabled(True)
            self.disconnect_button.setEnabled(False)

            # Limpo chart
            self.chart.clear()

    def _on_price_updated(self, price_data: dict) -> None:
        """
        Handler quando preço é atualizado.

        Args:
            price_data: Dict com dados de preço
        """
        # Adiciono ponto ao chart
        self.chart.add_price_point(price_data)

        # Atualizo preços das posições
        self.viewmodel.update_position_prices(price_data)

    def _on_positions_updated(self, positions: list) -> None:
        """
        Handler quando posições são atualizadas.

        Args:
            positions: Lista de posições
        """
        self.positions_table.setRowCount(len(positions))

        for row, position in enumerate(positions):
            self.positions_table.setItem(
                row, 0, QTableWidgetItem(position["symbol"])
            )
            self.positions_table.setItem(
                row, 1, QTableWidgetItem(f"{position['quantity']:.0f}")
            )
            self.positions_table.setItem(
                row, 2, QTableWidgetItem(f"${position['avg_price']:.2f}")
            )
            self.positions_table.setItem(
                row, 3, QTableWidgetItem(f"${position['current_price']:.2f}")
            )

            # P&L com cor
            pnl_percent = position["pnl_percent"]
            pnl_item = QTableWidgetItem(f"{pnl_percent:+.2f}%")

            if pnl_percent > 0:
                pnl_item.setForeground(Qt.GlobalColor.green)
            elif pnl_percent < 0:
                pnl_item.setForeground(Qt.GlobalColor.red)

            self.positions_table.setItem(row, 4, pnl_item)

    def _on_order_executed(self, order: dict) -> None:
        """
        Handler quando ordem é executada.

        Args:
            order: Dict com ordem
        """
        # TODO: Mostrar notificação de ordem executada
        print(f"Order executed: {order}")

    def _on_error(self, error: str) -> None:
        """
        Handler quando erro ocorre.

        Args:
            error: Mensagem de erro
        """
        # TODO: Mostrar erro em dialog
        print(f"Live trading error: {error}")

    def closeEvent(self, event) -> None:
        """Handler quando view é fechada."""
        if self.viewmodel.is_connected:
            self.viewmodel.disconnect()
        super().closeEvent(event)
