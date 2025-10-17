"""
Strategy Service - gerenciamento de estratégias.

Implementei CRUD de estratégias com validação de negócio.
"""

from typing import List, Optional
from uuid import UUID

from domain.entities.strategy import Strategy
from domain.repositories.strategy_repository import (
    StrategyRepository,
    DuplicateStrategyError,
)
from infrastructure.telemetry.loki_logger import get_logger


class StrategyService:
    """
    Service de gerenciamento de estratégias.

    Implementei lógica de negócio para CRUD de estratégias.
    """

    def __init__(self, repository: StrategyRepository):
        """
        Construtor com dependency injection.

        Args:
            repository: Strategy repository
        """
        self._repo = repository
        self._logger = get_logger()

    def create(self, strategy: Strategy) -> Strategy:
        """
        Crio nova estratégia.

        Args:
            strategy: Estratégia a criar

        Returns:
            Estratégia criada

        Raises:
            DuplicateStrategyError: Se nome já existe
        """
        # Verifico duplicata
        existing = self._repo.find_by_name(strategy.name)
        if existing:
            raise DuplicateStrategyError(strategy.name)

        saved = self._repo.save(strategy)
        self._logger.info(f"Created strategy: {saved.name}", strategy_id=str(saved.id))
        return saved

    def update(self, strategy: Strategy) -> Strategy:
        """
        Atualizo estratégia existente.

        Args:
            strategy: Estratégia a atualizar

        Returns:
            Estratégia atualizada
        """
        updated = self._repo.save(strategy)
        self._logger.info(f"Updated strategy: {updated.name}", strategy_id=str(updated.id))
        return updated

    def get_by_id(self, strategy_id: UUID) -> Optional[Strategy]:
        """Busco estratégia por ID."""
        return self._repo.find_by_id(strategy_id)

    def list_all(
        self, active_only: bool = False, strategy_type: Optional[str] = None
    ) -> List[Strategy]:
        """
        Listo estratégias com filtros.

        Args:
            active_only: Apenas ativas
            strategy_type: Filtrar por tipo

        Returns:
            Lista de estratégias
        """
        return self._repo.find_all(
            active_only=active_only, strategy_type=strategy_type
        )

    def delete(self, strategy_id: UUID) -> bool:
        """
        Deleto estratégia.

        Args:
            strategy_id: ID da estratégia

        Returns:
            True se deletado
        """
        deleted = self._repo.delete(strategy_id)
        if deleted:
            self._logger.info("Deleted strategy", strategy_id=str(strategy_id))
        return deleted