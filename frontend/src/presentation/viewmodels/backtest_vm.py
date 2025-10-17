"""
Backtest ViewModel.

Implementei ViewModel para view de backtest seguindo MVVM.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Dict, List


class BacktestViewModel(QObject):
    """
    ViewModel para backtest.

    Implementei usando Qt signals para comunicação assíncrona.
    """

    # Signals
    backtest_started = pyqtSignal()
    backtest_completed = pyqtSignal(dict)
    backtest_failed = pyqtSignal(str)
    progress_updated = pyqtSignal(int)

    def __init__(self):
        """Inicializo ViewModel."""
        super().__init__()
        self._is_running = False

    def start_backtest(
        self,
        strategy_id: str,
        symbols: List[str],
        start_date: str,
        end_date: str,
        initial_capital: float,
    ) -> None:
        """
        Inicio backtest.

        Args:
            strategy_id: ID da estratégia
            symbols: Lista de símbolos
            start_date: Data inicial
            end_date: Data final
            initial_capital: Capital inicial
        """
        if self._is_running:
            return

        self._is_running = True
        self.backtest_started.emit()

        # TODO: Chamar backend via BackendClient
        # Por enquanto, simulo conclusão
        self._is_running = False
        result = {"return": 15.5, "sharpe": 1.8, "trades": 45}
        self.backtest_completed.emit(result)

    def cancel_backtest(self) -> None:
        """Cancelo backtest em execução."""
        self._is_running = False
