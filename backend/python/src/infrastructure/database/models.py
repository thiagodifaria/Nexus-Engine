"""
SQLAlchemy Models para PostgreSQL.

Implementei estes models seguindo práticas do SQLAlchemy 2.0.
Decidi usar declarative base para mapeamento ORM limpo.

Referências:
- SQLAlchemy 2.0 Documentation: https://docs.sqlalchemy.org/en/20/
- PostgreSQL Best Practices: https://wiki.postgresql.org/wiki/Don't_Do_This
"""

from datetime import datetime
from typing import Dict
from uuid import uuid4

from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, String, Text, JSON, ForeignKey, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship

# Base para todos os models
# Decidi usar declarative_base do SQLAlchemy 2.0
Base = declarative_base()


class Strategy(Base):
    """
    Model SQLAlchemy para Strategy entity.

    Implementei mapeamento direto da domain entity para tabela PostgreSQL.
    Uso UUID como primary key para distribuição e unicidade global.
    """

    __tablename__ = "strategies"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Core fields
    name = Column(String(255), nullable=False, unique=True, index=True)
    strategy_type = Column(String(50), nullable=False, index=True)
    parameters = Column(JSON, nullable=False, default=dict)

    # Metadata
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    backtests = relationship("Backtest", back_populates="strategy", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_strategies_type_active", "strategy_type", "is_active"),
    )

    def __repr__(self) -> str:
        """Representação legível."""
        return f"<Strategy(id={self.id}, name='{self.name}', type='{self.strategy_type}')>"


class Backtest(Base):
    """
    Model SQLAlchemy para Backtest entity.

    Implementei com foreign key para Strategy e JSON para métricas flexíveis.
    """

    __tablename__ = "backtests"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False, index=True)

    # Configuration
    symbols = Column(JSON, nullable=False)  # Lista de símbolos
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)

    # Execution metadata
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    execution_time_seconds = Column(Float, nullable=True)

    # Results
    initial_capital = Column(Float, nullable=False, default=10000.0)
    final_capital = Column(Float, nullable=True)
    metrics = Column(JSON, nullable=False, default=dict)

    # Trade summary
    total_trades = Column(Integer, nullable=True)
    winning_trades = Column(Integer, nullable=True)
    losing_trades = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), nullable=False, default="pending", index=True)
    error_message = Column(Text, nullable=True)

    # Relationships
    strategy = relationship("Strategy", back_populates="backtests")
    trades = relationship("Trade", back_populates="backtest", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("ix_backtests_strategy_status", "strategy_id", "status"),
        Index("ix_backtests_date_range", "start_date", "end_date"),
    )

    def __repr__(self) -> str:
        """Representação legível."""
        return f"<Backtest(id={self.id}, strategy_id={self.strategy_id}, status='{self.status}')>"


class Trade(Base):
    """
    Model SQLAlchemy para Trade entity.

    Implementei para histórico completo de trades executados.
    Cada trade é imutável após inserção (append-only log).
    """

    __tablename__ = "trades"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Foreign Keys
    backtest_id = Column(UUID(as_uuid=True), ForeignKey("backtests.id"), nullable=True, index=True)
    strategy_id = Column(UUID(as_uuid=True), ForeignKey("strategies.id"), nullable=True, index=True)

    # Trade details
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(String(10), nullable=False)  # BUY, SELL
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, nullable=False, default=0.0)

    # Timestamp
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Optional metadata
    signal_confidence = Column(Float, nullable=True)
    slippage = Column(Float, nullable=True)

    # Relationships
    backtest = relationship("Backtest", back_populates="trades")

    # Indexes
    __table_args__ = (
        Index("ix_trades_backtest_symbol", "backtest_id", "symbol"),
        Index("ix_trades_timestamp_symbol", "timestamp", "symbol"),
    )

    def __repr__(self) -> str:
        """Representação legível."""
        return f"<Trade(id={self.id}, {self.side} {self.quantity} {self.symbol} @ {self.price})>"


class MarketDataCache(Base):
    """
    Model para cache de dados de mercado.

    Implementei tabela de cache para evitar rate limiting de APIs externas.
    Uso composite unique constraint em (symbol, timestamp, interval).
    """

    __tablename__ = "market_data_cache"

    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Market data fields
    symbol = Column(String(20), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    interval = Column(String(10), nullable=False, default="1d")  # 1m, 5m, 1h, 1d, etc

    # OHLCV data
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)

    # Cache metadata
    source = Column(String(50), nullable=True)  # finnhub, alpha_vantage, etc
    cached_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Indexes e constraints
    __table_args__ = (
        Index("ix_market_data_symbol_timestamp", "symbol", "timestamp", "interval", unique=True),
        Index("ix_market_data_cached_at", "cached_at"),
    )

    def __repr__(self) -> str:
        """Representação legível."""
        return f"<MarketDataCache({self.symbol} @ {self.timestamp}: C={self.close})>"


class User(Base):
    """
    Model para usuários do sistema.

    Implementei para futuro sistema de autenticação multi-usuário.
    Por enquanto, campos básicos para identificação.
    """

    __tablename__ = "users"

    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # User info
    username = Column(String(100), nullable=False, unique=True, index=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    full_name = Column(String(255), nullable=True)

    # Auth (hashed password - implementação futura)
    hashed_password = Column(String(255), nullable=True)

    # Metadata
    is_active = Column(Boolean, nullable=False, default=True)
    is_admin = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """Representação legível."""
        return f"<User(id={self.id}, username='{self.username}')>"