"""
Strategy Repository Interface - DDD Domain Layer.

Implementei como ABC (Abstract Base Class) seguindo Repository Pattern.
A implementação concreta virá na infrastructure layer.

Referências:
- Repository Pattern: https://martinfowler.com/eaaCatalog/repository.html
- Dependency Inversion Principle: https://en.wikipedia.org/wiki/Dependency_inversion_principle
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.entities.strategy import Strategy


class StrategyRepository(ABC):
    """
    Interface abstrata para persistência de Strategy entities.

    Implementei seguindo Repository Pattern para desacoplar domain de infrastructure.
    A implementação concreta (PostgreSQL, MongoDB, etc) virá na infra layer.

    Decidi usar ABC do Python para garantir que implementações concretas
    forneçam todos os métodos necessários.

    Referência: Repository Pattern
    https://martinfowler.com/eaaCatalog/repository.html
    """

    @abstractmethod
    def save(self, strategy: Strategy) -> Strategy:
        """
        Persisto ou atualizo uma estratégia.

        Implementação deve decidir se é INSERT ou UPDATE baseado na existência do ID.

        Args:
            strategy: Estratégia a persistir

        Returns:
            Estratégia persistida (pode ter campos atualizados pelo DB)

        Raises:
            RepositoryError: Se persistência falhar
        """
        pass

    @abstractmethod
    def find_by_id(self, strategy_id: UUID) -> Optional[Strategy]:
        """
        Busco estratégia por ID.

        Args:
            strategy_id: UUID da estratégia

        Returns:
            Strategy se encontrada, None caso contrário

        Raises:
            RepositoryError: Se busca falhar
        """
        pass

    @abstractmethod
    def find_by_name(self, name: str) -> Optional[Strategy]:
        """
        Busco estratégia por nome.

        Útil para evitar duplicatas de estratégias com mesmo nome.

        Args:
            name: Nome da estratégia

        Returns:
            Strategy se encontrada, None caso contrário
        """
        pass

    @abstractmethod
    def find_all(
        self,
        active_only: bool = False,
        strategy_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Strategy]:
        """
        Busco todas as estratégias com filtros opcionais.

        Implementei paginação para evitar carregar milhares de registros.

        Args:
            active_only: Se True, retorna apenas estratégias ativas
            strategy_type: Filtrar por tipo (SMA, MACD, RSI)
            limit: Máximo de resultados (padrão 100)
            offset: Offset para paginação

        Returns:
            Lista de Strategy entities

        Raises:
            RepositoryError: Se busca falhar
        """
        pass

    @abstractmethod
    def delete(self, strategy_id: UUID) -> bool:
        """
        Deleto estratégia por ID.

        Implementação pode fazer soft delete (marcar como inativa) ou hard delete.

        Args:
            strategy_id: UUID da estratégia a deletar

        Returns:
            True se deletado, False se não encontrado

        Raises:
            RepositoryError: Se deleção falhar
        """
        pass

    @abstractmethod
    def count(self, active_only: bool = False) -> int:
        """
        Conto número de estratégias.

        Útil para paginação e estatísticas.

        Args:
            active_only: Se True, conta apenas estratégias ativas

        Returns:
            Número de estratégias
        """
        pass

    @abstractmethod
    def exists(self, strategy_id: UUID) -> bool:
        """
        Verifico se estratégia existe.

        Mais eficiente que find_by_id quando só preciso verificar existência.

        Args:
            strategy_id: UUID da estratégia

        Returns:
            True se existe, False caso contrário
        """
        pass


class RepositoryError(Exception):
    """
    Exceção base para erros de repository.

    Implementei hierarquia de exceções para facilitar error handling.
    """
    pass


class StrategyNotFoundError(RepositoryError):
    """Estratégia não encontrada."""
    def __init__(self, strategy_id: UUID):
        super().__init__(f"Strategy with id {strategy_id} not found")
        self.strategy_id = strategy_id


class DuplicateStrategyError(RepositoryError):
    """Estratégia duplicada (nome já existe)."""
    def __init__(self, name: str):
        super().__init__(f"Strategy with name '{name}' already exists")
        self.name = name