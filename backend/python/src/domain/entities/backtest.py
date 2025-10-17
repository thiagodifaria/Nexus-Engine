"""
Entidade Backtest - DDD Domain Layer.

Implementei esta entidade para representar execuções de backtests.
Mantém referência à estratégia usada e resultados obtidos.
"""

from datetime import datetime
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Backtest(BaseModel):
    """
    Entidade Backtest representando uma execução de backtest.

    Implementei seguindo DDD com identidade única e agregação de resultados.
    Uso esta entidade para persistir histórico de backtests executados.
    """

    # Identity
    id: UUID = Field(default_factory=uuid4, description="ID único do backtest")

    # Relationships
    strategy_id: UUID = Field(..., description="ID da estratégia utilizada")

    # Backtest configuration
    symbols: List[str] = Field(..., min_length=1, description="Símbolos testados")
    start_date: datetime = Field(..., description="Data inicial do backtest")
    end_date: datetime = Field(..., description="Data final do backtest")

    # Execution metadata
    executed_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Quando o backtest foi executado"
    )
    execution_time_seconds: Optional[float] = Field(
        default=None,
        description="Tempo de execução em segundos"
    )

    # Results (populated after execution)
    initial_capital: float = Field(default=10000.0, gt=0, description="Capital inicial")
    final_capital: Optional[float] = Field(default=None, description="Capital final")

    # Performance metrics (stored as dict for flexibility)
    metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Métricas de performance (Sharpe, drawdown, etc)"
    )

    # Execution details
    total_trades: Optional[int] = Field(default=None, ge=0, description="Total de trades")
    winning_trades: Optional[int] = Field(default=None, ge=0, description="Trades vencedores")
    losing_trades: Optional[int] = Field(default=None, ge=0, description="Trades perdedores")

    # Status
    status: str = Field(
        default="pending",
        description="Status: pending, running, completed, failed"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Mensagem de erro se falhou"
    )

    class Config:
        """Configuração Pydantic."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "strategy_id": "123e4567-e89b-12d3-a456-426614174000",
                "symbols": ["AAPL", "GOOGL"],
                "start_date": "2023-01-01T00:00:00",
                "end_date": "2023-12-31T23:59:59",
                "initial_capital": 100000.0,
                "status": "completed"
            }
        }

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Valido que o status seja válido."""
        valid_statuses = ["pending", "running", "completed", "failed"]
        if v not in valid_statuses:
            raise ValueError(f"status must be one of {valid_statuses}")
        return v

    @field_validator("end_date")
    @classmethod
    def validate_date_range(cls, v: datetime, info) -> datetime:
        """
        Valido que end_date seja posterior a start_date.

        Implementei esta validação para evitar ranges inválidos.
        """
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v

    def mark_as_running(self) -> None:
        """Marco backtest como em execução."""
        self.status = "running"

    def mark_as_completed(
        self,
        final_capital: float,
        metrics: Dict[str, float],
        total_trades: int,
        winning_trades: int,
        losing_trades: int,
        execution_time: float
    ) -> None:
        """
        Marco backtest como completado e atualizo resultados.

        Implementei como método para garantir consistência ao finalizar backtest.

        Args:
            final_capital: Capital final após backtest
            metrics: Métricas de performance calculadas
            total_trades: Total de trades executados
            winning_trades: Trades vencedores
            losing_trades: Trades perdedores
            execution_time: Tempo de execução em segundos
        """
        self.status = "completed"
        self.final_capital = final_capital
        self.metrics = metrics
        self.total_trades = total_trades
        self.winning_trades = winning_trades
        self.losing_trades = losing_trades
        self.execution_time_seconds = execution_time
        self.error_message = None

    def mark_as_failed(self, error_message: str) -> None:
        """
        Marco backtest como falho.

        Args:
            error_message: Descrição do erro
        """
        self.status = "failed"
        self.error_message = error_message

    def get_return_percentage(self) -> Optional[float]:
        """
        Calculo retorno percentual do backtest.

        Returns:
            Retorno percentual ou None se não completado
        """
        if self.final_capital is None:
            return None
        return ((self.final_capital - self.initial_capital) / self.initial_capital) * 100

    def get_win_rate(self) -> Optional[float]:
        """
        Calculo taxa de acerto (win rate).

        Returns:
            Win rate percentual ou None se não há trades
        """
        if self.total_trades is None or self.total_trades == 0:
            return None
        if self.winning_trades is None:
            return None
        return (self.winning_trades / self.total_trades) * 100

    def __repr__(self) -> str:
        """Representação legível do backtest."""
        return (
            f"Backtest(id={self.id}, strategy_id={self.strategy_id}, "
            f"symbols={self.symbols}, status='{self.status}')"
        )