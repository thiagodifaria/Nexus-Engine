"""
Value Object TimeRange - DDD Domain Layer.

Implementei como Value Object imutável seguindo DDD.
Decidi usar frozen=True do Pydantic para garantir imutabilidade.

Referências:
- Value Objects in DDD: https://www.domainlanguage.com/ddd/
"""

from datetime import datetime, timedelta
from typing import Iterator

from pydantic import BaseModel, Field, field_validator


class TimeRange(BaseModel):
    """
    Value Object representando um range de tempo imutável.

    Implementei como Value Object pois não tem identidade - dois ranges
    com mesmas datas são indistinguíveis e intercambiáveis.

    A imutabilidade garante que ranges compartilhados não sejam modificados
    acidentalmente, seguindo princípios de programação funcional.
    """

    start_date: datetime = Field(..., description="Data inicial do range")
    end_date: datetime = Field(..., description="Data final do range")

    class Config:
        """Configuração Pydantic para imutabilidade."""
        frozen = True  # Torna o objeto imutável
        json_schema_extra = {
            "example": {
                "start_date": "2023-01-01T00:00:00",
                "end_date": "2023-12-31T23:59:59"
            }
        }

    @field_validator("end_date")
    @classmethod
    def validate_end_after_start(cls, v: datetime, info) -> datetime:
        """
        Valido que end_date seja posterior a start_date.

        Implementei esta invariante do Value Object para garantir ranges válidos.
        Um range inválido não deveria sequer existir no sistema.
        """
        if "start_date" in info.data and v <= info.data["start_date"]:
            raise ValueError("end_date must be after start_date")
        return v

    def duration_days(self) -> int:
        """
        Calculo duração em dias.

        Returns:
            Número de dias entre start e end
        """
        delta = self.end_date - self.start_date
        return delta.days

    def duration_seconds(self) -> float:
        """
        Calculo duração em segundos.

        Returns:
            Número de segundos entre start e end
        """
        delta = self.end_date - self.start_date
        return delta.total_seconds()

    def contains(self, dt: datetime) -> bool:
        """
        Verifico se uma data está dentro do range.

        Args:
            dt: Data a verificar

        Returns:
            True se dt está entre start_date e end_date (inclusive)
        """
        return self.start_date <= dt <= self.end_date

    def overlaps(self, other: "TimeRange") -> bool:
        """
        Verifico se este range sobrepõe outro range.

        Implementei usando lógica de Allen's interval algebra.

        Args:
            other: Outro TimeRange

        Returns:
            True se há sobreposição
        """
        return not (self.end_date < other.start_date or self.start_date > other.end_date)

    def split_by_days(self, days: int = 1) -> Iterator["TimeRange"]:
        """
        Divido range em sub-ranges de N dias.

        Útil para processar backtests longos em chunks menores.

        Args:
            days: Número de dias por chunk

        Yields:
            TimeRange de até N dias
        """
        current = self.start_date
        delta = timedelta(days=days)

        while current < self.end_date:
            chunk_end = min(current + delta, self.end_date)
            yield TimeRange(start_date=current, end_date=chunk_end)
            current = chunk_end

    def __str__(self) -> str:
        """String representation legível."""
        return f"{self.start_date.date()} to {self.end_date.date()} ({self.duration_days()} days)"

    def __repr__(self) -> str:
        """Representação técnica."""
        return f"TimeRange(start={self.start_date}, end={self.end_date})"