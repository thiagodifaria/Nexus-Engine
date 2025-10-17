"""
Implementação do MarketDataRepository com cache PostgreSQL.

Implementei cache local em PostgreSQL para evitar rate limiting de APIs.
Decidi usar cache-first strategy para otimizar performance.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from domain.value_objects.symbol import Symbol
from domain.value_objects.time_range import TimeRange
from domain.repositories.market_data_repository import (
    MarketDataRepository,
    MarketDataBar,
    MarketDataNotAvailableError,
    CacheError,
)
from infrastructure.database.models import MarketDataCache
from infrastructure.database.postgres_client import PostgresClient


class MarketDataRepositoryImpl(MarketDataRepository):
    """
    Implementação PostgreSQL do MarketDataRepository.

    Implementei com cache em PostgreSQL para:
    - Evitar rate limiting de APIs externas
    - Acelerar backtests repetidos
    - Persistir dados históricos
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Construtor com dependency injection.

        Args:
            postgres_client: Cliente PostgreSQL
        """
        self._client = postgres_client

    def get_historical(
        self, symbol: Symbol, time_range: TimeRange, interval: str = "1d"
    ) -> List[MarketDataBar]:
        """
        Busco dados históricos (cache-first).

        Implementei lógica:
        1. Tento buscar do cache
        2. Se não está completo, retorno vazio (adapter buscará de API)

        Args:
            symbol: Símbolo do ativo
            time_range: Range de tempo
            interval: Intervalo

        Returns:
            Lista de barras OHLCV ou lista vazia se não cacheado
        """
        try:
            with self._client.get_session() as session:
                query = session.query(MarketDataCache).filter(
                    and_(
                        MarketDataCache.symbol == symbol.value,
                        MarketDataCache.interval == interval,
                        MarketDataCache.timestamp >= time_range.start_date,
                        MarketDataCache.timestamp <= time_range.end_date,
                    )
                ).order_by(MarketDataCache.timestamp.asc())

                cached_data = query.all()

                # Converto para MarketDataBar
                return [
                    MarketDataBar(
                        symbol=data.symbol,
                        timestamp=data.timestamp,
                        open=data.open,
                        high=data.high,
                        low=data.low,
                        close=data.close,
                        volume=data.volume,
                    )
                    for data in cached_data
                ]

        except SQLAlchemyError as e:
            raise CacheError(f"Failed to retrieve cached data: {e}")

    def get_latest(self, symbol: Symbol) -> Optional[MarketDataBar]:
        """
        Busco última barra disponível no cache.

        Args:
            symbol: Símbolo do ativo

        Returns:
            Última barra ou None
        """
        try:
            with self._client.get_session() as session:
                latest = (
                    session.query(MarketDataCache)
                    .filter_by(symbol=symbol.value)
                    .order_by(MarketDataCache.timestamp.desc())
                    .first()
                )

                if latest:
                    return MarketDataBar(
                        symbol=latest.symbol,
                        timestamp=latest.timestamp,
                        open=latest.open,
                        high=latest.high,
                        low=latest.low,
                        close=latest.close,
                        volume=latest.volume,
                    )
                return None

        except SQLAlchemyError as e:
            raise CacheError(f"Failed to get latest data: {e}")

    def cache(
        self, symbol: Symbol, bars: List[MarketDataBar], interval: str = "1d"
    ) -> None:
        """
        Cacheia dados de mercado.

        Implementei upsert para evitar duplicatas.

        Args:
            symbol: Símbolo do ativo
            bars: Barras a cachear
            interval: Intervalo
        """
        try:
            with self._client.get_session() as session:
                for bar in bars:
                    # Verifico se já existe
                    existing = (
                        session.query(MarketDataCache)
                        .filter_by(
                            symbol=bar.symbol,
                            timestamp=bar.timestamp,
                            interval=interval,
                        )
                        .first()
                    )

                    if existing:
                        # UPDATE
                        existing.open = bar.open
                        existing.high = bar.high
                        existing.low = bar.low
                        existing.close = bar.close
                        existing.volume = bar.volume
                        existing.cached_at = datetime.utcnow()
                    else:
                        # INSERT
                        cache_entry = MarketDataCache(
                            symbol=bar.symbol,
                            timestamp=bar.timestamp,
                            interval=interval,
                            open=bar.open,
                            high=bar.high,
                            low=bar.low,
                            close=bar.close,
                            volume=bar.volume,
                            source=None,  # Pode ser preenchido pelo adapter
                        )
                        session.add(cache_entry)

        except SQLAlchemyError as e:
            raise CacheError(f"Failed to cache data: {e}")

    def is_cached(
        self, symbol: Symbol, time_range: TimeRange, interval: str = "1d"
    ) -> bool:
        """
        Verifico se dados estão completamente cacheados.

        Implementei verificação simples de existência de dados no range.

        Args:
            symbol: Símbolo
            time_range: Range de tempo
            interval: Intervalo

        Returns:
            True se há dados cacheados
        """
        try:
            with self._client.get_session() as session:
                count = (
                    session.query(MarketDataCache)
                    .filter(
                        and_(
                            MarketDataCache.symbol == symbol.value,
                            MarketDataCache.interval == interval,
                            MarketDataCache.timestamp >= time_range.start_date,
                            MarketDataCache.timestamp <= time_range.end_date,
                        )
                    )
                    .count()
                )
                return count > 0
        except SQLAlchemyError as e:
            raise CacheError(f"Failed to check cache: {e}")

    def clear_cache(self, symbol: Optional[Symbol] = None) -> None:
        """
        Limpo cache.

        Args:
            symbol: Se fornecido, limpa apenas este símbolo
        """
        try:
            with self._client.get_session() as session:
                if symbol:
                    session.query(MarketDataCache).filter_by(
                        symbol=symbol.value
                    ).delete()
                else:
                    session.query(MarketDataCache).delete()
        except SQLAlchemyError as e:
            raise CacheError(f"Failed to clear cache: {e}")