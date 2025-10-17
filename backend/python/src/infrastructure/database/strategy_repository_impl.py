"""
Implementação concreta do StrategyRepository para PostgreSQL.

Implementei usando SQLAlchemy para persistência.
Decidi mapear entre domain entities e ORM models explicitamente.

Referências:
- Repository Pattern: https://martinfowler.com/eaaCatalog/repository.html
- SQLAlchemy ORM: https://docs.sqlalchemy.org/en/20/orm/
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from domain.entities.strategy import Strategy as StrategyEntity
from domain.repositories.strategy_repository import (
    StrategyRepository,
    RepositoryError,
    StrategyNotFoundError,
    DuplicateStrategyError,
)
from infrastructure.database.models import Strategy as StrategyModel
from infrastructure.database.postgres_client import PostgresClient


class StrategyRepositoryImpl(StrategyRepository):
    """
    Implementação PostgreSQL do StrategyRepository.

    Implementei mapeamento explícito entre domain entities e ORM models
    para manter domain layer isolado de detalhes de persistência.

    Decidi usar session do PostgresClient via context manager para
    garantir cleanup automático e transactional consistency.
    """

    def __init__(self, postgres_client: PostgresClient):
        """
        Construtor com dependency injection.

        Args:
            postgres_client: Cliente PostgreSQL
        """
        self._client = postgres_client

    def _entity_to_model(self, entity: StrategyEntity) -> StrategyModel:
        """
        Converto domain entity para ORM model.

        Implementei conversão explícita para manter separação de camadas.

        Args:
            entity: Strategy entity

        Returns:
            Strategy ORM model
        """
        return StrategyModel(
            id=entity.id,
            name=entity.name,
            strategy_type=entity.strategy_type,
            parameters=entity.parameters,
            description=entity.description,
            is_active=entity.is_active,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )

    def _model_to_entity(self, model: StrategyModel) -> StrategyEntity:
        """
        Converto ORM model para domain entity.

        Args:
            model: Strategy ORM model

        Returns:
            Strategy entity
        """
        return StrategyEntity(
            id=model.id,
            name=model.name,
            strategy_type=model.strategy_type,
            parameters=model.parameters,
            description=model.description,
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def save(self, strategy: StrategyEntity) -> StrategyEntity:
        """
        Persisto ou atualizo estratégia.

        Implementei lógica de upsert: se ID existe, faz UPDATE, senão INSERT.

        Args:
            strategy: Estratégia a persistir

        Returns:
            Estratégia persistida

        Raises:
            DuplicateStrategyError: Se nome já existe
            RepositoryError: Se persistência falhar
        """
        try:
            with self._client.get_session() as session:
                # Verifico se já existe
                existing = session.query(StrategyModel).filter_by(id=strategy.id).first()

                if existing:
                    # UPDATE
                    existing.name = strategy.name
                    existing.strategy_type = strategy.strategy_type
                    existing.parameters = strategy.parameters
                    existing.description = strategy.description
                    existing.is_active = strategy.is_active
                    existing.updated_at = strategy.updated_at
                    session.flush()
                    return self._model_to_entity(existing)
                else:
                    # INSERT
                    model = self._entity_to_model(strategy)
                    session.add(model)
                    session.flush()
                    return self._model_to_entity(model)

        except IntegrityError as e:
            # Violação de unique constraint (nome duplicado)
            if "name" in str(e.orig):
                raise DuplicateStrategyError(strategy.name)
            raise RepositoryError(f"Database integrity error: {e}")
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to save strategy: {e}")

    def find_by_id(self, strategy_id: UUID) -> Optional[StrategyEntity]:
        """
        Busco estratégia por ID.

        Args:
            strategy_id: UUID da estratégia

        Returns:
            Strategy entity ou None

        Raises:
            RepositoryError: Se busca falhar
        """
        try:
            with self._client.get_session() as session:
                model = session.query(StrategyModel).filter_by(id=strategy_id).first()
                return self._model_to_entity(model) if model else None
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to find strategy by id: {e}")

    def find_by_name(self, name: str) -> Optional[StrategyEntity]:
        """
        Busco estratégia por nome.

        Args:
            name: Nome da estratégia

        Returns:
            Strategy entity ou None
        """
        try:
            with self._client.get_session() as session:
                model = session.query(StrategyModel).filter_by(name=name).first()
                return self._model_to_entity(model) if model else None
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to find strategy by name: {e}")

    def find_all(
        self,
        active_only: bool = False,
        strategy_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[StrategyEntity]:
        """
        Busco todas as estratégias com filtros.

        Implementei com paginação para evitar carregar muitos registros.

        Args:
            active_only: Filtrar apenas ativas
            strategy_type: Filtrar por tipo
            limit: Máximo de resultados
            offset: Offset para paginação

        Returns:
            Lista de Strategy entities
        """
        try:
            with self._client.get_session() as session:
                query = session.query(StrategyModel)

                # Aplico filtros
                if active_only:
                    query = query.filter_by(is_active=True)

                if strategy_type:
                    query = query.filter_by(strategy_type=strategy_type)

                # Ordeno por updated_at DESC (mais recentes primeiro)
                query = query.order_by(StrategyModel.updated_at.desc())

                # Paginação
                query = query.limit(limit).offset(offset)

                models = query.all()
                return [self._model_to_entity(m) for m in models]

        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to find strategies: {e}")

    def delete(self, strategy_id: UUID) -> bool:
        """
        Deleto estratégia por ID.

        Implementei hard delete. Considerar soft delete em produção.

        Args:
            strategy_id: UUID da estratégia

        Returns:
            True se deletado, False se não encontrado
        """
        try:
            with self._client.get_session() as session:
                model = session.query(StrategyModel).filter_by(id=strategy_id).first()
                if model:
                    session.delete(model)
                    return True
                return False
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to delete strategy: {e}")

    def count(self, active_only: bool = False) -> int:
        """
        Conto número de estratégias.

        Args:
            active_only: Contar apenas ativas

        Returns:
            Número de estratégias
        """
        try:
            with self._client.get_session() as session:
                query = session.query(StrategyModel)
                if active_only:
                    query = query.filter_by(is_active=True)
                return query.count()
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to count strategies: {e}")

    def exists(self, strategy_id: UUID) -> bool:
        """
        Verifico se estratégia existe.

        Implementei query otimizada que retorna apenas boolean.

        Args:
            strategy_id: UUID da estratégia

        Returns:
            True se existe
        """
        try:
            with self._client.get_session() as session:
                return (
                    session.query(StrategyModel.id)
                    .filter_by(id=strategy_id)
                    .first()
                    is not None
                )
        except SQLAlchemyError as e:
            raise RepositoryError(f"Failed to check strategy existence: {e}")