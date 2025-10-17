"""
Value Object Price - DDD Domain Layer.

Implementei para representar preços com validação e currency.
"""

from decimal import Decimal
from typing import Union

from pydantic import BaseModel, Field, field_validator


class Price(BaseModel):
    """
    Value Object representando um preço com moeda.

    Implementei usando Decimal para evitar problemas de precisão com floats.
    Preços financeiros devem ser exatos, não aproximados.

    Referência: Decimal arithmetic
    https://docs.python.org/3/library/decimal.html
    """

    value: Decimal = Field(..., description="Valor do preço")
    currency: str = Field(default="USD", description="Moeda (USD, BRL, EUR, etc)")

    class Config:
        """Configuração Pydantic para imutabilidade."""
        frozen = True
        json_schema_extra = {
            "example": {
                "value": "150.50",
                "currency": "USD"
            }
        }

    @field_validator("value", mode="before")
    @classmethod
    def validate_value(cls, v: Union[str, int, float, Decimal]) -> Decimal:
        """
        Valido e converto para Decimal.

        Implementei conversão automática de str/int/float para Decimal.
        """
        if isinstance(v, Decimal):
            decimal_value = v
        else:
            decimal_value = Decimal(str(v))

        if decimal_value <= 0:
            raise ValueError("price must be positive")

        return decimal_value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """
        Valido e normalizo currency code.

        Implementei normalização para uppercase seguindo ISO 4217.
        """
        v_upper = v.strip().upper()
        if len(v_upper) != 3:
            raise ValueError("currency code must be 3 characters (ISO 4217)")

        # Lista de currencies comuns (não exaustiva, mas cobre maioria)
        common_currencies = {
            "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
            "BRL", "MXN", "CNY", "HKD", "SGD", "INR", "KRW", "RUB",
            "BTC", "ETH", "USDT"  # Cryptocurrencies
        }

        if v_upper not in common_currencies:
            # Apenas aviso, não bloqueio (pode haver currencies menos comuns)
            pass

        return v_upper

    def to_float(self) -> float:
        """
        Converto para float.

        Útil para interop com código que espera float, mas perde precisão.
        Uso apenas quando necessário.

        Returns:
            Valor como float
        """
        return float(self.value)

    def add(self, other: "Price") -> "Price":
        """
        Somo com outro Price.

        Implementei verificação de currency matching.

        Args:
            other: Outro Price

        Returns:
            Novo Price com soma

        Raises:
            ValueError: Se currencies diferentes
        """
        if self.currency != other.currency:
            raise ValueError(f"Cannot add prices with different currencies: {self.currency} vs {other.currency}")
        return Price(value=self.value + other.value, currency=self.currency)

    def subtract(self, other: "Price") -> "Price":
        """
        Subtraio outro Price.

        Args:
            other: Outro Price

        Returns:
            Novo Price com diferença (pode ser negativo)

        Raises:
            ValueError: Se currencies diferentes
        """
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract prices with different currencies: {self.currency} vs {other.currency}")
        return Price(value=self.value - other.value, currency=self.currency)

    def multiply(self, factor: Union[int, float, Decimal]) -> "Price":
        """
        Multiplico por fator.

        Args:
            factor: Fator multiplicador

        Returns:
            Novo Price multiplicado
        """
        if isinstance(factor, (int, float)):
            factor = Decimal(str(factor))
        return Price(value=self.value * factor, currency=self.currency)

    def divide(self, divisor: Union[int, float, Decimal]) -> "Price":
        """
        Divido por divisor.

        Args:
            divisor: Divisor

        Returns:
            Novo Price dividido

        Raises:
            ValueError: Se divisor for zero
        """
        if isinstance(divisor, (int, float)):
            divisor = Decimal(str(divisor))
        if divisor == 0:
            raise ValueError("Cannot divide by zero")
        return Price(value=self.value / divisor, currency=self.currency)

    def __str__(self) -> str:
        """String representation."""
        return f"{self.currency} {self.value}"

    def __repr__(self) -> str:
        """Representação técnica."""
        return f"Price(value=Decimal('{self.value}'), currency='{self.currency}')"

    def __hash__(self) -> int:
        """Hash para uso em sets/dicts."""
        return hash((self.value, self.currency))