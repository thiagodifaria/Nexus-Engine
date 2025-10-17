"""
Entidade Strategy - DDD Domain Layer.

Implementei esta entidade seguindo princípios de Domain-Driven Design.
Decidi usar Pydantic para validação automática e type safety.

Referências:
- Domain-Driven Design: https://www.domainlanguage.com/ddd/
- Pydantic Documentation: https://docs.pydantic.dev/
"""

from datetime import datetime
from typing import Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class Strategy(BaseModel):
    """
    Entidade Strategy para persistência de estratégias de trading.

    Implementei esta classe como uma entidade DDD com identidade única (ID).
    Uso Pydantic para garantir validação automática e serialização.

    A entidade mantém referência aos parâmetros e permite conversão para/do C++ engine.
    """

    # Identity
    id: UUID = Field(default_factory=uuid4, description="ID único da estratégia")

    # Core attributes
    name: str = Field(..., min_length=1, max_length=255, description="Nome da estratégia")
    strategy_type: str = Field(
        ...,
        description="Tipo de estratégia (SMA, MACD, RSI, custom)"
    )

    # Parameters
    parameters: Dict[str, float] = Field(
        default_factory=dict,
        description="Parâmetros numéricos da estratégia"
    )

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data de criação"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Data de última atualização"
    )

    # Optional fields
    description: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Descrição da estratégia"
    )
    is_active: bool = Field(
        default=True,
        description="Se a estratégia está ativa"
    )

    class Config:
        """Configuração Pydantic."""
        from_attributes = True
        json_schema_extra = {
            "example": {
                "name": "SMA Crossover 10/20",
                "strategy_type": "SMA",
                "parameters": {
                    "short_window": 10.0,
                    "long_window": 20.0
                },
                "description": "Simple Moving Average crossover strategy"
            }
        }

    @field_validator("strategy_type")
    @classmethod
    def validate_strategy_type(cls, v: str) -> str:
        """
        Valido que o tipo de estratégia seja conhecido.

        Implementei esta validação para evitar tipos inválidos no sistema.
        """
        valid_types = ["SMA", "MACD", "RSI", "custom"]
        if v not in valid_types:
            raise ValueError(f"strategy_type must be one of {valid_types}, got: {v}")
        return v

    @field_validator("parameters")
    @classmethod
    def validate_parameters(cls, v: Dict[str, float]) -> Dict[str, float]:
        """
        Valido que os parâmetros sejam válidos (não negativos onde aplicável).

        Decidi validar aqui para garantir que parâmetros ruins não cheguem ao C++ engine.
        """
        for key, value in v.items():
            if not isinstance(value, (int, float)):
                raise ValueError(f"Parameter {key} must be numeric, got {type(value)}")
            # Períodos de janela devem ser positivos
            if "window" in key.lower() or "period" in key.lower():
                if value <= 0:
                    raise ValueError(f"Parameter {key} must be positive, got {value}")
        return v

    def to_cpp_params(self) -> Dict[str, float]:
        """
        Converto parâmetros para formato do C++ engine.

        Implementei este método para facilitar a ponte Python <-> C++.
        Por enquanto é identity function, mas permite transformações futuras.

        Returns:
            Dicionário de parâmetros compatível com C++ engine
        """
        return self.parameters.copy()

    @classmethod
    def from_cpp_strategy(
        cls,
        name: str,
        strategy_type: str,
        cpp_parameters: Dict[str, float],
        description: Optional[str] = None
    ) -> "Strategy":
        """
        Crio Strategy entity a partir de estratégia C++.

        Uso este factory method para criar entities a partir do C++ engine.

        Args:
            name: Nome da estratégia
            strategy_type: Tipo (SMA, MACD, RSI)
            cpp_parameters: Parâmetros do C++
            description: Descrição opcional

        Returns:
            Nova instância de Strategy
        """
        return cls(
            name=name,
            strategy_type=strategy_type,
            parameters=cpp_parameters,
            description=description
        )

    def update_parameters(self, new_parameters: Dict[str, float]) -> None:
        """
        Atualizo parâmetros da estratégia.

        Implementei como método para manter encapsulamento e permitir
        validação e side effects (como atualizar timestamp).

        Args:
            new_parameters: Novos parâmetros a serem aplicados
        """
        # Validação acontece automaticamente via Pydantic
        self.parameters = new_parameters
        self.updated_at = datetime.utcnow()

    def deactivate(self) -> None:
        """
        Desativo a estratégia.

        Uso soft delete para manter histórico.
        """
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Reativo a estratégia."""
        self.is_active = True
        self.updated_at = datetime.utcnow()

    def __repr__(self) -> str:
        """Representação legível da estratégia."""
        return (
            f"Strategy(id={self.id}, name='{self.name}', "
            f"type='{self.strategy_type}', active={self.is_active})"
        )