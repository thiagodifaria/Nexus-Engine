"""
Run Backtest Use Case.

Implementei caso de uso principal: executar backtest de estratégia.
Decidi orquestrar todos os componentes necessários aqui.
"""

from datetime import datetime
from typing import List
from uuid import UUID

from domain.entities.strategy import Strategy
from domain.entities.backtest import Backtest
from domain.value_objects.symbol import Symbol
from domain.value_objects.time_range import TimeRange
from application.services.market_data_service import MarketDataService
from application.services.strategy_service import StrategyService
from infrastructure.adapters.cpp_engine_adapter import CppEngineAdapter
from infrastructure.telemetry.prometheus_metrics import get_metrics
from infrastructure.telemetry.loki_logger import get_logger
from infrastructure.telemetry.tempo_tracer import get_tracer


class RunBacktestUseCase:
    """
    Use Case: Executar backtest de estratégia.

    Implementei orquestração completa do fluxo de backtest.
    """

    def __init__(
        self,
        strategy_service: StrategyService,
        market_data_service: MarketDataService,
        cpp_engine: CppEngineAdapter,
    ):
        """
        Construtor com dependency injection.

        Args:
            strategy_service: Service de estratégias
            market_data_service: Service de market data
            cpp_engine: Adapter do C++ engine
        """
        self._strategy_service = strategy_service
        self._market_data_service = market_data_service
        self._engine = cpp_engine
        self._metrics = get_metrics()
        self._logger = get_logger()
        self._tracer = get_tracer()

    def execute(
        self,
        strategy_id: UUID,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 10000.0,
    ) -> Backtest:
        """
        Executo backtest.

        Implementei fluxo completo:
        1. Busco estratégia
        2. Fetch market data
        3. Executo C++ engine
        4. Persisto resultados

        Args:
            strategy_id: ID da estratégia
            symbols: Lista de símbolos
            start_date: Data inicial
            end_date: Data final
            initial_capital: Capital inicial

        Returns:
            Backtest entity com resultados
        """
        with self._tracer.start_span("run_backtest", strategy_id=str(strategy_id)):
            # 1. Busco estratégia
            strategy = self._strategy_service.get_by_id(strategy_id)
            if not strategy:
                raise ValueError(f"Strategy {strategy_id} not found")

            self._logger.info(
                "Starting backtest",
                strategy_id=str(strategy_id),
                symbols=symbols,
            )

            # 2. Crio entidade Backtest
            backtest = Backtest(
                strategy_id=strategy_id,
                symbols=symbols,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
            )
            backtest.mark_as_running()

            try:
                # 3. Fetch market data
                time_range = TimeRange(start_date=start_date, end_date=end_date)
                all_market_data = []

                for symbol_str in symbols:
                    symbol = Symbol(value=symbol_str)
                    bars = self._market_data_service.fetch_historical(
                        symbol, time_range, interval="1d"
                    )
                    all_market_data.extend(bars)

                self._logger.info(f"Fetched {len(all_market_data)} bars")

                # 4. Configuro estratégia no C++ engine
                self._engine.create_strategy(strategy)

                # 5. Executo backtest
                execution_start = datetime.utcnow()

                results = self._engine.run_backtest(
                    strategy_id=str(strategy_id),
                    market_data=all_market_data,
                    initial_capital=initial_capital,
                )

                execution_time = (datetime.utcnow() - execution_start).total_seconds()

                # 6. Atualizo entidade Backtest
                backtest.mark_as_completed(
                    final_capital=results["final_capital"],
                    metrics=results,
                    total_trades=results["total_trades"],
                    winning_trades=results["winning_trades"],
                    losing_trades=results["losing_trades"],
                    execution_time=execution_time,
                )

                # 7. Métricas
                self._metrics.record_backtest(
                    strategy.strategy_type, "completed", execution_time
                )

                self._logger.info(
                    "Backtest completed successfully",
                    backtest_id=str(backtest.id),
                    return_pct=backtest.get_return_percentage(),
                )

                return backtest

            except Exception as e:
                # Marco como falho
                backtest.mark_as_failed(str(e))
                self._metrics.record_backtest(strategy.strategy_type, "failed", 0)
                self._logger.error(f"Backtest failed: {e}", backtest_id=str(backtest.id))
                raise