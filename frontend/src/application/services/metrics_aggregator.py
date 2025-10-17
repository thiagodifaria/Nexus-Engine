"""
Metrics Aggregator Service.

Implementei service para agregar métricas de múltiplas fontes.
Decidi consolidar métricas de backtests, live trading e sistema.
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta


class MetricsAggregator:
    """
    Agregador de métricas.

    Implementei singleton para consolidar métricas de diferentes fontes.
    """

    _instance: Optional["MetricsAggregator"] = None

    def __new__(cls):
        """Implemento singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Inicializo agregador."""
        if not hasattr(self, "_initialized"):
            self._backtest_metrics: List[Dict] = []
            self._live_trading_metrics: List[Dict] = []
            self._system_metrics: List[Dict] = []
            self._initialized = True

    def record_backtest_metric(
        self,
        strategy_id: str,
        metrics: Dict[str, float],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Registro métrica de backtest.

        Args:
            strategy_id: ID da estratégia
            metrics: Dict com métricas
            timestamp: Timestamp opcional
        """
        record = {
            "timestamp": timestamp or datetime.now(),
            "strategy_id": strategy_id,
            "type": "backtest",
            "metrics": metrics,
        }

        self._backtest_metrics.append(record)

        # Limito histórico a 1000 registros
        if len(self._backtest_metrics) > 1000:
            self._backtest_metrics.pop(0)

    def record_live_trading_metric(
        self,
        strategy_id: str,
        symbol: str,
        metrics: Dict[str, float],
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Registro métrica de live trading.

        Args:
            strategy_id: ID da estratégia
            symbol: Símbolo negociado
            metrics: Dict com métricas
            timestamp: Timestamp opcional
        """
        record = {
            "timestamp": timestamp or datetime.now(),
            "strategy_id": strategy_id,
            "symbol": symbol,
            "type": "live_trading",
            "metrics": metrics,
        }

        self._live_trading_metrics.append(record)

        # Limito histórico a 1000 registros
        if len(self._live_trading_metrics) > 1000:
            self._live_trading_metrics.pop(0)

    def record_system_metric(
        self,
        metric_name: str,
        value: float,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Registro métrica de sistema.

        Args:
            metric_name: Nome da métrica
            value: Valor
            timestamp: Timestamp opcional
        """
        record = {
            "timestamp": timestamp or datetime.now(),
            "metric_name": metric_name,
            "type": "system",
            "value": value,
        }

        self._system_metrics.append(record)

        # Limito histórico a 1000 registros
        if len(self._system_metrics) > 1000:
            self._system_metrics.pop(0)

    def get_backtest_summary(self) -> Dict:
        """
        Calculo resumo de backtests.

        Returns:
            Dict com estatísticas agregadas
        """
        if not self._backtest_metrics:
            return {
                "total_backtests": 0,
                "avg_return": 0.0,
                "avg_sharpe": 0.0,
                "avg_trades": 0.0,
            }

        total = len(self._backtest_metrics)
        avg_return = sum(
            m["metrics"].get("total_return", 0.0)
            for m in self._backtest_metrics
        ) / total

        avg_sharpe = sum(
            m["metrics"].get("sharpe_ratio", 0.0)
            for m in self._backtest_metrics
        ) / total

        avg_trades = sum(
            m["metrics"].get("total_trades", 0)
            for m in self._backtest_metrics
        ) / total

        return {
            "total_backtests": total,
            "avg_return": avg_return,
            "avg_sharpe": avg_sharpe,
            "avg_trades": avg_trades,
        }

    def get_live_trading_summary(self) -> Dict:
        """
        Calculo resumo de live trading.

        Returns:
            Dict com estatísticas agregadas
        """
        if not self._live_trading_metrics:
            return {
                "total_trades": 0,
                "total_pnl": 0.0,
                "win_rate": 0.0,
            }

        total_trades = len(self._live_trading_metrics)

        total_pnl = sum(
            m["metrics"].get("pnl", 0.0)
            for m in self._live_trading_metrics
        )

        winning_trades = sum(
            1 for m in self._live_trading_metrics
            if m["metrics"].get("pnl", 0.0) > 0
        )

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

        return {
            "total_trades": total_trades,
            "total_pnl": total_pnl,
            "win_rate": win_rate,
        }

    def get_metrics_by_strategy(self, strategy_id: str) -> Dict:
        """
        Busco métricas de uma estratégia específica.

        Args:
            strategy_id: ID da estratégia

        Returns:
            Dict com métricas agregadas da estratégia
        """
        backtest_metrics = [
            m for m in self._backtest_metrics
            if m["strategy_id"] == strategy_id
        ]

        live_metrics = [
            m for m in self._live_trading_metrics
            if m["strategy_id"] == strategy_id
        ]

        return {
            "strategy_id": strategy_id,
            "backtest_count": len(backtest_metrics),
            "live_trades": len(live_metrics),
            "backtest_metrics": backtest_metrics,
            "live_metrics": live_metrics,
        }

    def get_recent_metrics(self, hours: int = 24) -> Dict:
        """
        Busco métricas recentes.

        Args:
            hours: Quantidade de horas no passado

        Returns:
            Dict com métricas recentes
        """
        cutoff = datetime.now() - timedelta(hours=hours)

        recent_backtests = [
            m for m in self._backtest_metrics
            if m["timestamp"] >= cutoff
        ]

        recent_live = [
            m for m in self._live_trading_metrics
            if m["timestamp"] >= cutoff
        ]

        recent_system = [
            m for m in self._system_metrics
            if m["timestamp"] >= cutoff
        ]

        return {
            "period_hours": hours,
            "backtest_metrics": recent_backtests,
            "live_trading_metrics": recent_live,
            "system_metrics": recent_system,
        }

    def clear_all_metrics(self) -> None:
        """Limpo todas as métricas."""
        self._backtest_metrics = []
        self._live_trading_metrics = []
        self._system_metrics = []

    def export_metrics_to_dict(self) -> Dict:
        """
        Exporto todas as métricas.

        Returns:
            Dict com todas as métricas
        """
        return {
            "exported_at": datetime.now().isoformat(),
            "backtest_metrics": self._backtest_metrics,
            "live_trading_metrics": self._live_trading_metrics,
            "system_metrics": self._system_metrics,
        }