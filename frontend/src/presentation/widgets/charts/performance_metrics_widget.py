"""
Performance Metrics Widget.

Implementei widget para exibir métricas de performance de backtests.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGridLayout, QLabel, QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from typing import Dict, Optional


class PerformanceMetricsWidget(QWidget):
    """
    Widget de métricas de performance.

    Implementei display de métricas chave de backtest:
    - Return
    - Sharpe Ratio
    - Max Drawdown
    - Win Rate
    - Total Trades
    """

    def __init__(self):
        """Inicializo widget."""
        super().__init__()
        self._init_ui()
        self._metric_labels: Dict[str, QLabel] = {}

    def _init_ui(self) -> None:
        """Crio interface."""
        main_layout = QVBoxLayout()

        # Group box para métricas
        group = QGroupBox("Performance Metrics")
        metrics_layout = QGridLayout()

        # Defino métricas a serem exibidas
        metrics = [
            ("total_return", "Total Return", "%"),
            ("sharpe_ratio", "Sharpe Ratio", ""),
            ("max_drawdown", "Max Drawdown", "%"),
            ("win_rate", "Win Rate", "%"),
            ("total_trades", "Total Trades", ""),
            ("winning_trades", "Winning Trades", ""),
            ("losing_trades", "Losing Trades", ""),
            ("profit_factor", "Profit Factor", ""),
            ("avg_trade", "Avg Trade", "$"),
            ("best_trade", "Best Trade", "$"),
            ("worst_trade", "Worst Trade", "$"),
            ("avg_win", "Avg Win", "$"),
            ("avg_loss", "Avg Loss", "$"),
        ]

        # Crio labels para cada métrica
        for i, (key, label, unit) in enumerate(metrics):
            row = i // 2
            col = (i % 2) * 2

            # Label name
            name_label = QLabel(f"{label}:")
            name_label.setStyleSheet("font-weight: bold;")
            metrics_layout.addWidget(name_label, row, col)

            # Value label
            value_label = QLabel("--")
            value_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            self._metric_labels[key] = value_label
            metrics_layout.addWidget(value_label, row, col + 1)

        group.setLayout(metrics_layout)
        main_layout.addWidget(group)

        self.setLayout(main_layout)

    def update_metrics(self, metrics: Dict[str, float]) -> None:
        """
        Atualizo métricas exibidas.

        Args:
            metrics: Dict com métricas calculadas
        """
        # Mapeamento de como formatar cada métrica
        formatters = {
            "total_return": lambda v: f"{v:+.2f}%",
            "sharpe_ratio": lambda v: f"{v:.2f}",
            "max_drawdown": lambda v: f"{v:.2f}%",
            "win_rate": lambda v: f"{v:.1f}%",
            "total_trades": lambda v: f"{int(v)}",
            "winning_trades": lambda v: f"{int(v)}",
            "losing_trades": lambda v: f"{int(v)}",
            "profit_factor": lambda v: f"{v:.2f}",
            "avg_trade": lambda v: f"${v:,.2f}",
            "best_trade": lambda v: f"${v:,.2f}",
            "worst_trade": lambda v: f"${v:,.2f}",
            "avg_win": lambda v: f"${v:,.2f}",
            "avg_loss": lambda v: f"${v:,.2f}",
        }

        for key, value_label in self._metric_labels.items():
            if key in metrics:
                value = metrics[key]
                formatter = formatters.get(key, lambda v: f"{v:.2f}")

                formatted_value = formatter(value)
                value_label.setText(formatted_value)

                # Aplico cor baseado no valor
                self._apply_color_by_value(value_label, key, value)
            else:
                value_label.setText("--")
                value_label.setStyleSheet("")

    def _apply_color_by_value(self, label: QLabel, metric_key: str, value: float) -> None:
        """
        Aplico cor baseado no valor da métrica.

        Args:
            label: Label a colorir
            metric_key: Chave da métrica
            value: Valor da métrica
        """
        # Métricas onde positivo é bom
        positive_is_good = [
            "total_return",
            "sharpe_ratio",
            "win_rate",
            "profit_factor",
            "avg_trade",
            "best_trade",
            "avg_win",
        ]

        # Métricas onde negativo é bom (menor é melhor)
        negative_is_good = [
            "max_drawdown",
            "worst_trade",
            "avg_loss",
        ]

        if metric_key in positive_is_good:
            if value > 0:
                label.setStyleSheet("color: #00ff00; font-weight: bold;")
            elif value < 0:
                label.setStyleSheet("color: #ff0000; font-weight: bold;")
            else:
                label.setStyleSheet("color: #cccccc;")

        elif metric_key in negative_is_good:
            if value < 0:
                label.setStyleSheet("color: #ff0000; font-weight: bold;")
            else:
                label.setStyleSheet("color: #cccccc;")

        else:
            label.setStyleSheet("color: #cccccc;")

    def clear_metrics(self) -> None:
        """Limpo todas as métricas."""
        for label in self._metric_labels.values():
            label.setText("--")
            label.setStyleSheet("")

    def set_metrics_from_backtest_result(self, result: Dict) -> None:
        """
        Defino métricas a partir de resultado de backtest.

        Args:
            result: Dict com resultado de backtest
        """
        # Extraio métricas do resultado
        metrics = {
            "total_return": result.get("total_return", 0.0),
            "sharpe_ratio": result.get("sharpe_ratio", 0.0),
            "max_drawdown": result.get("max_drawdown", 0.0),
            "win_rate": result.get("win_rate", 0.0),
            "total_trades": result.get("total_trades", 0),
            "winning_trades": result.get("winning_trades", 0),
            "losing_trades": result.get("losing_trades", 0),
        }

        # Calculo métricas derivadas se possível
        if "total_profit" in result and "total_loss" in result:
            total_loss = abs(result["total_loss"])
            metrics["profit_factor"] = (
                result["total_profit"] / total_loss if total_loss > 0 else 0.0
            )

        if "total_pnl" in result and result.get("total_trades", 0) > 0:
            metrics["avg_trade"] = result["total_pnl"] / result["total_trades"]

        if "best_trade" in result:
            metrics["best_trade"] = result["best_trade"]

        if "worst_trade" in result:
            metrics["worst_trade"] = result["worst_trade"]

        if "total_profit" in result and result.get("winning_trades", 0) > 0:
            metrics["avg_win"] = result["total_profit"] / result["winning_trades"]

        if "total_loss" in result and result.get("losing_trades", 0) > 0:
            metrics["avg_loss"] = result["total_loss"] / result["losing_trades"]

        self.update_metrics(metrics)