"""
Equity Curve Chart Widget.

Implementei widget para visualizar curva de equity de backtests.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtCore import Qt
import pyqtgraph as pg
from typing import List


class EquityCurveChart(QWidget):
    """
    Widget de equity curve chart.

    Implementei chart para visualizar evolução do capital ao longo
    do tempo em backtests.
    """

    def __init__(self):
        """Inicializo widget."""
        super().__init__()
        self._init_ui()

    def _init_ui(self) -> None:
        """Crio interface."""
        layout = QVBoxLayout()

        # Crio plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("#1e1e1e")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        # Configurações do plot
        self.plot_widget.setLabel("left", "Equity ($)")
        self.plot_widget.setLabel("bottom", "Time")
        self.plot_widget.setTitle(
            "Equity Curve",
            color="#cccccc",
            size="12pt"
        )

        # Estilos
        styles = {"color": "#cccccc", "font-size": "10px"}
        self.plot_widget.getAxis("left").setTextPen(pg.mkPen(**styles))
        self.plot_widget.getAxis("bottom").setTextPen(pg.mkPen(**styles))

        # Adiciono legenda
        self.plot_widget.addLegend()

        layout.addWidget(self.plot_widget)
        self.setLayout(layout)

        # Referências para plots
        self.equity_line = None
        self.drawdown_line = None

    def plot_equity_curve(self, equity_values: List[float]) -> None:
        """
        Ploto curva de equity.

        Args:
            equity_values: Lista de valores de equity ao longo do tempo
        """
        if not equity_values:
            return

        # Limpo plot anterior
        self.plot_widget.clear()

        # Ploto equity
        self.equity_line = self.plot_widget.plot(
            equity_values,
            pen=pg.mkPen(color="#00ff00", width=2),
            name="Equity"
        )

        # Calculo e ploto drawdown
        drawdown = self._calculate_drawdown(equity_values)

        if drawdown:
            # Ploto drawdown em escala secundária (aproximada)
            # Para simplificar, ploto no mesmo eixo
            self.drawdown_line = self.plot_widget.plot(
                drawdown,
                pen=pg.mkPen(color="#ff0000", width=1, style=Qt.PenStyle.DashLine),
                name="Drawdown"
            )

    def _calculate_drawdown(self, equity_values: List[float]) -> List[float]:
        """
        Calculo drawdown.

        Args:
            equity_values: Lista de valores de equity

        Returns:
            Lista de valores de drawdown
        """
        if not equity_values:
            return []

        drawdown = []
        peak = equity_values[0]

        for value in equity_values:
            if value > peak:
                peak = value

            dd = ((value - peak) / peak) * 100 if peak > 0 else 0
            drawdown.append(dd)

        return drawdown

    def plot_multiple_curves(
        self,
        curves_data: List[tuple[str, List[float]]]
    ) -> None:
        """
        Ploto múltiplas curvas para comparação.

        Args:
            curves_data: Lista de tuplas (nome, valores)
        """
        if not curves_data:
            return

        # Limpo plot anterior
        self.plot_widget.clear()

        # Cores para diferentes curvas
        colors = ["#00ff00", "#007acc", "#ff6600", "#ff00ff", "#ffff00"]

        for i, (name, values) in enumerate(curves_data):
            color = colors[i % len(colors)]
            self.plot_widget.plot(
                values,
                pen=pg.mkPen(color=color, width=2),
                name=name
            )

    def clear(self) -> None:
        """Limpo chart."""
        self.plot_widget.clear()

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

    def export_image(self, file_path: str) -> None:
        """
        Exporto chart como imagem.

        Args:
            file_path: Caminho do arquivo
        """
        exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
        exporter.export(file_path)
