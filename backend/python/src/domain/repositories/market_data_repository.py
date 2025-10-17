"""
Market Data Repository Interface - DDD Domain Layer.

Implementei interface para acesso a dados de mercado.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional

from domain.value_objects.symbol import Symbol
from domain.value_objects.time_range import TimeRange


class MarketDataBar:
    """
    Representa uma barra OHLCV de dados de mercado.

    Implementei como dataclass simples para transportar dados de mercado.
    Não é uma Entity pois não tem identidade única relevante.
    """

    def __init__(
        self,
        symbol: str,
        timestamp: datetime,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float
    ):
        """
        Construtor de MarketDataBar.

        Args:
            symbol: Símbolo do ativo
            timestamp: Timestamp da barra
            open: Preço de abertura
            high: Preço máximo
            low: Preço mínimo
            close: Preço de fechamento
            volume: Volume negociado
        """
        self.symbol = symbol
        self.timestamp = timestamp
        self.open = open
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume

    def __repr__(self) -> str:
        """Representação legível."""
        return (
            f"MarketDataBar({self.symbol} @ {self.timestamp}: "
            f"O={self.open} H={self.high} L={self.low} C={self.close} V={self.volume})"
        )


class MarketDataRepository(ABC):
    """
    Interface abstrata para acesso a dados de mercado.

    Implementei seguindo Repository Pattern. A implementação concreta
    pode buscar dados de APIs (Finnhub, Alpha Vantage), cache local,
    ou banco de dados.

    Decidi separar leitura histórica de real-time para otimizar cada caso.
    """

    @abstractmethod
    def get_historical(
        self,
        symbol: Symbol,
        time_range: TimeRange,
        interval: str = "1d"
    ) -> List[MarketDataBar]:
        """
        Busco dados históricos para um símbolo.

        Implementação deve cachear dados quando possível para evitar
        rate limiting de APIs externas.

        Args:
            symbol: Símbolo do ativo
            time_range: Range de tempo desejado
            interval: Intervalo (1m, 5m, 15m, 1h, 1d, etc)

        Returns:
            Lista de barras OHLCV ordenadas por timestamp

        Raises:
            MarketDataNotAvailableError: Se dados não disponíveis
            MarketDataAPIError: Se API falhar
        """
        pass

    @abstractmethod
    def get_latest(self, symbol: Symbol) -> Optional[MarketDataBar]:
        """
        Busco última barra disponível para símbolo.

        Útil para obter preço atual em live trading.

        Args:
            symbol: Símbolo do ativo

        Returns:
            Última barra disponível ou None

        Raises:
            MarketDataAPIError: Se API falhar
        """
        pass

    @abstractmethod
    def cache(
        self,
        symbol: Symbol,
        bars: List[MarketDataBar],
        interval: str = "1d"
    ) -> None:
        """
        Cacheia dados de mercado localmente.

        Implementei método explícito de cache para otimizar backtests
        repetidos e evitar rate limiting.

        Args:
            symbol: Símbolo do ativo
            bars: Barras a cachear
            interval: Intervalo dos dados

        Raises:
            CacheError: Se cache falhar
        """
        pass

    @abstractmethod
    def is_cached(
        self,
        symbol: Symbol,
        time_range: TimeRange,
        interval: str = "1d"
    ) -> bool:
        """
        Verifico se dados estão cacheados.

        Útil para decidir se preciso buscar de API ou posso usar cache.

        Args:
            symbol: Símbolo do ativo
            time_range: Range de tempo
            interval: Intervalo

        Returns:
            True se dados completos estão em cache
        """
        pass

    @abstractmethod
    def clear_cache(self, symbol: Optional[Symbol] = None) -> None:
        """
        Limpo cache de market data.

        Args:
            symbol: Se fornecido, limpa apenas este símbolo. Se None, limpa tudo.
        """
        pass


class MarketDataNotAvailableError(Exception):
    """Dados de mercado não disponíveis para o período solicitado."""

    def __init__(self, symbol: str, time_range: TimeRange):
        super().__init__(
            f"Market data not available for {symbol} in range {time_range}"
        )
        self.symbol = symbol
        self.time_range = time_range


class MarketDataAPIError(Exception):
    """Erro ao buscar dados de API externa."""

    def __init__(self, api_name: str, message: str):
        super().__init__(f"Market data API error ({api_name}): {message}")
        self.api_name = api_name
        self.original_message = message


class CacheError(Exception):
    """Erro ao cachear ou ler dados do cache."""
    pass