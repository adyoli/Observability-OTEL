"""
OpenTelemetry Observability Configuration for Document API Service

This module provides comprehensive observability setup for the Document API service using
OpenTelemetry (OTEL). It configures distributed tracing, metrics collection, and
automatic instrumentation to provide deep visibility into service performance and behavior.

Key Components:
- TracerProvider: Manages trace generation and sampling
- MeterProvider: Handles metrics collection and aggregation
- BatchSpanProcessor: Efficiently batches and exports trace data
- PeriodicExportingMetricReader: Exports metrics at regular intervals
- Resource: Adds service metadata to all telemetry data
- Automatic Instrumentation: Instruments FastAPI and HTTPX for zero-code observability

Configuration:
- OTLP gRPC export to otel-collector:4317
- Batch processing for performance optimization
- Service attribution with name, version, and environment
- Correlation ID context management for request tracing

Usage:
    from telemetry import init_observability, get_correlation_id
    
    # Initialize at startup
    init_observability()
    
    # Use correlation ID in request handling
    correlation_id = get_correlation_id()
"""

import os
import uuid
from contextvars import ContextVar
from opentelemetry import trace
from opentelemetry import metrics

# Core OpenTelemetry SDK components for tracing
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,  # Batches spans for efficient export
)
# Core OpenTelemetry SDK components for metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import (
    PeriodicExportingMetricReader  # Exports metrics at regular intervals
)
# OTLP exporters for sending data to the collector
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

# Resource management for service attribution
from opentelemetry.sdk.resources import Resource
# Automatic instrumentation for popular frameworks
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

# Context variable for correlation ID management across async operations
# This allows us to track request flow through the entire system
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

def get_correlation_id() -> str:
    """
    Get the current correlation ID from the context.
    
    The correlation ID is a unique identifier that flows through all services
    involved in processing a single request. This enables distributed tracing
    and request correlation across the entire system.
    
    Returns:
        str: The current correlation ID, or empty string if not set
        
    Example:
        >>> correlation_id = get_correlation_id()
        >>> print(f"Processing request: {correlation_id}")
    """
    return correlation_id.get()

def set_correlation_id(corr_id: str) -> None:
    """
    Set the current correlation ID in the context.
    
    This function sets the correlation ID for the current async context.
    All subsequent operations in the same request will have access to this ID
    through get_correlation_id().
    
    Args:
        corr_id (str): The correlation ID to set
        
    Example:
        >>> set_correlation_id("req-123-abc")
        >>> # Now all operations can access this ID
    """
    correlation_id.set(corr_id)

def generate_correlation_id() -> str:
    """
    Generate a new unique correlation ID.
    
    Creates a UUID4-based correlation ID that is guaranteed to be unique
    across the entire system. This is used to track individual requests
    from start to finish.
    
    Returns:
        str: A new unique correlation ID
        
    Example:
        >>> new_id = generate_correlation_id()
        >>> # Result: "550e8400-e29b-41d4-a716-446655440000"
    """
    return str(uuid.uuid4())

def init_observability():
    """
    Initialize OpenTelemetry observability for the Document API service.
    
    This function sets up the complete observability infrastructure:
    1. Creates and configures the TracerProvider for distributed tracing
    2. Sets up the MeterProvider for metrics collection
    3. Configures OTLP exporters to send data to the collector
    4. Sets up batch processing for performance optimization
    5. Adds service metadata to all telemetry data
    6. Enables automatic instrumentation for FastAPI and HTTPX
    
    Configuration Details:
    - Tracing: Uses BatchSpanProcessor for efficient span export
    - Metrics: Uses PeriodicExportingMetricReader with 5-second intervals
    - Export: Sends data to otel-collector:4317 via gRPC
    - Resource: Adds service name, version, and environment metadata
    
    Environment Variables:
    - OTEL_EXPORTER_OTLP_ENDPOINT: Collector endpoint (default: otel-collector:4317)
    - ENVIRONMENT: Deployment environment (default: development)
    
    Note: This function should be called once at service startup, before
    any requests are processed.
    
    Example:
        >>> init_observability()
        >>> # Now all FastAPI requests and HTTPX calls are automatically instrumented
    """
    
    # Create resource with service information for attribution
    # This metadata is attached to ALL telemetry data (traces, metrics, logs)
    # making it easy to identify which service generated what data
    resource = Resource.create({
        "service.name": "document-api",           # Service identifier
        "service.version": "1.0.0",               # Version for tracking deployments
        "deployment.environment": os.getenv("ENVIRONMENT", "development")  # Environment context
    })

    # Initialize distributed tracing infrastructure
    # TracerProvider is the main entry point for trace generation
    trace_provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter for sending traces to the collector
    # The collector acts as a central hub for all observability data
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    )
    
    # BatchSpanProcessor batches spans before sending to improve performance
    # This reduces network overhead and collector load
    processor = BatchSpanProcessor(otlp_exporter)
    trace_provider.add_span_processor(processor)
    
    # Set the global trace provider so all instrumentation can use it
    trace.set_tracer_provider(trace_provider)

    # Initialize metrics collection infrastructure
    # MeterProvider manages all metric instruments and their lifecycle
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
        ), 
        export_interval_millis=5000  # Export metrics every 5 seconds
    )
    
    # Create and set the global meter provider
    metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(metric_provider)

    # Enable automatic instrumentation for zero-code observability
    # FastAPIInstrumentor: Automatically traces all HTTP requests, adds timing, etc.
    # HTTPXClientInstrumentor: Traces all outgoing HTTP calls to other services
    FastAPIInstrumentor().instrument()
    HTTPXClientInstrumentor().instrument()

    print("✅ OpenTelemetry observability initialized successfully!")
    print("   - Distributed tracing enabled with correlation ID support")
    print("   - Metrics collection active with 5-second export intervals")
    print("   - Automatic instrumentation for FastAPI and HTTPX")
    print("   - Service attribution: document-api v1.0.0 (development)")
    print("   - Exporting to: otel-collector:4317")
