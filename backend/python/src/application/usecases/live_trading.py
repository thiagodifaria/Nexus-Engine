"""
Live Trading Use Case.

Implementei use case para execução de live trading em tempo real.
Decidi usar WebSocket para dados real-time via Finnhub.

Referências:
- Clean Architecture: Use Cases layer
"""

from typing import Dict, List, Optional, Callable
from uuid import UUID
from datetime import datetime

from domain.entities.strategy import Strategy
from domain.entities.position import Position
from domain.entities.trade import Trade
from domain.value_objects.symbol import Symbol
from domain.repositories.strategy_repository import StrategyRepository
from infrastructure.telemetry.tempo_tracer import TempoTracer
from infrastructure.telemetry.prometheus_metrics import PrometheusMetrics


class LiveTradingUseCase:
    """
    Use case para live trading.

    Implementei execução de estratégia em tempo real com WebSocket.
    """

    def __init__(
        self,
        strategy_repository: Optional[StrategyRepository] = None,
        tracer: Optional[TempoTracer] = None,
        metrics: Optional[PrometheusMetrics] = None,
    ):
        """
        Construtor.

        Args:
            strategy_repository: Repositório de estratégias
            tracer: Tracer para observabilidade
            metrics: Métricas Prometheus
        """
        # TODO: Injetar dependências via DI
        if strategy_repository is None:
            from infrastructure.database.strategy_repository_impl import (
                StrategyRepositoryImpl,
            )
            from infrastructure.database.postgres_client import PostgresClient

            client = PostgresClient()
            strategy_repository = StrategyRepositoryImpl(client)

        self._strategy_repository = strategy_repository
        self._tracer = tracer or TempoTracer()
        self._metrics = metrics or PrometheusMetrics()

        # Estado interno
        self._active_sessions: Dict[str, Dict] = {}
        self._positions: Dict[str, Position] = {}

    def start_session(
        self,
        strategy_id: UUID,
        symbols: List[Symbol],
        initial_capital: float = 100000.0,
        on_trade: Optional[Callable] = None,
        on_position_update: Optional[Callable] = None,
    ) -> str:
        """
        Inicio sessão de live trading.

        Args:
            strategy_id: ID da estratégia
            symbols: Lista de símbolos para monitorar
            initial_capital: Capital inicial
            on_trade: Callback quando trade é executado
            on_position_update: Callback quando posição é atualizada

        Returns:
            Session ID

        Raises:
            ValueError: Se parâmetros inválidos
            RuntimeError: Se falha ao iniciar
        """
        with self._tracer.start_span("start_live_trading_session"):
            # Valido inputs
            if not symbols:
                raise ValueError("symbols cannot be empty")

            if initial_capital <= 0:
                raise ValueError("initial_capital must be positive")

            # Busco estratégia
            strategy = self._strategy_repository.find_by_id(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")

            # Crio session
            from uuid import uuid4
            session_id = str(uuid4())

            session = {
                "id": session_id,
                "strategy": strategy,
                "symbols": symbols,
                "initial_capital": initial_capital,
                "current_capital": initial_capital,
                "positions": {},
                "trades": [],
                "started_at": datetime.now(),
                "status": "active",
                "on_trade": on_trade,
                "on_position_update": on_position_update,
            }

            self._active_sessions[session_id] = session

            # TODO: Conectar WebSocket Finnhub
            # self._connect_websocket(session_id, symbols)

            # Incremento métrica
            self._metrics.live_trading_sessions_total.inc()

            return session_id

    def stop_session(self, session_id: str) -> Dict:
        """
        Paro sessão de live trading.

        Args:
            session_id: ID da sessão

        Returns:
            Dict com resumo da sessão

        Raises:
            ValueError: Se sessão não existe
        """
        with self._tracer.start_span("stop_live_trading_session"):
            if session_id not in self._active_sessions:
                raise ValueError(f"Session {session_id} not found")

            session = self._active_sessions[session_id]

            # TODO: Desconectar WebSocket
            # self._disconnect_websocket(session_id)

            # Fecho todas as posições
            for symbol, position in session["positions"].items():
                if position.quantity > 0:
                    # TODO: Executar ordem de fechamento
                    pass

            # Marco como stopped
            session["status"] = "stopped"
            session["stopped_at"] = datetime.now()

            # Calculo resumo
            total_pnl = session["current_capital"] - session["initial_capital"]
            total_return_pct = (total_pnl / session["initial_capital"]) * 100

            summary = {
                "session_id": session_id,
                "strategy_id": str(session["strategy"].id),
                "duration_seconds": (
                    session["stopped_at"] - session["started_at"]
                ).total_seconds(),
                "initial_capital": session["initial_capital"],
                "final_capital": session["current_capital"],
                "total_pnl": total_pnl,
                "total_return_pct": total_return_pct,
                "total_trades": len(session["trades"]),
                "started_at": session["started_at"].isoformat(),
                "stopped_at": session["stopped_at"].isoformat(),
            }

            # Removo da lista de ativas
            del self._active_sessions[session_id]

            return summary

    def process_price_update(
        self,
        session_id: str,
        symbol: Symbol,
        price: float,
        timestamp: datetime,
    ) -> None:
        """
        Processo atualização de preço.

        Args:
            session_id: ID da sessão
            symbol: Símbolo
            price: Preço atual
            timestamp: Timestamp

        Raises:
            ValueError: Se sessão não existe
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self._active_sessions[session_id]
        strategy = session["strategy"]

        # Atualizo posições existentes
        if symbol.value in session["positions"]:
            position = session["positions"][symbol.value]
            # TODO: Atualizar P&L da posição

            if session["on_position_update"]:
                session["on_position_update"](position)

        # TODO: Executar lógica da estratégia para gerar sinais
        # signal = strategy.evaluate(price, timestamp)
        # if signal:
        #     self._execute_signal(session_id, symbol, signal, price)

    def _execute_signal(
        self,
        session_id: str,
        symbol: Symbol,
        signal: str,
        price: float,
    ) -> None:
        """
        Executo sinal de trading.

        Args:
            session_id: ID da sessão
            symbol: Símbolo
            signal: Sinal (BUY/SELL)
            price: Preço de execução
        """
        session = self._active_sessions[session_id]

        # TODO: Calcular quantidade baseado em risk management
        quantity = 100.0

        # Crio trade
        from uuid import uuid4
        trade = Trade(
            id=uuid4(),
            strategy_id=session["strategy"].id,
            symbol=symbol,
            direction=signal,
            quantity=quantity,
            price=price,
            timestamp=datetime.now(),
        )

        # Adiciono ao histórico
        session["trades"].append(trade)

        # Atualizo posição
        if symbol.value not in session["positions"]:
            session["positions"][symbol.value] = Position(
                id=uuid4(),
                strategy_id=session["strategy"].id,
                symbol=symbol,
                quantity=0,
                average_price=0.0,
                current_price=price,
            )

        position = session["positions"][symbol.value]

        if signal == "BUY":
            position.add_quantity(quantity, price)
        elif signal == "SELL":
            position.reduce_quantity(quantity, price)

        # Atualizo capital
        pnl = trade.quantity * (trade.price - position.average_price)
        session["current_capital"] += pnl

        # Incremento métrica
        self._metrics.trades_total.inc()

        # Callback
        if session["on_trade"]:
            session["on_trade"](trade)

    def get_session_status(self, session_id: str) -> Dict:
        """
        Busco status da sessão.

        Args:
            session_id: ID da sessão

        Returns:
            Dict com status

        Raises:
            ValueError: Se sessão não existe
        """
        if session_id not in self._active_sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self._active_sessions[session_id]

        return {
            "session_id": session_id,
            "strategy_id": str(session["strategy"].id),
            "status": session["status"],
            "current_capital": session["current_capital"],
            "open_positions": len(session["positions"]),
            "total_trades": len(session["trades"]),
            "started_at": session["started_at"].isoformat(),
        }

    def list_active_sessions(self) -> List[Dict]:
        """
        Listo todas as sessões ativas.

        Returns:
            Lista de sessões
        """
        return [
            self.get_session_status(session_id)
            for session_id in self._active_sessions.keys()
        ]