"""
Entidade Trade - DDD Domain Layer.

Implementei para representar trades executados.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Trade(BaseModel):
    """
    Entidade Trade representando um trade executado.

    Implementei seguindo DDD para manter histórico completo de trades.
    Cada trade é imutável após criação (event sourcing style).
    """

    # Identity
    id: UUID = Field(default_factory=uuid4, description="ID único do trade")

    # Relationships
    backtest_id: Optional[UUID] = Field(
        default=None,
        description="ID do backtest (se aplicável)"
    )
    position_id: Optional[UUID] = Field(
        default=None,
        description="ID da posição relacionada"
    )
    strategy_id: Optional[UUID] = Field(
        default=None,
        description="ID da estratégia que gerou o trade"
    )

    # Trade details
    symbol: str = Field(..., min_length=1, description="Símbolo do ativo")
    side: str = Field(..., description="Lado: BUY ou SELL")
    quantity: float = Field(..., gt=0, description="Quantidade executada")
    price: float = Field(..., gt=0, description="Preço de execução")
    commission: float = Field(default=0.0, ge=0, description="Comissão paga")

    # Timestamps
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp da execução"
    )

    # Optional metadata
    signal_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confiança do sinal que gerou o trade"
    )
    slippage: Optional[float] = Field(
        default=None,
        description="Slippage aplicado (diferença do preço esperado)"
    )

    class Config:
        """Configuração Pydantic."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "symbol": "AAPL",
                "side": "BUY",
                "quantity": 100.0,
                "price": 150.50,
                "commission": 1.0,
                "signal_confidence": 0.85
            }
        }

    @field_validator("side")
    @classmethod
    def validate_side(cls, v: str) -> str:
        """
        Valido que side seja BUY ou SELL.

        Implementei validação estrita para evitar valores inválidos.
        """
        v_upper = v.upper()
        if v_upper not in ["BUY", "SELL"]:
            raise ValueError("side must be 'BUY' or 'SELL'")
        return v_upper

    def calculate_total_cost(self) -> float:
        """
        Calculo custo total do trade (preço * quantidade + comissão).

        Returns:
            Custo total
        """
        base_cost = self.price * self.quantity
        return base_cost + self.commission

    def calculate_net_value(self) -> float:
        """
        Calculo valor líquido do trade.

        Para BUY: negativo (saída de caixa)
        Para SELL: positivo (entrada de caixa)

        Returns:
            Valor líquido (positivo ou negativo)
        """
        total = self.calculate_total_cost()
        if self.side == "BUY":
            return -total
        else:  # SELL
            return total - self.commission  # Receita menos comissão

    def is_buy(self) -> bool:
        """Verifico se é ordem de compra."""
        return self.side == "BUY"

    def is_sell(self) -> bool:
        """Verifico se é ordem de venda."""
        return self.side == "SELL"

    def get_effective_price(self) -> float:
        """
        Calculo preço efetivo incluindo comissão.

        Implementei para obter custo real por ação incluindo fees.

        Returns:
            Preço efetivo por unidade
        """
        commission_per_share = self.commission / self.quantity
        if self.is_buy():
            return self.price + commission_per_share
        else:
            return self.price - commission_per_share

    def __repr__(self) -> str:
        """Representação legível do trade."""
        return (
            f"Trade({self.side} {self.quantity} {self.symbol} @ {self.price}, "
            f"commission={self.commission:.2f}, "
            f"total={self.calculate_total_cost():.2f})"
        )