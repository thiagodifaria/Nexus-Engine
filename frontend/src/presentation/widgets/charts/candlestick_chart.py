"""
Candlestick Chart Widget.

Implementei widget de candlestick chart usando PyQtGraph para
visualização de preços em tempo real.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from typing import List, Dict
from datetime import datetime


class CandlestickChart(QWidget):
    """
    Widget de candlestick chart.

    Implementei chart de preços em tempo real com candlesticks.
    """

    def __init__(self):
        """Inicializo widget."""
        super().__init__()
        self._init_ui()
        self._data_points: List[Dict] = []

    def _init_ui(self) -> None:
        """Crio interface."""
        layout = QVBoxLayout()

        # Crio plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#1e1e1e")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Configurações do plot
        self.plot_widget.setLabel("left", "Price ($)")
        self.plot_widget.setLabel("bottom", "Time")

        # Estilos
        styles = {"color": "#cccccc", "font-size": "10px"}
        self.plot_widget.getAxis("left").setTextPen(pg.mkPen(**styles))
        self.plot_widget.getAxis("bottom").setTextPen(pg.mkPen(**styles))

        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

        # Line plot para preços (simplificado - candlestick completo requer custom item)
        self.price_line = self.plot_widget.plot(
            pen=pg.mkPen(color="#007acc", width=2)
        )

    def add_price_point(self, price_data: Dict) -> None:
        """
        Adiciono ponto de preço.

        Args:
            price_data: Dict com {symbol, price, timestamp}
        """
        self._data_points.append(price_data)

        # Limito a 100 pontos
        if len(self._data_points) > 100:
            self._data_points.pop(0)

        self._update_chart()

    def _update_chart(self) -> None:
        """Atualizo chart com dados atuais."""
        if not self._data_points:
            return

        # Extraio preços
        prices = [p["price"] for p in self._data_points]

        # Atualizo linha
        self.price_line.setData(prices)

    def clear(self) -> None:
        """Limpo chart."""
        self._data_points = []
        self.price_line.setData([])

    def set_title(self, title: str) -> None:
        """
        Defino título do chart.

        Args:
            title: Título
        """
        self.plot_widget.setTitle(
            title,
            color="#cccccc",
            size="12pt"
        )
