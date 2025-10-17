"""
Integration Tests - Database Integration (PostgreSQL)
Implementei estes testes para validar repositórios com banco real
Decidi testar: CRUD operations, transactions, queries complexas
"""

import pytest
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List
from uuid import uuid4, UUID
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Importações do projeto
from backend.python.src.infrastructure.database.models import Base, StrategyModel, BacktestModel, PositionModel, TradeModel
from backend.python.src.infrastructure.database.strategy_repository_impl import StrategyRepositoryImpl
from backend.python.src.infrastructure.database.postgres_client import PostgresClient
from backend.python.src.domain.entities.strategy import Strategy, StrategyType
from backend.python.src.domain.entities.backtest import Backtest, BacktestStatus
from backend.python.src.domain.value_objects import Symbol, TimeRange, StrategyParameters


# Database URL de teste
TEST_DB_URL = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql://nexus_user:nexus_password@localhost:5433/nexus_test'
)


@pytest.fixture(scope="session")
def test_engine():
    """
    Implementei este fixture para criar engine de teste
    Decidi usar scope=session para reutilizar conexão
    """
    engine = create_engine(TEST_DB_URL, echo=False)
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_db(test_engine):
    """
    Implementei este fixture para criar/limpar schema de teste
    Decidi usar scope=function para isolamento total entre testes
    """
    # Create all tables
    Base.metadata.create_all(test_engine)

    # Create session
    Session = sessionmaker(bind=test_engine)
    session = Session()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(test_engine)


@pytest.fixture
def strategy_repository(test_db):
    """
    Implementei este fixture para criar repository com DB real
    """
    return StrategyRepositoryImpl(session=test_db)


@pytest.mark.integration
@pytest.mark.database
class TestStrategyRepository:
    """
    Implementei esta classe para testar StrategyRepository com PostgreSQL real
    """

    def test_create_strategy(self, strategy_repository: StrategyRepositoryImpl, test_db: Session):
        """
        Implementei este teste para validar criação de estratégia no DB
        """
        # Arrange
        strategy = Strategy(
            id=uuid4(),
            name="Test SMA Strategy",
            strategy_type=StrategyType.SMA_CROSSOVER,
            parameters=StrategyParameters(
                params={
                    "fast_period": 50,
                    "slow_period": 200
                }
            ),
            is_active=True,
            created_at=datetime.now()
        )

        # Act
        created = strategy_repository.create(strategy)
        test_db.commit()

        # Assert
        assert created is not None
        assert created.id == strategy.id
        assert created.name == strategy.name

        # Verificar que foi persistido
        found = strategy_repository.get_by_id(strategy.id)
        assert found is not None
        assert found.name == "Test SMA Strategy"

    def test_get_by_id(self, strategy_repository: StrategyRepositoryImpl, test_db: Session):
        """
        Implementei este teste para validar busca por ID
        """
        # Arrange
        strategy = Strategy(
            id=uuid4(),
            name="Test Strategy",
            strategy_type=StrategyType.RSI_STRATEGY,
            parameters=StrategyParameters(params={"period": 14}),
            is_active=True,
            created_at=datetime.now()
        )
        strategy_repository.create(strategy)
        test_db.commit()

        # Act
        found = strategy_repository.get_by_id(strategy.id)

        # Assert
        assert found is not None
        assert found.id == strategy.id
        assert found.strategy_type == StrategyType.RSI_STRATEGY

    def test_get_by_id_not_found(self, strategy_repository: StrategyRepositoryImpl):
        """
        Implementei este teste para validar busca de ID inexistente
        """
        # Arrange
        non_existent_id = uuid4()

        # Act
        found = strategy_repository.get_by_id(non_existent_id)

        # Assert
        assert found is None

    def test_list_all_strategies(self, strategy_repository: StrategyRepositoryImpl, test_db: Session):
        """
        Implementei este teste para validar listagem de todas as estratégias
        """
        # Arrange - criar 3 estratégias
        strategies = [
            Strategy(
                id=uuid4(),
                name=f"Strategy {i}",
                strategy_type=StrategyType.SMA_CROSSOVER,
                parameters=StrategyParameters(params={"fast_period": 50}),
                is_active=True,
                created_at=datetime.now()
            )
            for i in range(3)
        ]

        for strategy in strategies:
            strategy_repository.create(strategy)
        test_db.commit()

        # Act
        all_strategies = strategy_repository.list_all()

        # Assert
        assert len(all_strategies) == 3
        names = [s.name for s in all_strategies]
        assert "Strategy 0" in names
        assert "Strategy 1" in names
        assert "Strategy 2" in names

    def test_update_strategy(self, strategy_repository: StrategyRepositoryImpl, test_db: Session):
        """
        Implementei este teste para validar atualização de estratégia
        """
        # Arrange
        strategy = Strategy(
            id=uuid4(),
            name="Original Name",
            strategy_type=StrategyType.MACD_STRATEGY,
            parameters=StrategyParameters(params={"fast_period": 12}),
            is_active=True,
            created_at=datetime.now()
        )
        strategy_repository.create(strategy)
        test_db.commit()

        # Act - atualizar nome
        strategy.name = "Updated Name"
        strategy.is_active = False
        updated = strategy_repository.update(strategy)
        test_db.commit()

        # Assert
        assert updated.name == "Updated Name"
        assert updated.is_active is False

        # Verificar persistência
        found = strategy_repository.get_by_id(strategy.id)
        assert found.name == "Updated Name"
        assert found.is_active is False

    def test_delete_strategy(self, strategy_repository: StrategyRepositoryImpl, test_db: Session):
        """
        Implementei este teste para validar deleção de estratégia
        """
        # Arrange
        strategy = Strategy(
            id=uuid4(),
            name="To Delete",
            strategy_type=StrategyType.SMA_CROSSOVER,
            parameters=StrategyParameters(params={"fast_period": 50}),
            is_active=True,
            created_at=datetime.now()
        )
        strategy_repository.create(strategy)
        test_db.commit()

        # Act
        result = strategy_repository.delete(strategy.id)
        test_db.commit()

        # Assert
        assert result is True

        # Verificar que foi deletado
        found = strategy_repository.get_by_id(strategy.id)
        assert found is None

    def test_filter_active_strategies(self, strategy_repository: StrategyRepositoryImpl, test_db: Session):
        """
        Implementei este teste para validar filtro de estratégias ativas
        """
        # Arrange
        active_strategy = Strategy(
            id=uuid4(),
            name="Active",
            strategy_type=StrategyType.SMA_CROSSOVER,
            parameters=StrategyParameters(params={"fast_period": 50}),
            is_active=True,
            created_at=datetime.now()
        )

        inactive_strategy = Strategy(
            id=uuid4(),
            name="Inactive",
            strategy_type=StrategyType.RSI_STRATEGY,
            parameters=StrategyParameters(params={"period": 14}),
            is_active=False,
            created_at=datetime.now()
        )

        strategy_repository.create(active_strategy)
        strategy_repository.create(inactive_strategy)
        test_db.commit()

        # Act
        active_strategies = strategy_repository.find_by_active(is_active=True)

        # Assert
        assert len(active_strategies) == 1
        assert active_strategies[0].name == "Active"


@pytest.mark.integration
@pytest.mark.database
class TestBacktestRepository:
    """
    Implementei esta classe para testar BacktestRepository com PostgreSQL
    """

    @pytest.fixture
    def backtest_repository(self, test_db):
        """
        Implementei este fixture para backtest repository
        """
        from backend.python.src.infrastructure.database.backtest_repository_impl import BacktestRepositoryImpl
        return BacktestRepositoryImpl(session=test_db)

    @pytest.fixture
    def sample_strategy(self, strategy_repository, test_db):
        """
        Implementei este fixture para criar estratégia de teste
        """
        strategy = Strategy(
            id=uuid4(),
            name="Sample Strategy",
            strategy_type=StrategyType.SMA_CROSSOVER,
            parameters=StrategyParameters(params={"fast_period": 50}),
            is_active=True,
            created_at=datetime.now()
        )
        created = strategy_repository.create(strategy)
        test_db.commit()
        return created

    def test_create_backtest(self, backtest_repository, sample_strategy, test_db):
        """
        Implementei este teste para validar criação de backtest
        """
        # Arrange
        backtest = Backtest(
            id=uuid4(),
            strategy_id=sample_strategy.id,
            symbol=Symbol(value="AAPL"),
            time_range=TimeRange(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31)
            ),
            status=BacktestStatus.PENDING,
            created_at=datetime.now()
        )

        # Act
        created = backtest_repository.create(backtest)
        test_db.commit()

        # Assert
        assert created is not None
        assert created.strategy_id == sample_strategy.id
        assert created.symbol.value == "AAPL"

    def test_update_backtest_status(self, backtest_repository, sample_strategy, test_db):
        """
        Implementei este teste para validar atualização de status
        """
        # Arrange
        backtest = Backtest(
            id=uuid4(),
            strategy_id=sample_strategy.id,
            symbol=Symbol(value="GOOGL"),
            time_range=TimeRange(
                start_date=datetime(2024, 1, 1),
                end_date=datetime(2024, 12, 31)
            ),
            status=BacktestStatus.PENDING,
            created_at=datetime.now()
        )
        backtest_repository.create(backtest)
        test_db.commit()

        # Act - atualizar para RUNNING
        backtest.status = BacktestStatus.RUNNING
        updated = backtest_repository.update(backtest)
        test_db.commit()

        # Assert
        assert updated.status == BacktestStatus.RUNNING

        # Atualizar para COMPLETED com results
        backtest.status = BacktestStatus.COMPLETED
        backtest.results = {
            'total_return': 0.15,
            'sharpe_ratio': 1.5
        }
        updated = backtest_repository.update(backtest)
        test_db.commit()

        # Verificar persistência
        found = backtest_repository.get_by_id(backtest.id)
        assert found.status == BacktestStatus.COMPLETED
        assert found.results['total_return'] == 0.15

    def test_list_backtests_by_strategy(self, backtest_repository, sample_strategy, test_db):
        """
        Implementei este teste para validar listagem por estratégia
        """
        # Arrange - criar 2 backtests para mesma estratégia
        backtests = [
            Backtest(
                id=uuid4(),
                strategy_id=sample_strategy.id,
                symbol=Symbol(value=symbol),
                time_range=TimeRange(
                    start_date=datetime(2024, 1, 1),
                    end_date=datetime(2024, 12, 31)
                ),
                status=BacktestStatus.COMPLETED,
                created_at=datetime.now()
            )
            for symbol in ["AAPL", "GOOGL"]
        ]

        for backtest in backtests:
            backtest_repository.create(backtest)
        test_db.commit()

        # Act
        strategy_backtests = backtest_repository.find_by_strategy(sample_strategy.id)

        # Assert
        assert len(strategy_backtests) == 2
        symbols = [b.symbol.value for b in strategy_backtests]
        assert "AAPL" in symbols
        assert "GOOGL" in symbols


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.slow
class TestDatabaseTransactions:
    """
    Implementei esta classe para testar transações e rollback
    """

    def test_transaction_commit(self, strategy_repository, test_db):
        """
        Implementei este teste para validar commit de transação
        """
        # Arrange
        strategy = Strategy(
            id=uuid4(),
            name="Transaction Test",
            strategy_type=StrategyType.SMA_CROSSOVER,
            parameters=StrategyParameters(params={"fast_period": 50}),
            is_active=True,
            created_at=datetime.now()
        )

        # Act
        strategy_repository.create(strategy)
        test_db.commit()

        # Assert - deve estar persistido
        found = strategy_repository.get_by_id(strategy.id)
        assert found is not None

    def test_transaction_rollback(self, strategy_repository, test_db):
        """
        Implementei este teste para validar rollback de transação
        """
        # Arrange
        strategy = Strategy(
            id=uuid4(),
            name="Rollback Test",
            strategy_type=StrategyType.RSI_STRATEGY,
            parameters=StrategyParameters(params={"period": 14}),
            is_active=True,
            created_at=datetime.now()
        )

        # Act
        created = strategy_repository.create(strategy)
        strategy_id = created.id

        # Rollback antes de commit
        test_db.rollback()

        # Assert - NÃO deve estar persistido
        found = strategy_repository.get_by_id(strategy_id)
        assert found is None


@pytest.mark.integration
@pytest.mark.database
class TestComplexQueries:
    """
    Implementei esta classe para testar queries SQL complexas
    """

    def test_query_with_joins(self, strategy_repository, test_db):
        """
        Implementei este teste para validar query com JOIN
        """
        # TODO: Implementar quando houver queries com JOIN entre Strategy e Backtest
        pytest.skip("Complex JOIN queries not yet implemented")

    def test_query_with_aggregation(self, strategy_repository, test_db):
        """
        Implementei este teste para validar query com agregação (COUNT, AVG, etc)
        """
        # TODO: Implementar quando houver métodos de agregação
        pytest.skip("Aggregation queries not yet implemented")


if __name__ == "__main__":
    # Implementei este bloco para executar testes diretamente
    pytest.main([__file__, "-v", "--tb=short", "-m", "integration"])