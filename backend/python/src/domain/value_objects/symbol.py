"""
Value Object Symbol - DDD Domain Layer.

Implementei para representar símbolos de ativos de forma type-safe.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class Symbol(BaseModel):
    """
    Value Object representando um símbolo de ativo.

    Implementei como Value Object para encapsular validações e normalizações.
    Decidi usar uppercase sempre para consistência.

    Exemplos: AAPL, GOOGL, BTC-USD, ES=F (futures)
    """

    value: str = Field(..., min_length=1, max_length=20, description="Símbolo do ativo")
    exchange: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Exchange (opcional): NASDAQ, NYSE, etc"
    )

    class Config:
        """Configuração Pydantic para imutabilidade."""
        frozen = True
        json_schema_extra = {
            "example": {
                "value": "AAPL",
                "exchange": "NASDAQ"
            }
        }

    @field_validator("value")
    @classmethod
    def validate_and_normalize(cls, v: str) -> str:
        """
        Valido e normalizo símbolo.

        Implementei normalização automática para uppercase para evitar
        inconsistências (AAPL vs aapl vs AaPl).
        """
        v = v.strip().upper()
        if not v:
            raise ValueError("symbol cannot be empty or whitespace")

        # Valido caracteres permitidos (letras, números, alguns símbolos)
        allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._=")
        if not all(c in allowed_chars for c in v):
            raise ValueError(
                f"symbol contains invalid characters. Allowed: letters, numbers, - _ . ="
            )

        return v

    @field_validator("exchange")
    @classmethod
    def validate_exchange(cls, v: Optional[str]) -> Optional[str]:
        """Normalizo exchange para uppercase."""
        if v is None:
            return None
        return v.strip().upper()

    def is_crypto(self) -> bool:
        """
        Verifico se é criptomoeda (heurística simples).

        Returns:
            True se parece ser crypto
        """
        crypto_indicators = ["-USD", "-USDT", "-BTC", "-ETH"]
        return any(self.value.endswith(indicator) for indicator in crypto_indicators)

    def is_futures(self) -> bool:
        """
        Verifico se é contrato futuro (heurística).

        Returns:
            True se parece ser futures
        """
        return self.value.endswith("=F") or self.value.endswith("=")

    def get_base_symbol(self) -> str:
        """
        Retorno símbolo base sem sufixos.

        Exemplos:
        - BTC-USD -> BTC
        - ES=F -> ES

        Returns:
            Símbolo base
        """
        # Remove sufixos comuns
        base = self.value
        for suffix in ["-USD", "-USDT", "-BTC", "-ETH", "=F", "="]:
            if base.endswith(suffix):
                base = base[:-len(suffix)]
                break
        return base

    def __str__(self) -> str:
        """String representation."""
        if self.exchange:
            return f"{self.value}:{self.exchange}"
        return self.value

    def __repr__(self) -> str:
        """Representação técnica."""
        if self.exchange:
            return f"Symbol('{self.value}', exchange='{self.exchange}')"
        return f"Symbol('{self.value}')"

    def __hash__(self) -> int:
        """
        Hash para uso em sets e dicts.

        Implementei considerando value e exchange para unicidade.
        """
        return hash((self.value, self.exchange))