"""
FeedbackForge OpenTelemetry Instrumentation
==========================================

Configures OpenTelemetry with Azure Application Insights for:
- Distributed tracing
- Metrics
- Logging
- Automatic instrumentation for FastAPI, Redis, HTTP clients

Note: OpenTelemetry is optional. Install with: pip install -e ".[telemetry]"
"""

import logging
import os
from functools import wraps
from typing import Optional, Any

logger = logging.getLogger(__name__)

# Try to import Azure Monitor OpenTelemetry - it's optional
try:
    from opentelemetry import trace, metrics
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
    from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, SERVICE_INSTANCE_ID
    from azure.monitor.opentelemetry import configure_azure_monitor
    from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter, AzureMonitorMetricExporter

    OTEL_AVAILABLE = True
except ImportError as e:
    OTEL_AVAILABLE = False
    trace = None
    metrics = None
    logger.info("📊 Azure Monitor OpenTelemetry not installed. Telemetry disabled. Install with: pip install -e '.[telemetry]'")

# Global tracer and meter
tracer: Optional[Any] = None
meter: Optional[Any] = None


def setup_telemetry(service_name: str = "feedbackforge", service_version: str = "1.0.0") -> bool:
    """
    Setup OpenTelemetry with Azure Application Insights.

    Args:
        service_name: Name of the service
        service_version: Version of the service

    Returns:
        True if telemetry was configured, False if disabled or failed

    Environment Variables:
        APPLICATIONINSIGHTS_CONNECTION_STRING: Azure App Insights connection string
        OTEL_SERVICE_NAME: Override service name (optional)
        DISABLE_TELEMETRY: Set to "true" to disable telemetry
    """
    global tracer, meter

    # Check if Azure Monitor OpenTelemetry is available
    if not OTEL_AVAILABLE:
        logger.info("📊 Azure Monitor OpenTelemetry not available. Install with: pip install -e '.[telemetry]'")
        return False

    # Check if telemetry is disabled
    if os.environ.get("DISABLE_TELEMETRY", "").lower() == "true":
        logger.info("📊 Telemetry disabled via DISABLE_TELEMETRY environment variable")
        return False

    # Get Application Insights connection string
    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

    if not connection_string:
        logger.info("📊 Application Insights not configured. Set APPLICATIONINSIGHTS_CONNECTION_STRING to enable telemetry.")
        return False

    try:
        # Override service name if provided
        service_name = os.environ.get("OTEL_SERVICE_NAME", service_name)

        # Create resource with service information
        resource = Resource.create({
            SERVICE_NAME: service_name,
            SERVICE_VERSION: service_version,
            SERVICE_INSTANCE_ID: os.environ.get("HOSTNAME", "local"),
        })

        # ===== TRACING SETUP =====
        trace_exporter = AzureMonitorTraceExporter(connection_string=connection_string)
        trace_provider = TracerProvider(resource=resource)
        trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        trace.set_tracer_provider(trace_provider)

        # ===== METRICS SETUP =====
        metric_exporter = AzureMonitorMetricExporter(connection_string=connection_string)
        metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=60000)
        metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
        metrics.set_meter_provider(metric_provider)

        # Set global tracer and meter (must use global keyword above)
        globals()['tracer'] = trace.get_tracer(__name__)
        globals()['meter'] = metrics.get_meter(__name__)

        logger.info(f"✅ OpenTelemetry configured for Azure Application Insights")
        logger.info(f"   Service: {service_name} v{service_version}")
        logger.info(f"   Connection: {connection_string[:50]}...")

        return True

    except Exception as e:
        logger.error(f"⚠️ Failed to configure OpenTelemetry: {e}")
        logger.info("   Application will continue without telemetry.")
        return False


def setup_telemetry_extended(enable_live_metrics: bool = True):
    """
    Extended telemetry setup using azure-monitor-opentelemetry auto-configuration.

    This provides a simplified way to configure Azure Monitor with additional features
    like live metrics and automatic instrumentation for common libraries.

    Args:
        enable_live_metrics: Enable live metrics streaming. Defaults to True.

    Environment Variables:
        APPLICATIONINSIGHTS_CONNECTION_STRING: Required for Azure Monitor

    Example:
        setup_telemetry_extended(enable_live_metrics=True)
    """
    if not OTEL_AVAILABLE:
        logger.info("📊 Azure Monitor OpenTelemetry not available. Install with: pip install -e '.[telemetry]'")
        return

    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")

    if not connection_string:
        logger.warning("⚠️ APPLICATIONINSIGHTS_CONNECTION_STRING not set, skipping extended telemetry")
        return

    if os.environ.get("DISABLE_TELEMETRY", "").lower() == "true":
        logger.info("📊 Extended telemetry disabled via DISABLE_TELEMETRY environment variable")
        return

    try:
        # Configure Azure Monitor with OpenTelemetry
        # This auto-instruments common frameworks and libraries
        configure_azure_monitor(
            connection_string=connection_string,
            enable_live_metrics=enable_live_metrics,
        )
        logger.info("✅ Extended telemetry with Azure Monitor auto-instrumentation configured")
        if enable_live_metrics:
            logger.info("   Live metrics enabled")
            
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to configure extended telemetry: {e}")
    


def instrument_app(app):
    """
    Instrument FastAPI application with OpenTelemetry.

    This adds automatic instrumentation for:
    - FastAPI endpoints (requests, responses, errors)
    - Redis operations
    - HTTP client calls

    Args:
        app: FastAPI application instance
    """
    if not OTEL_AVAILABLE:
        return

    connection_string = os.environ.get("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string or os.environ.get("DISABLE_TELEMETRY", "").lower() == "true":
        return

    try:
        # Auto-instrument FastAPI
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor.instrument_app(app)
        logger.info("✅ FastAPI auto-instrumentation enabled")

        # Auto-instrument Redis (if used)
        try:
            from opentelemetry.instrumentation.redis import RedisInstrumentor
            RedisInstrumentor().instrument()
            logger.info("✅ Redis auto-instrumentation enabled")
        except Exception as e:
            logger.debug(f"Redis instrumentation not available: {e}")

        # Auto-instrument HTTP clients
        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            HTTPXClientInstrumentor().instrument()
            logger.info("✅ HTTPX client auto-instrumentation enabled")
        except Exception as e:
            logger.debug(f"HTTPX instrumentation not available: {e}")

    except Exception as e:
        logger.warning(f"⚠️ Failed to instrument app: {e}")


# Custom metrics (examples)
def create_custom_metrics():
    """Create custom metrics for FeedbackForge."""
    if not OTEL_AVAILABLE or not meter:
        return {}

    return {
        "feedback_processed": meter.create_counter(
            name="feedbackforge.feedback.processed",
            description="Number of feedback items processed",
            unit="1",
        ),
        "sessions_created": meter.create_counter(
            name="feedbackforge.sessions.created",
            description="Number of sessions created",
            unit="1",
        ),
        "agent_executions": meter.create_counter(
            name="feedbackforge.agent.executions",
            description="Number of agent workflow executions",
            unit="1",
        ),
        "agent_duration": meter.create_histogram(
            name="feedbackforge.agent.duration",
            description="Duration of agent workflow executions",
            unit="ms",
        ),
    }


# Helper function for custom spans
def trace_operation(operation_name: str):
    """
    Decorator to trace a function with a custom span.

    Usage:
        @trace_operation("my_operation")
        def my_function():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # If OpenTelemetry not available or tracer not configured, just run the function
            if not OTEL_AVAILABLE or not tracer:
                return func(*args, **kwargs)

            # Create span with tracer
            with tracer.start_as_current_span(operation_name) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_attribute("success", True)
                    return result
                except Exception as e:
                    span.set_attribute("success", False)
                    span.set_attribute("error.type", type(e).__name__)
                    span.set_attribute("error.message", str(e))
                    span.record_exception(e)
                    raise
        return wrapper
    return decorator
