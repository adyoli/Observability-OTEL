"""
Observability Utilities for Document API Service

This module provides comprehensive observability utilities that work on top of the
OpenTelemetry infrastructure. It includes middleware for request correlation,
structured logging, metrics collection, and span creation utilities.

Key Components:
- ObservabilityMiddleware: Injects correlation IDs and logs request lifecycle
- Metrics Collection: HTTP request counters, durations, and error rates
- Structured Logging: Context-aware logging with correlation IDs
- Span Creation: Utilities for creating and managing distributed traces
- Health Metrics: Specialized metrics for health check monitoring

Architecture:
1. Middleware generates correlation ID for each request
2. All subsequent operations use this ID for tracing and logging
3. Metrics are automatically collected with request context
4. Spans are created for custom operations and business logic
5. Structured logging provides context for debugging and monitoring

Usage:
    from observability import (
        ObservabilityMiddleware, 
        log_request_metrics, 
        create_span, 
        log_with_context
    )
    
    # Add middleware to FastAPI app
    app.add_middleware(ObservabilityMiddleware)
    
    # Create custom spans for business operations
    with create_span("operation_name", "operation_type", **attributes) as span:
        # Your business logic here
        pass
    
    # Log with context
    log_with_context("Message", level="info", **context_data)
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from opentelemetry import trace, metrics
from opentelemetry.trace import SpanKind
from opentelemetry.sdk.trace import Tracer
from opentelemetry.sdk.metrics import Meter
from telemetry import get_correlation_id, set_correlation_id, generate_correlation_id

# Get the global tracer and meter instances for this service
# These are configured in telemetry.py and provide the core observability infrastructure
tracer: Tracer = trace.get_tracer(__name__)
meter: Meter = metrics.get_meter(__name__)

# =============================================================================
# METRIC INSTRUMENTS
# =============================================================================
# These instruments collect metrics automatically and send them to the OTEL collector
# Each metric type serves a specific monitoring purpose

# Counter for total HTTP requests - tracks request volume by endpoint, method, and status
request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total number of HTTP requests processed by the service",
    unit="1"  # Count of requests
)

# Histogram for request duration - tracks response time performance and distribution
request_duration = meter.create_histogram(
    name="http_request_duration_seconds",
    description="HTTP request duration in seconds, used for performance monitoring",
    unit="s"  # Time in seconds
)

# Counter for HTTP errors - tracks error rates by endpoint and status code
error_counter = meter.create_counter(
    name="http_errors_total",
    description="Total number of HTTP errors (4xx and 5xx status codes)",
    unit="1"  # Count of errors
)

# Create structured logger with consistent formatting
# This logger will include correlation IDs and context in all log entries
logger = logging.getLogger(__name__)

class ObservabilityMiddleware:
    """
    Middleware for adding comprehensive observability to FastAPI requests.
    
    This middleware is the foundation of the observability system. It:
    1. Generates a unique correlation ID for each request
    2. Injects this ID into the request context
    3. Logs request start with full context
    4. Enables distributed tracing across all services
    
    The correlation ID flows through the entire request lifecycle, allowing
    engineers to trace requests from the load balancer through all services
    to the database and back.
    
    Architecture:
    - Generates UUID4 correlation ID for each request
    - Sets correlation ID in async context for the request duration
    - Logs request start with method, path, client IP, and user agent
    - Preserves all existing FastAPI functionality
    
    Usage:
        app.add_middleware(ObservabilityMiddleware)
        
    Example Correlation ID Flow:
        Request → Middleware generates "abc-123-def" → 
        Document API → Data Store → Database
        All operations tagged with "abc-123-def" for easy correlation
    """
    
    def __init__(self, app):
        """
        Initialize the observability middleware.
        
        Args:
            app: The FastAPI application instance to wrap
        """
        self.app = app
    
    async def __call__(self, scope, receive, send):
        """
        Process each request through the observability middleware.
        
        This method is called for every HTTP request and:
        1. Generates a unique correlation ID
        2. Sets it in the async context
        3. Logs request start information
        4. Processes the request normally
        
        Args:
            scope: ASGI scope containing request information
            receive: ASGI receive callable
            send: ASGI send callable
            
        Note:
            This middleware only processes HTTP requests. Other ASGI
            protocols (WebSocket, etc.) are passed through unchanged.
        """
        if scope["type"] == "http":
            # Generate a unique correlation ID for this request
            # This ID will be used throughout the entire request lifecycle
            correlation_id = generate_correlation_id()
            set_correlation_id(correlation_id)
            
            # Add correlation ID to scope for potential use by other middleware
            # This allows other components to access the correlation ID
            scope["correlation_id"] = correlation_id
            
            # Create a custom send function to capture response information
            # This allows us to log request start when the response begins
            async def custom_send(message):
                if message["type"] == "http.response.start":
                    # Extract client information for security and debugging
                    client_ip = scope.get("client", ("unknown", 0))[0]
                    
                    # Extract user agent for client identification
                    headers = dict(scope.get("headers", []))
                    user_agent = headers.get(b"user-agent", b"").decode()
                    
                    # Log request start with comprehensive context
                    # This provides immediate visibility into incoming requests
                    logger.info(
                        "Request started",
                        extra={
                            "correlation_id": correlation_id,
                            "method": scope["method"],
                            "path": scope["path"],
                            "client_ip": client_ip,
                            "user_agent": user_agent,
                            "request_type": "http_start"
                        }
                    )
                
                # Forward the message to the original send function
                await send(message)
            
            # Process the request through the wrapped application
            # All subsequent operations will have access to the correlation ID
            await self.app(scope, receive, custom_send)
        else:
            # For non-HTTP requests (WebSocket, etc.), pass through unchanged
            # This ensures the middleware doesn't interfere with other protocols
            await self.app(scope, receive, send)

def log_request_metrics(request: Request, response: Response, duration: float):
    """
    Log comprehensive metrics for an HTTP request.
    
    This function collects detailed metrics about each request including:
    - Request count by method, path, and status code
    - Request duration for performance monitoring
    - Error tracking for 4xx and 5xx responses
    
    All metrics include the correlation ID for request correlation and
    the ability to trace specific requests through the metrics.
    
    Args:
        request: FastAPI Request object containing request details
        response: FastAPI Response object containing response details
        duration: Request duration in seconds (float)
        
    Metrics Collected:
        - http_requests_total: Count of all requests
        - http_request_duration_seconds: Request duration histogram
        - http_errors_total: Count of error responses
        
    Example:
        >>> log_request_metrics(request, response, 0.125)
        >>> # Records: 1 request, 0.125s duration, error status if applicable
    """
    # Get the correlation ID for this request
    # This links all metrics to the specific request being processed
    correlation_id = get_correlation_id()
    
    # Increment the total request counter
    # This tracks overall request volume and can be used for capacity planning
    request_counter.add(1, {
        "method": request.method,           # HTTP method (GET, POST, PUT, etc.)
        "path": request.url.path,           # Request path (/health, /upload, etc.)
        "status_code": str(response.status_code),  # Response status (200, 404, 500, etc.)
        "correlation_id": correlation_id,   # Links metrics to specific requests
        "service": "document-api"          # Service identifier for multi-service monitoring
    })
    
    # Record request duration in the histogram
    # This provides detailed performance analysis including percentiles
    request_duration.record(duration, {
        "method": request.method,           # HTTP method for method-specific performance
        "path": request.url.path,           # Path for endpoint-specific performance
        "correlation_id": correlation_id,   # Request correlation
        "service": "document-api"          # Service attribution
    })
    
    # Increment error counter for 4xx and 5xx status codes
    # This tracks error rates and helps identify problematic endpoints
    if response.status_code >= 400:
        error_counter.add(1, {
            "method": request.method,           # HTTP method for error analysis
            "path": request.url.path,           # Endpoint for error localization
            "status_code": str(response.status_code),  # Specific error type
            "correlation_id": correlation_id,   # Links errors to specific requests
            "service": "document-api",         # Service attribution
            "error_category": "4xx" if response.status_code < 500 else "5xx"  # Error classification
        })

def create_span(name: str, operation: str, **attributes):
    """
    Create a custom span for distributed tracing.
    
    This function creates spans that represent specific operations within a request.
    Each span includes the correlation ID and any additional attributes provided,
    enabling detailed tracing of business logic and external service calls.
    
    Spans are automatically exported to the OTEL collector and can be viewed
    in tracing tools like Jaeger, Zipkin, or the collector's debug exporter.
    
    Args:
        name (str): Human-readable name for the span (e.g., "file_processing")
        operation (str): Type of operation (e.g., "document_processing", "data_operation")
        **attributes: Additional key-value pairs to attach to the span
        
    Returns:
        Span: An OpenTelemetry span object that can be used as a context manager
        
    Usage:
        >>> with create_span("upload_document", "document_upload", client_id="123") as span:
        >>>     # Your business logic here
        >>>     span.set_attribute("file_size", 1024)
        >>>     # Span automatically ends when context exits
        
    Example Attributes:
        - client_id: Identifies the client making the request
        - file_size: Size of uploaded files for capacity monitoring
        - operation_type: Type of business operation being performed
        - external_service: Name of external service being called
    """
    # Get the current correlation ID to link this span to the request
    correlation_id = get_correlation_id()
    
    # Build comprehensive span attributes
    # These attributes provide context for debugging and monitoring
    span_attributes = {
        "correlation_id": correlation_id,    # Links span to specific request
        "operation": operation,              # Operation type for categorization
        "service": "document-api",          # Service attribution
        **attributes                         # Additional custom attributes
    }
    
    # Create and return the span
    # SpanKind.INTERNAL indicates this is an internal operation within the service
    return tracer.start_span(
        name=name,
        kind=SpanKind.INTERNAL,
        attributes=span_attributes
    )

def log_with_context(message: str, level: str = "info", **kwargs):
    """
    Log a message with correlation ID and additional context.
    
    This function provides structured logging that automatically includes
    the correlation ID and any additional context data. This enables
    engineers to trace log entries back to specific requests and
    understand the full context of any operation.
    
    The logging is structured and can be easily parsed by log aggregation
    systems like ELK Stack, Splunk, or cloud logging services.
    
    Args:
        message (str): The log message to record
        level (str): Log level (debug, info, warning, error, critical)
        **kwargs: Additional context data to include in the log
        
    Log Levels:
        - debug: Detailed information for debugging
        - info: General information about normal operations
        - warning: Situations that might need attention
        - error: Error conditions that don't stop operation
        - critical: Critical errors that might cause service failure
        
    Example:
        >>> log_with_context(
        >>>     "File uploaded successfully",
        >>>     level="info",
        >>>     client_id="123",
        >>>     file_size=1024,
        >>>     file_type="text/plain"
        >>> )
        >>> # Result: Structured log with correlation_id, client_id, file_size, file_type
        
    Structured Output:
        {
            "correlation_id": "abc-123-def",
            "log_message": "File uploaded successfully",
            "client_id": "123",
            "file_size": 1024,
            "file_type": "text/plain",
            "timestamp": "2025-08-20T08:00:00Z",
            "level": "info"
        }
    """
    # Get the current correlation ID for request correlation
    correlation_id = get_correlation_id()
    
    # Build the complete log data structure
    # This includes the correlation ID and all additional context
    log_data = {
        "correlation_id": correlation_id,    # Links log to specific request
        "log_message": message,              # The actual log message
        "service": "document-api",          # Service attribution
        "timestamp": time.time(),           # Unix timestamp for correlation
        **kwargs                            # Additional context data
    }
    
    # Log at the appropriate level with structured data
    # Each level provides different visibility in production environments
    if level == "debug":
        logger.debug(message, extra=log_data)
    elif level == "info":
        logger.info(message, extra=log_data)
    elif level == "warning":
        logger.warning(message, extra=log_data)
    elif level == "error":
        logger.error(message, extra=log_data)
    elif level == "critical":
        logger.critical(message, extra=log_data)
    else:
        # Default to info level for unknown levels
        logger.info(message, extra=log_data)

def create_health_metrics():
    """
    Create specialized metrics for health check monitoring.
    
    This function creates metrics specifically designed for monitoring
    service health and availability. These metrics help identify:
    - Service availability and uptime
    - Health check performance and latency
    - Health check failure patterns
    
    Returns:
        tuple: (health_check_counter, health_check_duration)
            - health_check_counter: Counts health check requests by status
            - health_check_duration: Measures health check response time
            
    Usage:
        >>> counter, duration = create_health_metrics()
        >>> counter.add(1, {"status": "healthy"})
        >>> duration.record(0.125)
        
    Health Check Statuses:
        - healthy: Service is fully operational
        - degraded: Service has partial functionality
        - unhealthy: Service is not operational
        
    Example Metrics:
        - health_check_total{status="healthy"}: Count of successful health checks
        - health_check_duration_seconds{status="healthy"}: Response time distribution
    """
    # Counter for health check requests
    # Tracks health check volume and success/failure rates
    health_check_counter = meter.create_counter(
        name="health_check_total",
        description="Total number of health check requests with status breakdown",
        unit="1"  # Count of health checks
    )
    
    # Histogram for health check duration
    # Monitors health check performance and identifies slow responses
    health_check_duration = meter.create_histogram(
        name="health_check_duration_seconds",
        description="Health check response time in seconds for performance monitoring",
        unit="s"  # Time in seconds
    )
    
    return health_check_counter, health_check_duration
