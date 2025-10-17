"""Initial schema

Revision ID: 001_initial
Revises:
Create Date: 2025-10-16 00:00:00.000000

Implementei a migration inicial criando todas as tabelas base do sistema.
Decidi criar indexes otimizados desde o início para performance.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Upgrade schema - crio todas as tabelas.

    Implementei na ordem correta respeitando foreign keys:
    1. strategies (sem dependências)
    2. users (sem dependências)
    3. backtests (depende de strategies)
    4. trades (depende de backtests e strategies)
    5. market_data_cache (sem dependências)
    """
    # ========== Strategies Table ==========
    op.create_table(
        'strategies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('strategy_type', sa.String(length=50), nullable=False),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index('ix_strategies_name', 'strategies', ['name'])
    op.create_index('ix_strategies_strategy_type', 'strategies', ['strategy_type'])
    op.create_index('ix_strategies_is_active', 'strategies', ['is_active'])
    op.create_index('ix_strategies_type_active', 'strategies', ['strategy_type', 'is_active'])

    # ========== Users Table ==========
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_users_email', 'users', ['email'])

    # ========== Backtests Table ==========
    op.create_table(
        'backtests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('symbols', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.Column('execution_time_seconds', sa.Float(), nullable=True),
        sa.Column('initial_capital', sa.Float(), nullable=False),
        sa.Column('final_capital', sa.Float(), nullable=True),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('total_trades', sa.Integer(), nullable=True),
        sa.Column('winning_trades', sa.Integer(), nullable=True),
        sa.Column('losing_trades', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_backtests_strategy_id', 'backtests', ['strategy_id'])
    op.create_index('ix_backtests_status', 'backtests', ['status'])
    op.create_index('ix_backtests_strategy_status', 'backtests', ['strategy_id', 'status'])
    op.create_index('ix_backtests_date_range', 'backtests', ['start_date', 'end_date'])

    # ========== Trades Table ==========
    op.create_table(
        'trades',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('backtest_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('strategy_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('quantity', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('commission', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('signal_confidence', sa.Float(), nullable=True),
        sa.Column('slippage', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['backtest_id'], ['backtests.id'], ),
        sa.ForeignKeyConstraint(['strategy_id'], ['strategies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_trades_backtest_id', 'trades', ['backtest_id'])
    op.create_index('ix_trades_strategy_id', 'trades', ['strategy_id'])
    op.create_index('ix_trades_symbol', 'trades', ['symbol'])
    op.create_index('ix_trades_timestamp', 'trades', ['timestamp'])
    op.create_index('ix_trades_backtest_symbol', 'trades', ['backtest_id', 'symbol'])
    op.create_index('ix_trades_timestamp_symbol', 'trades', ['timestamp', 'symbol'])

    # ========== Market Data Cache Table ==========
    op.create_table(
        'market_data_cache',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('symbol', sa.String(length=20), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('interval', sa.String(length=10), nullable=False),
        sa.Column('open', sa.Float(), nullable=False),
        sa.Column('high', sa.Float(), nullable=False),
        sa.Column('low', sa.Float(), nullable=False),
        sa.Column('close', sa.Float(), nullable=False),
        sa.Column('volume', sa.Float(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('cached_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_market_data_cache_symbol', 'market_data_cache', ['symbol'])
    op.create_index('ix_market_data_cache_timestamp', 'market_data_cache', ['timestamp'])
    op.create_index('ix_market_data_cached_at', 'market_data_cache', ['cached_at'])
    op.create_index(
        'ix_market_data_symbol_timestamp',
        'market_data_cache',
        ['symbol', 'timestamp', 'interval'],
        unique=True
    )


def downgrade() -> None:
    """
    Downgrade schema - removo todas as tabelas.

    Implementei na ordem reversa respeitando foreign keys.
    """
    op.drop_table('market_data_cache')
    op.drop_table('trades')
    op.drop_table('backtests')
    op.drop_table('users')
    op.drop_table('strategies')