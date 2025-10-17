"""
Entidade Position - DDD Domain Layer.

Implementei para representar posições abertas em trading.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Position(BaseModel):
    """
    Entidade Position representando uma posição aberta.

    Implementei seguindo DDD para tracking de posições em real-time ou backtest.
    Mantenho informações de entrada, preço atual e P&L calculado.
    """

    # Identity
    id: UUID = Field(default_factory=uuid4, description="ID único da posição")

    # Position details
    symbol: str = Field(..., min_length=1, description="Símbolo do ativo")
    quantity: float = Field(..., description="Quantidade (positivo=long, negativo=short)")
    entry_price: float = Field(..., gt=0, description="Preço de entrada")
    current_price: float = Field(..., gt=0, description="Preço atual")

    # Timestamps
    opened_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Quando a posição foi aberta"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Última atualização de preço"
    )
    closed_at: Optional[datetime] = Field(
        default=None,
        description="Quando a posição foi fechada"
    )

    # Status
    is_open: bool = Field(default=True, description="Se a posição está aberta")

    # Optional metadata
    backtest_id: Optional[UUID] = Field(
        default=None,
        description="ID do backtest (se aplicável)"
    )
    strategy_id: Optional[UUID] = Field(
        default=None,
        description="ID da estratégia que abriu a posição"
    )

    class Config:
        """Configuração Pydantic."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "quantity": 100.0,
                "entry_price": 150.50,
                "current_price": 152.75,
                "is_open": True
            }
        }

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        """Valido que quantity não seja zero."""
        if v == 0:
            raise ValueError("quantity cannot be zero")
        return v

    def update_price(self, new_price: float) -> None:
        """
        Atualizo preço atual da posição.

        Implementei como método para encapsular lógica e manter timestamp atualizado.

        Args:
            new_price: Novo preço de mercado
        """
        if new_price <= 0:
            raise ValueError("price must be positive")
        self.current_price = new_price
        self.updated_at = datetime.utcnow()

    def calculate_pnl(self) -> float:
        """
        Calculo P&L (Profit and Loss) da posição.

        Implementei cálculo direto:
        - Long position: (current - entry) * quantity
        - Short position: (entry - current) * |quantity|

        Returns:
            P&L em valor absoluto (não percentual)
        """
        price_diff = self.current_price - self.entry_price
        return price_diff * self.quantity

    def calculate_pnl_percentage(self) -> float:
        """
        Calculo P&L percentual.

        Returns:
            P&L em percentual relativo ao preço de entrada
        """
        price_diff = self.current_price - self.entry_price
        return (price_diff / self.entry_price) * 100

    def is_long(self) -> bool:
        """Verifico se é posição long."""
        return self.quantity > 0

    def is_short(self) -> bool:
        """Verifico se é posição short."""
        return self.quantity < 0

    def close(self, closing_price: float) -> float:
        """
        Fecho a posição.

        Implementei como método para garantir state consistency ao fechar.

        Args:
            closing_price: Preço de fechamento

        Returns:
            P&L final realizado
        """
        if not self.is_open:
            raise ValueError("Position is already closed")

        self.current_price = closing_price
        self.closed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.is_open = False

        return self.calculate_pnl()

    def __repr__(self) -> str:
        """Representação legível da posição."""
        direction = "LONG" if self.is_long() else "SHORT"
        status = "OPEN" if self.is_open else "CLOSED"
        pnl = self.calculate_pnl()
        return (
            f"Position({direction} {abs(self.quantity)} {self.symbol} @ {self.entry_price}, "
            f"current={self.current_price}, P&L={pnl:.2f}, {status})"
        )