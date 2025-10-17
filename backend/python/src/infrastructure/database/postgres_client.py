"""
PostgreSQL Client com connection pooling.

Implementei cliente robusto com pooling e session management.
Decidi usar context managers para garantir cleanup automático.

Referências:
- SQLAlchemy Engine: https://docs.sqlalchemy.org/en/20/core/engines.html
- Connection Pooling: https://docs.sqlalchemy.org/en/20/core/pooling.html
"""

from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, pool, Engine
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.exc import SQLAlchemyError

from config.settings import get_settings
from infrastructure.database.models import Base


class PostgresClient:
    """
    Cliente PostgreSQL com connection pooling.

    Implementei seguindo singleton pattern para garantir apenas uma engine
    por aplicação. Uso QueuePool para connection pooling eficiente.

    Referência: SQLAlchemy Engine Configuration
    https://docs.sqlalchemy.org/en/20/core/engines.html
    """

    _instance: Optional["PostgresClient"] = None
    _engine: Optional[Engine] = None

    def __new__(cls) -> "PostgresClient":
        """
        Implemento singleton para garantir única instância.

        Decidi usar singleton porque múltiplas engines causariam
        overhead desnecessário de conexões.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Inicializo cliente PostgreSQL."""
        if self._engine is None:
            self._initialize_engine()

    def _initialize_engine(self) -> None:
        """
        Inicializo SQLAlchemy engine com pooling otimizado.

        Implementei configurações de pool baseadas em best practices:
        - pool_size=10: Conexões permanentes no pool
        - max_overflow=20: Conexões extras em picos
        - pool_pre_ping=True: Verifica conexões antes de usar
        - pool_recycle=3600: Recicla conexões a cada hora
        """
        settings = get_settings()

        # Crio engine com QueuePool otimizado
        # Decidi usar QueuePool porque é thread-safe e eficiente
        self._engine = create_engine(
            settings.database_url,
            poolclass=pool.QueuePool,
            pool_size=10,  # Conexões permanentes
            max_overflow=20,  # Conexões extras permitidas
            pool_pre_ping=True,  # Verifica conexão antes de usar
            pool_recycle=3600,  # Recicla conexões a cada hora (previne stale connections)
            echo=False,  # Log de queries (True para debug)
            future=True,  # SQLAlchemy 2.0 style
        )

        # Session factory
        # Uso scoped_session para thread-safety
        self._session_factory = scoped_session(
            sessionmaker(
                bind=self._engine,
                autocommit=False,
                autoflush=False,
                expire_on_commit=False,  # Evita lazy loading após commit
            )
        )

        # Event listeners para logging e debugging
        self._setup_event_listeners()

    def _setup_event_listeners(self) -> None:
        """
        Configuro event listeners para logging e debugging.

        Implementei listeners úteis para diagnóstico de problemas.
        """
        @event.listens_for(self._engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """
            Executado quando nova conexão é criada.

            Uso para configurar session-level settings do PostgreSQL.
            """
            # Configuro timezone para UTC
            cursor = dbapi_conn.cursor()
            cursor.execute("SET timezone TO 'UTC'")
            cursor.close()

        @event.listens_for(self._engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """
            Executado quando conexão é retirada do pool.

            Útil para debug de pool exhaustion.
            """
            pass  # Implementar logging se necessário

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager para obter session com auto-cleanup.

        Implementei usando context manager para garantir que sessions
        sejam sempre fechadas, mesmo em caso de exceção.

        Uso:
            with client.get_session() as session:
                result = session.query(Strategy).all()

        Yields:
            Session SQLAlchemy

        Raises:
            SQLAlchemyError: Se operação de database falhar
        """
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise
        finally:
            session.close()

    def create_tables(self) -> None:
        """
        Crio todas as tabelas no database.

        Uso apenas para desenvolvimento. Em produção, usar migrations (Alembic).

        Referência: https://docs.sqlalchemy.org/en/20/core/metadata.html
        """
        if self._engine is None:
            raise RuntimeError("Engine not initialized")
        Base.metadata.create_all(bind=self._engine)

    def drop_tables(self) -> None:
        """
        Deleto todas as tabelas (PERIGOSO!).

        Uso apenas em testes. NUNCA executar em produção.
        """
        if self._engine is None:
            raise RuntimeError("Engine not initialized")
        Base.metadata.drop_all(bind=self._engine)

    def get_engine(self) -> Engine:
        """
        Retorno engine SQLAlchemy.

        Útil para operações que precisam da engine diretamente.

        Returns:
            SQLAlchemy Engine
        """
        if self._engine is None:
            raise RuntimeError("Engine not initialized")
        return self._engine

    def close(self) -> None:
        """
        Fecho todas as conexões e dispose engine.

        Uso no shutdown da aplicação para cleanup.
        """
        if self._engine is not None:
            self._session_factory.remove()
            self._engine.dispose()
            self._engine = None

    def get_pool_status(self) -> dict:
        """
        Retorno status do connection pool.

        Útil para monitoramento e debugging de pool exhaustion.

        Returns:
            Dict com estatísticas do pool
        """
        if self._engine is None:
            raise RuntimeError("Engine not initialized")

        pool_obj = self._engine.pool
        return {
            "pool_size": pool_obj.size(),
            "checked_in": pool_obj.checkedin(),
            "checked_out": pool_obj.checkedout(),
            "overflow": pool_obj.overflow(),
            "total_connections": pool_obj.size() + pool_obj.overflow(),
        }


# Singleton instance
# Decidi exportar instância global para facilitar uso
_postgres_client: Optional[PostgresClient] = None


def get_postgres_client() -> PostgresClient:
    """
    Retorno singleton do PostgresClient.

    Implementei factory function para acesso global consistente.

    Returns:
        PostgresClient instance
    """
    global _postgres_client
    if _postgres_client is None:
        _postgres_client = PostgresClient()
    return _postgres_client


# Cleanup function para shutdown
def close_postgres_client() -> None:
    """
    Fecho client PostgreSQL no shutdown.

    Uso em handlers de shutdown da aplicação.
    """
    global _postgres_client
    if _postgres_client is not None:
        _postgres_client.close()
        _postgres_client = None