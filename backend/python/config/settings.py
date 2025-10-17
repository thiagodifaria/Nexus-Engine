"""
Settings gerais do sistema usando Pydantic Settings.

Implementei esta configuração centralizada para facilitar o gerenciamento
de variáveis de ambiente e validação automática com Pydantic.
"""

from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configurações centralizadas do Nexus Engine.

    Uso Pydantic Settings para validação automática e carregamento
    de variáveis de ambiente. Decidi separar as configs por categoria
    para melhor organização.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # Database
    database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/nexus",
        description="PostgreSQL connection URL"
    )

    # Market Data APIs
    finnhub_api_key: Optional[str] = Field(
        default=None,
        description="Finnhub API key for real-time data"
    )
    alpha_vantage_api_key: Optional[str] = Field(
        default=None,
        description="Alpha Vantage API key for historical data"
    )
    nasdaq_data_link_api_key: Optional[str] = Field(
        default=None,
        description="Nasdaq Data Link API key"
    )
    fred_api_key: Optional[str] = Field(
        default=None,
        description="FRED API key for macroeconomic data"
    )

    # Observability
    prometheus_port: int = Field(
        default=9090,
        description="Prometheus metrics export port"
    )
    loki_url: str = Field(
        default="http://localhost:3100",
        description="Loki logs aggregation URL"
    )
    tempo_url: str = Field(
        default="http://localhost:4317",
        description="Tempo tracing URL (OTLP endpoint)"
    )

    # Application
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    )
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Valido que o log level seja um valor válido."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v_upper

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Valido que o environment seja um valor válido."""
        valid_envs = ["development", "staging", "production"]
        v_lower = v.lower()
        if v_lower not in valid_envs:
            raise ValueError(f"environment must be one of {valid_envs}")
        return v_lower

    @field_validator("prometheus_port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Valido que a porta esteja no range válido."""
        if not (1024 <= v <= 65535):
            raise ValueError("prometheus_port must be between 1024 and 65535")
        return v

    def is_production(self) -> bool:
        """Verifico se estamos em produção."""
        return self.environment == "production"

    def has_market_data_access(self) -> bool:
        """
        Verifico se temos acesso a pelo menos uma API de market data.

        Implementei este método para facilitar validações em runtime
        e evitar iniciar o sistema sem dados de mercado disponíveis.
        """
        return any([
            self.finnhub_api_key,
            self.alpha_vantage_api_key,
            self.nasdaq_data_link_api_key,
        ])


# Singleton para acesso global às configurações
# Decidi usar este pattern para evitar recarregar o .env múltiplas vezes
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Retorno a instância singleton de Settings.

    Implementei como singleton para garantir que as configs sejam
    carregadas apenas uma vez durante a execução da aplicação.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Exporto para fácil importação
settings = get_settings()