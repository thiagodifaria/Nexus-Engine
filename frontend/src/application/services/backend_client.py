"""
Backend Client - ponte entre frontend e backend.

Implementei client para chamar backend Python diretamente (Direct Library).
Decidi usar QThread para operações assíncronas e não travar UI.

Referências:
- PyQt6 Threading: https://doc.qt.io/qtforpython-6/PySide6/QtCore/QThread.html
"""

from PyQt6.QtCore import QThread, pyqtSignal
from typing import Dict, List
import sys
from pathlib import Path

# Adiciono backend ao path
backend_path = Path(__file__).parent.parent.parent.parent.parent / "backend" / "python" / "src"
sys.path.insert(0, str(backend_path))


class BacktestThread(QThread):
    """
    Thread para executar backtest assincronamente.

    Implementei worker thread para não bloquear UI durante backtest.
    """

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, params: Dict):
        """
        Construtor.

        Args:
            params: Parâmetros do backtest
        """
        super().__init__()
        self.params = params

    def run(self) -> None:
        """Executo backtest em background."""
        try:
            # Importo use case do backend
            from application.usecases.run_backtest import RunBacktestUseCase
            from domain.value_objects.time_range import TimeRange
            from domain.value_objects.symbol import Symbol
            from datetime import datetime

            # Instancio use case
            usecase = RunBacktestUseCase()

            # Converto parâmetros
            strategy_id = self.params["strategy_id"]
            symbols = [Symbol(s) for s in self.params["symbols"]]
            time_range = TimeRange(
                start=datetime.fromisoformat(self.params["start_date"]),
                end=datetime.fromisoformat(self.params["end_date"])
            )
            initial_capital = self.params.get("initial_capital", 10000.0)

            # Executo backtest
            result = usecase.execute(
                strategy_id=strategy_id,
                symbols=symbols,
                time_range=time_range,
                initial_capital=initial_capital,
            )

            # Converto resultado para dict
            result_dict = {
                "backtest_id": str(result.id),
                "strategy_id": result.strategy_id,
                "final_capital": result.final_capital,
                "total_return": result.total_return_pct,
                "sharpe_ratio": result.sharpe_ratio,
                "max_drawdown": result.max_drawdown_pct,
                "total_trades": result.total_trades,
                "winning_trades": result.winning_trades,
                "losing_trades": result.losing_trades,
                "start_date": result.start_date.isoformat(),
                "end_date": result.end_date.isoformat(),
            }

            self.finished.emit(result_dict)

        except Exception as e:
            self.error.emit(str(e))


class BackendClient:
    """
    Cliente para comunicação com backend Python.

    Implementei direct library access (não REST API).
    Uso threads para operações assíncronas.
    """

    @staticmethod
    def run_backtest_async(params: Dict, callback: callable) -> QThread:
        """
        Executo backtest assincronamente.

        Args:
            params: Parâmetros do backtest
            callback: Função callback para resultado

        Returns:
            Thread em execução
        """
        thread = BacktestThread(params)
        thread.finished.connect(callback)
        thread.start()
        return thread

    @staticmethod
    def get_strategies() -> List[Dict]:
        """
        Busco todas as estratégias.

        Returns:
            Lista de estratégias
        """
        try:
            from application.services.strategy_service import StrategyService

            service = StrategyService()
            strategies = service.list_strategies()

            return [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "type": s.strategy_type,
                    "parameters": s.parameters,
                    "created_at": s.created_at.isoformat() if hasattr(s, "created_at") else None,
                }
                for s in strategies
            ]

        except Exception as e:
            print(f"Erro ao buscar estratégias: {e}")
            return []

    @staticmethod
    def create_strategy(
        name: str,
        strategy_type: str,
        parameters: Dict[str, float],
    ) -> Dict:
        """
        Crio nova estratégia.

        Args:
            name: Nome da estratégia
            strategy_type: Tipo (SMA, RSI, MACD)
            parameters: Parâmetros

        Returns:
            Dict com estratégia criada
        """
        try:
            from application.services.strategy_service import StrategyService

            service = StrategyService()
            strategy = service.create_strategy(name, strategy_type, parameters)

            return {
                "id": str(strategy.id),
                "name": strategy.name,
                "type": strategy.strategy_type,
                "parameters": strategy.parameters,
            }

        except Exception as e:
            raise Exception(f"Erro ao criar estratégia: {e}")

    @staticmethod
    def fetch_market_data(symbol: str, start_date: str, end_date: str) -> List[Dict]:
        """
        Busco dados de mercado.

        Args:
            symbol: Símbolo
            start_date: Data inicial (ISO format)
            end_date: Data final (ISO format)

        Returns:
            Lista de dados OHLCV
        """
        try:
            from application.services.market_data_service import MarketDataService
            from domain.value_objects.symbol import Symbol
            from datetime import datetime

            service = MarketDataService()

            symbol_vo = Symbol(symbol)
            start = datetime.fromisoformat(start_date)
            end = datetime.fromisoformat(end_date)

            data = service.get_historical_data(symbol_vo, start, end)

            return [
                {
                    "timestamp": bar.timestamp.isoformat(),
                    "open": float(bar.open),
                    "high": float(bar.high),
                    "low": float(bar.low),
                    "close": float(bar.close),
                    "volume": float(bar.volume),
                }
                for bar in data
            ]

        except Exception as e:
            print(f"Erro ao buscar dados de mercado: {e}")
            return []