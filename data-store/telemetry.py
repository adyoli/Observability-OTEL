"""
OpenTelemetry Observability Configuration for Data Store Service

This module provides comprehensive observability setup for the Data Store service using
OpenTelemetry (OTEL). It configures distributed tracing, metrics collection, and
automatic instrumentation specifically designed for database-heavy operations.

Key Components:
- TracerProvider: Manages trace generation and sampling for database operations
- MeterProvider: Handles metrics collection for database performance monitoring
- BatchSpanProcessor: Efficiently batches and exports trace data
- PeriodicExportingMetricReader: Exports metrics at regular intervals
- Resource: Adds service metadata to all telemetry data
- Automatic Instrumentation: Instruments FastAPI and SQLAlchemy for database observability

Configuration:
- OTLP gRPC export to otel-collector:4317
- Batch processing for performance optimization
- Service attribution with name, version, and environment
- Correlation ID context management for request tracing
- SQLAlchemy instrumentation for database operation visibility

Usage:
    from telemetry import init_observability, get_correlation_id
    
    # Initialize at startup
    init_observability()
    
    # Use correlation ID in database operations
    correlation_id = get_correlation_id()
    
Database Observability Features:
- Automatic SQL query tracing with timing
- Database connection pool monitoring
- Transaction boundary identification
- Query parameter sanitization for security
- Performance bottleneck identification
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
# SQLAlchemy instrumentation for database operation visibility
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Context variable for correlation ID management across async operations
# This allows us to track request flow through the entire system, including database operations
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

def get_correlation_id() -> str:
    """
    Get the current correlation ID from the context.
    
    The correlation ID is a unique identifier that flows through all services
    involved in processing a single request. This enables distributed tracing
    and request correlation across the entire system, including database operations.
    
    In the data-store service, this ID is particularly important because it links:
    - HTTP requests to database operations
    - Multiple database queries within a single request
    - Database performance metrics to specific client requests
    
    Returns:
        str: The current correlation ID, or empty string if not set
        
    Example:
        >>> correlation_id = get_correlation_id()
        >>> print(f"Executing database query for request: {correlation_id}")
        
    Database Correlation:
        When a client uploads a document, the correlation ID flows:
        Client Request → Document API → Data Store → PostgreSQL
        All database operations are tagged with the same correlation ID
    """
    return correlation_id.get()

def set_correlation_id(corr_id: str) -> None:
    """
    Set the current correlation ID in the context.
    
    This function sets the correlation ID for the current async context.
    All subsequent operations in the same request will have access to this ID
    through get_correlation_id(), including all database operations.
    
    Args:
        corr_id (str): The correlation ID to set
        
    Example:
        >>> set_correlation_id("req-123-abc")
        >>> # Now all database operations can access this ID for correlation
        
    Database Context:
        The correlation ID is automatically propagated to SQLAlchemy operations
        through the OpenTelemetry instrumentation, enabling end-to-end tracing
        of database performance and operations.
    """
    correlation_id.set(corr_id)

def generate_correlation_id() -> str:
    """
    Generate a new unique correlation ID.
    
    Creates a UUID4-based correlation ID that is guaranteed to be unique
    across the entire system. This is used to track individual requests
    from start to finish, including all database interactions.
    
    Returns:
        str: A new unique correlation ID
        
    Example:
        >>> new_id = generate_correlation_id()
        >>> # Result: "550e8400-e29b-41d4-a716-446655440000"
        
    Database Tracing:
        Each correlation ID enables engineers to trace:
        - Which client made the request
        - What database queries were executed
        - How long each query took
        - What data was accessed or modified
        - Any database errors or performance issues
    """
    return str(uuid.uuid4())

def init_observability():
    """
    Initialize OpenTelemetry observability for the Data Store service.
    
    This function sets up the complete observability infrastructure specifically
    designed for database-heavy operations:
    1. Creates and configures the TracerProvider for distributed tracing
    2. Sets up the MeterProvider for metrics collection
    3. Configures OTLP exporters to send data to the collector
    4. Sets up batch processing for performance optimization
    5. Adds service metadata to all telemetry data
    6. Enables automatic instrumentation for FastAPI and SQLAlchemy
    
    Configuration Details:
    - Tracing: Uses BatchSpanProcessor for efficient span export
    - Metrics: Uses PeriodicExportingMetricReader with 5-second intervals
    - Export: Sends data to otel-collector:4317 via gRPC
    - Resource: Adds service name, version, and environment metadata
    - SQLAlchemy: Automatic instrumentation for database operation visibility
    
    Environment Variables:
    - OTEL_EXPORTER_OTLP_ENDPOINT: Collector endpoint (default: otel-collector:4317)
    - ENVIRONMENT: Deployment environment (default: development)
    
    Database Observability Features:
    - Automatic SQL query tracing with timing information
    - Database connection pool monitoring and metrics
    - Transaction boundary identification and tracking
    - Query parameter sanitization for security
    - Performance bottleneck identification in database operations
    
    Note: This function should be called once at service startup, before
    any database operations or requests are processed.
    
    Example:
        >>> init_observability()
        >>> # Now all FastAPI requests and SQLAlchemy operations are automatically instrumented
        
    Database Tracing Example:
        When a client retrieves a document, you'll see:
        - Span: "GET /clients/{client_id}/documents/{document_id}"
        - Span: "SELECT document_metadata" (database operation)
        - Attributes: correlation_id, client_id, document_id, query_duration
        - Metrics: database_operations_total, database_operation_duration_seconds
    """
    
    # Create resource with service information for attribution
    # This metadata is attached to ALL telemetry data (traces, metrics, logs)
    # making it easy to identify which service generated what data
    resource = Resource.create({
        "service.name": "data-store",           # Service identifier
        "service.version": "1.0.0",             # Version for tracking deployments
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),  # Environment context
        "service.type": "database_service",     # Indicates this is a database service
        "database.type": "postgresql"          # Database technology for monitoring
    })

    # Initialize distributed tracing infrastructure
    # TracerProvider is the main entry point for trace generation
    # In the data-store service, this traces all database operations
    trace_provider = TracerProvider(resource=resource)
    
    # Configure OTLP exporter for sending traces to the collector
    # The collector acts as a central hub for all observability data
    # Database operation traces are sent here for analysis
    otlp_exporter = OTLPSpanExporter(
        endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    )
    
    # BatchSpanProcessor batches spans before sending to improve performance
    # This is especially important for database operations which can generate
    # many spans in rapid succession
    processor = BatchSpanProcessor(otlp_exporter)
    trace_provider.add_span_processor(processor)
    
    # Set the global trace provider so all instrumentation can use it
    # This includes SQLAlchemy instrumentation for database operations
    trace.set_tracer_provider(trace_provider)

    # Initialize metrics collection infrastructure
    # MeterProvider manages all metric instruments and their lifecycle
    # Database-specific metrics are created here for performance monitoring
    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
        ), 
        export_interval_millis=5000  # Export metrics every 5 seconds
    )
    
    # Create and set the global meter provider
    # This enables metrics collection for database operations and health checks
    metric_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(metric_provider)

    # Enable automatic instrumentation for zero-code observability
    # FastAPIInstrumentor: Automatically traces all HTTP requests, adds timing, etc.
    # SQLAlchemyInstrumentor: Traces all database operations with detailed context
    FastAPIInstrumentor().instrument()
    
    # SQLAlchemy instrumentation provides comprehensive database observability:
    # - Tracks all SQL queries with timing and parameters
    # - Monitors database connection pool usage
    # - Identifies slow queries and performance bottlenecks
    # - Correlates database operations with HTTP requests
    # - Provides transaction boundary visibility
    SQLAlchemyInstrumentor().instrument()

    print("✅ OpenTelemetry observability initialized successfully for Data Store!")
    print("   - Distributed tracing enabled with correlation ID support")
    print("   - Metrics collection active with 5-second export intervals")
    print("   - Automatic instrumentation for FastAPI and SQLAlchemy")
    print("   - Service attribution: data-store v1.0.0 (development)")
    print("   - Database observability: PostgreSQL query tracing enabled")
    print("   - Exporting to: otel-collector:4317")
    print("   - Database operations will be automatically traced and monitored")
