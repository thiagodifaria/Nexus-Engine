"""
Telemetry Service - Unified observability interface.

This module provides a unified service for all telemetry operations including
logging, metrics, and distributed tracing. It consolidates PrometheusMetrics,
LokiLogger, and TempoTracer into a single interface.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from contextlib import contextmanager

from infrastructure.observability.prometheus_metrics import PrometheusMetrics
from infrastructure.observability.loki_logger import LokiLogger
from infrastructure.observability.tempo_tracer import TempoTracer


class TelemetryService:
    """
    Unified telemetry service for observability.

    I provide a single interface for logging events, tracking metrics,
    and creating distributed traces across the Nexus platform.
    """

    def __init__(
        self,
        prometheus_metrics: PrometheusMetrics,
        loki_logger: LokiLogger,
        tempo_tracer: TempoTracer
    ):
        """
        Initialize the telemetry service.

        Args:
            prometheus_metrics: Prometheus metrics exporter instance
            loki_logger: Loki logger instance for structured logging
            tempo_tracer: Tempo tracer instance for distributed tracing
        """
        self._metrics = prometheus_metrics
        self._logger = loki_logger
        self._tracer = tempo_tracer
        self._internal_logger = logging.getLogger(__name__)

    def log_event(
        self,
        level: str,
        message: str,
        labels: Optional[Dict[str, str]] = None,
        extra_fields: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a structured event to Loki.

        I send structured log events to Loki with customizable labels
        and additional fields for rich context.

        Args:
            level: Log level (debug, info, warning, error, critical)
            message: Log message
            labels: Optional labels for log categorization
            extra_fields: Optional additional fields to include in log

        Example:
            >>> telemetry.log_event(
            ...     level="info",
            ...     message="Backtest completed successfully",
            ...     labels={"component": "backtest_engine", "strategy": "sma_cross"},
            ...     extra_fields={"duration_ms": 1234, "trades": 42}
            ... )
        """
        try:
            # Prepare log data
            log_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": level.upper(),
                "message": message
            }

            # Add extra fields if provided
            if extra_fields:
                log_data.update(extra_fields)

            # Send to Loki
            self._logger.log(
                level=level,
                message=message,
                labels=labels or {},
                extra_fields=extra_fields or {}
            )

        except Exception as e:
            self._internal_logger.error(f"Failed to log event: {e}")

    def track_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        metric_type: str = "gauge"
    ) -> None:
        """
        Track a metric value in Prometheus.

        I record metric values to Prometheus with support for different
        metric types (counter, gauge, histogram, summary).

        Args:
            metric_name: Name of the metric
            value: Metric value
            labels: Optional labels for metric categorization
            metric_type: Type of metric (counter, gauge, histogram, summary)

        Example:
            >>> telemetry.track_metric(
            ...     metric_name="backtest_duration_seconds",
            ...     value=1.234,
            ...     labels={"strategy": "sma_cross"},
            ...     metric_type="histogram"
            ... )
        """
        try:
            if metric_type == "counter":
                self._metrics.increment_counter(
                    name=metric_name,
                    value=value,
                    labels=labels or {}
                )
            elif metric_type == "gauge":
                self._metrics.set_gauge(
                    name=metric_name,
                    value=value,
                    labels=labels or {}
                )
            elif metric_type == "histogram":
                self._metrics.observe_histogram(
                    name=metric_name,
                    value=value,
                    labels=labels or {}
                )
            elif metric_type == "summary":
                self._metrics.observe_summary(
                    name=metric_name,
                    value=value,
                    labels=labels or {}
                )
            else:
                raise ValueError(f"Unknown metric type: {metric_type}")

        except Exception as e:
            self._internal_logger.error(f"Failed to track metric: {e}")

    @contextmanager
    def create_span(
        self,
        operation_name: str,
        tags: Optional[Dict[str, Any]] = None,
        parent_span_id: Optional[str] = None
    ):
        """
        Create a distributed tracing span.

        I create and manage distributed tracing spans for tracking
        request flows across services. Use as a context manager.

        Args:
            operation_name: Name of the operation being traced
            tags: Optional tags to attach to the span
            parent_span_id: Optional parent span ID for nested spans

        Yields:
            Span object that can be used to add tags/logs

        Example:
            >>> with telemetry.create_span(
            ...     operation_name="run_backtest",
            ...     tags={"strategy": "sma_cross", "symbol": "BTCUSDT"}
            ... ) as span:
            ...     # Do backtest work
            ...     span.set_tag("trades_count", 42)
            ...     span.log_event("backtest_completed")
        """
        span = None
        try:
            # Start the span
            span = self._tracer.start_span(
                operation_name=operation_name,
                parent_span_id=parent_span_id
            )

            # Add initial tags
            if tags:
                for key, value in tags.items():
                    span.set_tag(key, str(value))

            # Yield control to the calling code
            yield span

        except Exception as e:
            # Mark span as error if exception occurs
            if span:
                span.set_tag("error", True)
                span.set_tag("error.message", str(e))
                span.log_event("exception", {"exception": str(e)})

            self._internal_logger.error(f"Error in traced operation '{operation_name}': {e}")
            raise

        finally:
            # Always finish the span
            if span:
                span.finish()

    def log_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Log an error with full context.

        I log exceptions with stack traces and contextual information
        to both Loki and internal logger.

        Args:
            error: Exception to log
            context: Optional context information
            labels: Optional labels for categorization
        """
        error_data = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "stack_trace": self._get_stack_trace(error)
        }

        if context:
            error_data["context"] = context

        self.log_event(
            level="error",
            message=f"Error occurred: {str(error)}",
            labels=labels,
            extra_fields=error_data
        )

    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool,
        labels: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log performance metrics for an operation.

        I track operation performance by logging to Loki and recording
        metrics to Prometheus simultaneously.

        Args:
            operation: Name of the operation
            duration_ms: Duration in milliseconds
            success: Whether the operation succeeded
            labels: Optional labels
            metadata: Optional additional metadata
        """
        # Prepare labels
        perf_labels = labels or {}
        perf_labels["operation"] = operation
        perf_labels["success"] = str(success)

        # Track metric
        self.track_metric(
            metric_name="operation_duration_ms",
            value=duration_ms,
            labels=perf_labels,
            metric_type="histogram"
        )

        # Log event
        log_fields = {
            "duration_ms": duration_ms,
            "success": success
        }
        if metadata:
            log_fields.update(metadata)

        self.log_event(
            level="info" if success else "warning",
            message=f"Operation '{operation}' {'succeeded' if success else 'failed'} in {duration_ms:.2f}ms",
            labels=perf_labels,
            extra_fields=log_fields
        )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current metrics.

        Returns:
            Dictionary containing metrics summary
        """
        try:
            return self._metrics.get_metrics_summary()
        except Exception as e:
            self._internal_logger.error(f"Failed to get metrics summary: {e}")
            return {}

    def health_check(self) -> Dict[str, bool]:
        """
        Check health of all telemetry components.

        Returns:
            Dictionary with health status of each component
        """
        health = {
            "prometheus": False,
            "loki": False,
            "tempo": False
        }

        try:
            health["prometheus"] = self._metrics.is_healthy()
        except Exception:
            pass

        try:
            health["loki"] = self._logger.is_healthy()
        except Exception:
            pass

        try:
            health["tempo"] = self._tracer.is_healthy()
        except Exception:
            pass

        return health

    @staticmethod
    def _get_stack_trace(error: Exception) -> str:
        """Get formatted stack trace from exception."""
        import traceback
        return ''.join(traceback.format_exception(
            type(error), error, error.__traceback__
        ))