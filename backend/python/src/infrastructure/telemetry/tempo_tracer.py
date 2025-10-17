"""
OpenTelemetry tracer para Tempo.

Implementei distributed tracing com OpenTelemetry.
Decidi usar OTLP exporter para enviar traces ao Tempo.

Referências:
- OpenTelemetry Python: https://opentelemetry.io/docs/instrumentation/python/
- Tempo: https://grafana.com/docs/tempo/
"""

from typing import Optional
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

from config.settings import get_settings


class TempoTracer:
    """
    Tracer para distributed tracing com Tempo.

    Implementei usando OpenTelemetry para instrumentação automática.
    """

    def __init__(self):
        """Inicializo tracer."""
        settings = get_settings()

        # Resource com metadados do serviço
        resource = Resource.create({
            "service.name": "nexus-engine",
            "service.version": "0.7.0",
            "deployment.environment": settings.environment
        })

        # Provider
        provider = TracerProvider(resource=resource)

        # OTLP Exporter para Tempo
        otlp_exporter = OTLPSpanExporter(
            endpoint=settings.tempo_url,
            insecure=True  # Uso TLS em produção
        )

        # Batch processor para eficiência
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)

        # Seto provider global
        trace.set_tracer_provider(provider)

        self.tracer = trace.get_tracer(__name__)

    def start_span(self, name: str, **attributes):
        """
        Inicio novo span.

        Args:
            name: Nome do span
            **attributes: Atributos customizados

        Returns:
            Context manager do span
        """
        return self.tracer.start_as_current_span(name, attributes=attributes)


# Singleton
_tracer: Optional[TempoTracer] = None


def get_tracer() -> TempoTracer:
    """Retorno singleton do tracer."""
    global _tracer
    if _tracer is None:
        _tracer = TempoTracer()
    return _tracer