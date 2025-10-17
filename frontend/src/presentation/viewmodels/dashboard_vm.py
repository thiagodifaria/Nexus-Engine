"""
Dashboard ViewModel.

Implementei ViewModel para dashboard seguindo MVVM pattern.
Carrego métricas, backtests recentes e estratégias ativas.
"""

from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from typing import Dict, List, Optional
from datetime import datetime


class DashboardViewModel(QObject):
    """
    ViewModel para dashboard.

    Implementei carregamento de dados assíncrono e refresh automático.
    """

    # Signals
    metrics_loaded = pyqtSignal(dict)
    recent_backtests_loaded = pyqtSignal(list)
    active_strategies_loaded = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    refresh_completed = pyqtSignal()

    def __init__(self):
        """Inicializo ViewModel."""
        super().__init__()
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._auto_refresh)
        self._is_loading = False

    def load_dashboard_data(self) -> None:
        """
        Carrego todos os dados do dashboard.

        Implementei carregamento paralelo de métricas, backtests e estratégias.
        """
        if self._is_loading:
            return

        self._is_loading = True

        try:
            # TODO: Chamar backend via BackendClient
            # Por enquanto, simulo dados

            # Métricas gerais
            metrics = {
                "total_backtests": 156,
                "total_strategies": 12,
                "avg_return": 18.7,
                "avg_sharpe": 1.65,
                "total_trades": 8432,
                "win_rate": 58.3,
            }
            self.metrics_loaded.emit(metrics)

            # Backtests recentes
            recent_backtests = [
                {
                    "id": "bt-001",
                    "strategy": "SMA Crossover",
                    "symbols": ["AAPL", "GOOGL"],
                    "return": 22.5,
                    "sharpe": 1.92,
                    "date": "2025-10-15",
                },
                {
                    "id": "bt-002",
                    "strategy": "RSI Mean Reversion",
                    "symbols": ["TSLA"],
                    "return": 15.8,
                    "sharpe": 1.45,
                    "date": "2025-10-14",
                },
                {
                    "id": "bt-003",
                    "strategy": "MACD Momentum",
                    "symbols": ["SPY"],
                    "return": 12.3,
                    "sharpe": 1.33,
                    "date": "2025-10-13",
                },
            ]
            self.recent_backtests_loaded.emit(recent_backtests)

            # Estratégias ativas
            active_strategies = [
                {
                    "id": "str-001",
                    "name": "SMA Crossover",
                    "type": "SMA",
                    "status": "active",
                    "parameters": {"fast_period": 10, "slow_period": 50},
                },
                {
                    "id": "str-002",
                    "name": "RSI Mean Reversion",
                    "type": "RSI",
                    "status": "active",
                    "parameters": {"period": 14, "oversold": 30, "overbought": 70},
                },
                {
                    "id": "str-003",
                    "name": "MACD Momentum",
                    "type": "MACD",
                    "status": "paused",
                    "parameters": {"fast": 12, "slow": 26, "signal": 9},
                },
            ]
            self.active_strategies_loaded.emit(active_strategies)

            self.refresh_completed.emit()

        except Exception as e:
            self.error_occurred.emit(str(e))

        finally:
            self._is_loading = False

    def start_auto_refresh(self, interval_ms: int = 30000) -> None:
        """
        Inicio refresh automático.

        Args:
            interval_ms: Intervalo em milissegundos (padrão: 30s)
        """
        self._refresh_timer.start(interval_ms)

    def stop_auto_refresh(self) -> None:
        """Paro refresh automático."""
        self._refresh_timer.stop()

    def _auto_refresh(self) -> None:
        """Handler para refresh automático."""
        self.load_dashboard_data()

    def get_backtest_details(self, backtest_id: str) -> Optional[Dict]:
        """
        Busco detalhes de um backtest específico.

        Args:
            backtest_id: ID do backtest

        Returns:
            Detalhes do backtest ou None
        """
        try:
            # TODO: Chamar backend
            # Por enquanto, retorno None
            return None

        except Exception as e:
            self.error_occurred.emit(str(e))
            return None