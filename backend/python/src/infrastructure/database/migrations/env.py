"""
Alembic environment configuration.

Implementei configuração do Alembic para migrations automáticas.
Decidi usar autogenerate para detectar mudanças nos models.

Referência: https://alembic.sqlalchemy.org/en/latest/autogenerate.html
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# Importo Base e settings
# Ajusto sys.path para importar do projeto
import sys
from pathlib import Path

# Adiciono src ao path
src_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(src_path))

from config.settings import get_settings
from infrastructure.database.models import Base

# this is the Alembic Config object
config = context.config

# Sobrescrevo database URL com settings
# Decidi usar settings para manter consistência
settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata do SQLAlchemy para autogenerate
# Implementei usando Base.metadata que contém todos os models
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Implementei modo offline para gerar SQL scripts sem conexão ao DB.
    Útil para revisão de migrations antes de aplicar.

    Referência: https://alembic.sqlalchemy.org/en/latest/offline.html
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,  # Detecta mudanças de tipo
        compare_server_default=True,  # Detecta mudanças de default
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Implementei modo online para aplicar migrations diretamente no DB.
    Uso connection pooling para eficiência.

    Referência: https://alembic.sqlalchemy.org/en/latest/tutorial.html
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # Não uso pooling em migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,  # Detecta mudanças de tipo
            compare_server_default=True,  # Detecta mudanças de default
        )

        with context.begin_transaction():
            context.run_migrations()


# Decido qual modo usar baseado em context
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()