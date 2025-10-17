"""
Structured logging para Loki.

Implementei logger estruturado com JSON para facilitar queries no Loki.
Decidi adicionar trace_id para correlação com Tempo.

Referências:
- Python JSON Logger: https://github.com/madzak/python-json-logger
- Loki: https://grafana.com/docs/loki/
"""

import logging
import sys
from typing import Optional
from pythonjsonlogger import jsonlogger

from config.settings import get_settings


class LokiLogger:
    """
    Logger estruturado para Loki.

    Implementei formatação JSON com campos customizados.
    Uso trace_id para correlação com distributed tracing.
    """

    def __init__(self, name: str = "nexus"):
        """
        Inicializo logger.

        Args:
            name: Nome do logger
        """
        self.logger = logging.getLogger(name)
        settings = get_settings()

        # Configuro nível baseado em settings
        level = getattr(logging, settings.log_level.upper())
        self.logger.setLevel(level)

        # Handler para stdout (será capturado por Loki)
        handler = logging.StreamHandler(sys.stdout)

        # Formato JSON com campos customizados
        formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(trace_id)s %(user_id)s'
        )
        handler.setFormatter(formatter)

        self.logger.addHandler(handler)

    def debug(self, message: str, **kwargs) -> None:
        """Log debug com contexto adicional."""
        self.logger.debug(message, extra=kwargs)

    def info(self, message: str, **kwargs) -> None:
        """Log info com contexto adicional."""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning com contexto adicional."""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error com contexto adicional."""
        self.logger.error(message, extra=kwargs)

    def critical(self, message: str, **kwargs) -> None:
        """Log critical com contexto adicional."""
        self.logger.critical(message, extra=kwargs)


# Singleton
_logger: Optional[LokiLogger] = None


def get_logger() -> LokiLogger:
    """Retorno singleton do logger."""
    global _logger
    if _logger is None:
        _logger = LokiLogger()
    return _logger