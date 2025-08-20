"""
Observability Utilities for Data Store Service

This module provides comprehensive observability utilities specifically designed for
database-heavy operations. It includes middleware for request correlation,
structured logging, metrics collection, and specialized database operation tracking.

Key Components:
- ObservabilityMiddleware: Injects correlation IDs and logs request lifecycle
- Metrics Collection: HTTP request counters, durations, and error rates
- Database Metrics: Specialized metrics for database operation monitoring
- Structured Logging: Context-aware logging with correlation IDs
- Span Creation: Utilities for creating and managing distributed traces
- Database Operation Tracking: Comprehensive database performance monitoring
- Health Metrics: Specialized metrics for health check monitoring

Architecture:
1. Middleware generates correlation ID for each request
2. All subsequent operations use this ID for tracing and logging
3. Metrics are automatically collected with request context
4. Database operations are tracked with detailed performance metrics
5. Spans are created for custom operations and business logic
6. Structured logging provides context for debugging and monitoring

Database Observability Features:
- Automatic SQL query tracing with timing
- Database operation counters and duration histograms
- Table-level operation attribution
- Success/failure tracking for all database operations
- Performance bottleneck identification
- Connection pool monitoring

Usage:
    from observability import (
        ObservabilityMiddleware, 
        log_request_metrics, 
        create_span, 
        log_with_context,
        track_db_operation
    )
    
    # Add middleware to FastAPI app
    app.add_middleware(ObservabilityMiddleware)
    
    # Track database operations with detailed metrics
    with track_db_operation("insert", "documentmetadata", client_id="123") as db_tracker:
        # Your database operation here
        db.add(document)
        db.commit()
    
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
# The meter is particularly important for database operation metrics
tracer: Tracer = trace.get_tracer(__name__)
meter: Meter = metrics.get_meter(__name__)

# =============================================================================
# METRIC INSTRUMENTS
# =============================================================================
# These instruments collect metrics automatically and send them to the OTEL collector
# Each metric type serves a specific monitoring purpose, with special focus on database operations

# Counter for total HTTP requests - tracks request volume by endpoint, method, and status
request_counter = meter.create_counter(
    name="http_requests_total",
    description="Total number of HTTP requests processed by the data-store service",
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

# =============================================================================
# DATABASE-SPECIFIC METRICS
# =============================================================================
# These metrics provide detailed visibility into database performance and operations
# They are essential for identifying database bottlenecks and monitoring query performance

# Counter for database operations - tracks operation volume by type, table, and success status
db_operation_counter = meter.create_counter(
    name="database_operations_total",
    description="Total number of database operations with detailed breakdown by operation type, table, and success status",
    unit="1"  # Count of database operations
)

# Histogram for database operation duration - tracks query performance and identifies slow operations
db_operation_duration = meter.create_histogram(
    name="database_operation_duration_seconds",
    description="Database operation duration in seconds for performance monitoring and bottleneck identification",
    unit="s"  # Time in seconds
)

# Create structured logger with consistent formatting
# This logger will include correlation IDs and context in all log entries
# Database operations are logged with detailed context for debugging
logger = logging.getLogger(__name__)

class ObservabilityMiddleware:
    """
    Middleware for adding comprehensive observability to FastAPI requests in the data-store service.
    
    This middleware is the foundation of the observability system for database operations. It:
    1. Generates a unique correlation ID for each request
    2. Injects this ID into the request context
    3. Logs request start with full context
    4. Enables distributed tracing across all services and database operations
    
    The correlation ID flows through the entire request lifecycle, allowing
    engineers to trace requests from the load balancer through the data-store service
    to the PostgreSQL database and back. This is crucial for database performance
    analysis and troubleshooting.
    
    Architecture:
    - Generates UUID4 correlation ID for each request
    - Sets correlation ID in async context for the request duration
    - Logs request start with method, path, client IP, and user agent
    - Preserves all existing FastAPI functionality
    - Enables correlation between HTTP requests and database operations
    
    Usage:
        app.add_middleware(ObservabilityMiddleware)
        
    Example Correlation ID Flow:
        Request → Middleware generates "abc-123-def" → 
        Data Store API → Database Query → PostgreSQL
        All operations tagged with "abc-123-def" for easy correlation
        
    Database Correlation Benefits:
        - Link HTTP requests to specific database queries
        - Track database performance per request
        - Identify which requests cause database bottlenecks
        - Correlate database errors with client requests
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
        
        The correlation ID is particularly important for database operations
        as it links HTTP requests to database queries for performance analysis.
        
        Args:
            scope: ASGI scope containing request information
            receive: ASGI receive callable
            send: ASGI send callable
            
        Note:
            This middleware only processes HTTP requests. Other ASGI
            protocols (WebSocket, etc.) are passed through unchanged.
            
        Database Context:
            The correlation ID is automatically propagated to all database
            operations through SQLAlchemy instrumentation, enabling end-to-end
            tracing of database performance and operations.
        """
        if scope["type"] == "http":
            # Generate a unique correlation ID for this request
            # This ID will be used throughout the entire request lifecycle
            # including all database operations performed during the request
            correlation_id = generate_correlation_id()
            set_correlation_id(correlation_id)
            
            # Add correlation ID to scope for potential use by other middleware
            # This allows other components to access the correlation ID
            # and link their operations to the same request
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
                    # and helps correlate HTTP requests with database operations
                    logger.info(
                        "Request started",
                        extra={
                            "correlation_id": correlation_id,
                            "method": scope["method"],
                            "path": scope["path"],
                            "client_ip": client_ip,
                            "user_agent": user_agent,
                            "request_type": "http_start",
                            "service": "data-store"
                        }
                    )
                
                # Forward the message to the original send function
                await send(message)
            
            # Process the request through the wrapped application
            # All subsequent operations will have access to the correlation ID
            # This includes all database operations performed during the request
            await self.app(scope, receive, custom_send)
        else:
            # For non-HTTP requests (WebSocket, etc.), pass through unchanged
            # This ensures the middleware doesn't interfere with other protocols
            await self.app(scope, receive, send)

def log_request_metrics(request: Request, response: Response, duration: float):
    """
    Log comprehensive metrics for an HTTP request in the data-store service.
    
    This function collects detailed metrics about each request including:
    - Request count by method, path, and status code
    - Request duration for performance monitoring
    - Error tracking for 4xx and 5xx responses
    
    All metrics include the correlation ID for request correlation and
    the ability to trace specific requests through the metrics. This is
    particularly important for correlating HTTP requests with database
    operations and performance.
    
    Args:
        request: FastAPI Request object containing request details
        response: FastAPI Response object containing response details
        duration: Request duration in seconds (float)
        
    Metrics Collected:
        - http_requests_total: Count of all requests
        - http_request_duration_seconds: Request duration histogram
        - http_errors_total: Count of error responses
        
    Database Correlation:
        The correlation ID links HTTP requests to database operations,
        enabling engineers to identify which requests cause database
        performance issues or errors.
        
    Example:
        >>> log_request_metrics(request, response, 0.125)
        >>> # Records: 1 request, 0.125s duration, error status if applicable
        >>> # Links to database operations with the same correlation ID
    """
    # Get the correlation ID for this request
    # This links all metrics to the specific request being processed
    # and enables correlation with database operation metrics
    correlation_id = get_correlation_id()
    
    # Increment the total request counter
    # This tracks overall request volume and can be used for capacity planning
    # The correlation ID links this metric to specific database operations
    request_counter.add(1, {
        "method": request.method,           # HTTP method (GET, POST, PUT, etc.)
        "path": request.url.path,           # Request path (/health, /documents, etc.)
        "status_code": str(response.status_code),  # Response status (200, 404, 500, etc.)
        "correlation_id": correlation_id,   # Links metrics to specific requests
        "service": "data-store",           # Service identifier for multi-service monitoring
        "service_type": "database_service" # Indicates this is a database service
    })
    
    # Record request duration in the histogram
    # This provides detailed performance analysis including percentiles
    # Database-heavy requests will show longer durations, helping identify bottlenecks
    request_duration.record(duration, {
        "method": request.method,           # HTTP method for method-specific performance
        "path": request.url.path,           # Path for endpoint-specific performance
        "correlation_id": correlation_id,   # Request correlation
        "service": "data-store",           # Service attribution
        "service_type": "database_service" # Service type for monitoring
    })
    
    # Increment error counter for 4xx and 5xx status codes
    # This tracks error rates and helps identify problematic endpoints
    # Database errors (e.g., connection failures, query errors) will be captured here
    if response.status_code >= 400:
        error_counter.add(1, {
            "method": request.method,           # HTTP method for error analysis
            "path": request.url.path,           # Endpoint for error localization
            "status_code": str(response.status_code),  # Specific error type
            "correlation_id": correlation_id,   # Links errors to specific requests
            "service": "data-store",           # Service attribution
            "service_type": "database_service", # Service type for error categorization
            "error_category": "4xx" if response.status_code < 500 else "5xx"  # Error classification
        })

def create_span(name: str, operation: str, **attributes):
    """
    Create a custom span for distributed tracing in the data-store service.
    
    This function creates spans that represent specific operations within a request.
    Each span includes the correlation ID and any additional attributes provided,
    enabling detailed tracing of business logic, database operations, and external
    service calls.
    
    Spans are automatically exported to the OTEL collector and can be viewed
    in tracing tools like Jaeger, Zipkin, or the collector's debug exporter.
    Database operation spans are particularly valuable for performance analysis.
    
    Args:
        name (str): Human-readable name for the span (e.g., "create_document")
        operation (str): Type of operation (e.g., "document_creation", "data_operation")
        **attributes: Additional key-value pairs to attach to the span
        
    Returns:
        Span: An OpenTelemetry span object that can be used as a context manager
        
    Usage:
        >>> with create_span("create_document", "document_creation", client_id="123") as span:
        >>>     # Your business logic here
        >>>     span.set_attribute("document_keys", ["filename", "file_size"])
        >>>     # Span automatically ends when context exits
        
    Example Attributes:
        - client_id: Identifies the client making the request
        - table_name: Database table being operated on
        - operation_type: Type of database operation (insert, select, update, delete)
        - document_id: ID of the document being processed
        - file_size: Size of uploaded files for capacity monitoring
        
    Database Tracing Benefits:
        - Identify slow database operations
        - Track database operation patterns
        - Correlate database performance with business operations
        - Monitor database connection usage
        - Debug database-related errors
    """
    # Get the current correlation ID to link this span to the request
    correlation_id = get_correlation_id()
    
    # Build comprehensive span attributes
    # These attributes provide context for debugging and monitoring
    # Database-specific attributes help identify performance patterns
    span_attributes = {
        "correlation_id": correlation_id,    # Links span to specific request
        "operation": operation,              # Operation type for categorization
        "service": "data-store",            # Service attribution
        "service_type": "database_service", # Service type for monitoring
        **attributes                         # Additional custom attributes
    }
    
    # Create and return the span
    # SpanKind.INTERNAL indicates this is an internal operation within the service
    # Database operations are typically internal operations
    return tracer.start_span(
        name=name,
        kind=SpanKind.INTERNAL,
        attributes=span_attributes
    )

def log_with_context(message: str, level: str = "info", **kwargs):
    """
    Log a message with correlation ID and additional context in the data-store service.
    
    This function provides structured logging that automatically includes
    the correlation ID and any additional context data. This enables
    engineers to trace log entries back to specific requests and
    understand the full context of any operation, especially database operations.
    
    The logging is structured and can be easily parsed by log aggregation
    systems like ELK Stack, Splunk, or cloud logging services. Database
    operation logs include detailed context for troubleshooting.
    
    Args:
        message (str): The log message to record
        level (str): Log level (debug, info, warning, error, critical)
        **kwargs: Additional context data to include in the log
        
    Log Levels:
        - debug: Detailed information for debugging (includes SQL queries)
        - info: General information about normal operations
        - warning: Situations that might need attention (e.g., slow queries)
        - error: Error conditions that don't stop operation (e.g., query timeouts)
        - critical: Critical errors that might cause service failure (e.g., DB connection loss)
        
    Example:
        >>> log_with_context(
        >>>     "Document metadata stored successfully",
        >>>     level="info",
        >>>     client_id="123",
        >>>     document_id=456,
        >>>     table_name="document_metadata",
        >>>     operation_type="insert"
        >>> )
        >>> # Result: Structured log with correlation_id, client_id, document_id, etc.
        
    Structured Output:
        {
            "correlation_id": "abc-123-def",
            "log_message": "Document metadata stored successfully",
            "client_id": "123",
            "document_id": 456,
            "table_name": "document_metadata",
            "operation_type": "insert",
            "timestamp": 1692537600.0,
            "level": "info",
            "service": "data-store",
            "service_type": "database_service"
        }
        
    Database Logging Benefits:
        - Track database operation success/failure
        - Monitor database performance patterns
        - Debug database-related issues
        - Correlate logs with database metrics
        - Identify database bottlenecks
    """
    # Get the current correlation ID for request correlation
    correlation_id = get_correlation_id()
    
    # Build the complete log data structure
    # This includes the correlation ID and all additional context
    # Database-specific context helps with troubleshooting and monitoring
    log_data = {
        "correlation_id": correlation_id,    # Links log to specific request
        "log_message": message,              # The actual log message
        "service": "data-store",            # Service attribution
        "service_type": "database_service", # Service type for categorization
        "timestamp": time.time(),           # Unix timestamp for correlation
        **kwargs                            # Additional context data
    }
    
    # Log at the appropriate level with structured data
    # Each level provides different visibility in production environments
    # Database operations are logged at appropriate levels for monitoring
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
    Create specialized metrics for health check monitoring in the data-store service.
    
    This function creates metrics specifically designed for monitoring
    service health and availability, with special focus on database connectivity
    and performance. These metrics help identify:
    - Service availability and uptime
    - Database connectivity status and latency
    - Health check performance and response time
    - Database table availability and status
    - Health check failure patterns and root causes
    
    Returns:
        tuple: (health_check_counter, health_check_duration)
            - health_check_counter: Counts health check requests by status
            - health_check_duration: Measures health check response time
            
    Usage:
        >>> counter, duration = create_health_metrics()
        >>> counter.add(1, {"status": "healthy", "database_status": "healthy"})
        >>> duration.record(0.125)
        
    Health Check Statuses:
        - healthy: Service and database are fully operational
        - degraded: Service has partial functionality (e.g., slow database)
        - unhealthy: Service is not operational (e.g., database connection lost)
        
    Database Health Metrics:
        - database_connectivity: Database connection status
        - database_latency: Database response time
        - table_availability: Database table existence and accessibility
        - connection_pool_status: Database connection pool health
        
    Example Metrics:
        - health_check_total{status="healthy", database_status="healthy"}: Count of successful health checks
        - health_check_duration_seconds{status="healthy"}: Response time distribution for healthy checks
        - health_check_total{status="degraded", database_status="slow"}: Count of degraded database performance
    """
    # Counter for health check requests
    # Tracks health check volume and success/failure rates
    # Includes database-specific status for comprehensive monitoring
    health_check_counter = meter.create_counter(
        name="health_check_total",
        description="Total number of health check requests with status and database health breakdown",
        unit="1"  # Count of health checks
    )
    
    # Histogram for health check duration
    # Monitors health check performance and identifies slow responses
    # Database-heavy health checks will show longer durations
    health_check_duration = meter.create_histogram(
        name="health_check_duration_seconds",
        description="Health check response time in seconds for performance monitoring and database health assessment",
        unit="s"  # Time in seconds
    )
    
    return health_check_counter, health_check_duration

def track_db_operation(operation: str, table: str, **attributes):
    """
    Track database operation with comprehensive metrics and tracing.
    
    This function provides detailed monitoring of database operations including:
    - Operation timing and performance metrics
    - Success/failure tracking
    - Table-level attribution
    - Correlation with HTTP requests
    - Performance bottleneck identification
    
    The function returns a context manager that automatically:
    1. Creates a span for the database operation
    2. Records operation start time
    3. Captures operation duration
    4. Records success/failure metrics
    5. Sets span attributes for debugging
    
    Args:
        operation (str): Type of database operation (insert, select, update, delete)
        table (str): Database table name for operation attribution
        **attributes: Additional attributes to include in metrics and spans
        
    Returns:
        DBOperationTracker: Context manager for tracking database operations
        
    Usage:
        >>> with track_db_operation("insert", "documentmetadata", client_id="123") as db_tracker:
        >>>     # Your database operation here
        >>>     db.add(document)
        >>>     db.commit()
        >>>     # Metrics and spans are automatically recorded
        
    Example Attributes:
        - client_id: Client making the request
        - document_id: Document being operated on
        - operation_type: Specific operation details
        - batch_size: Number of records being processed
        
    Metrics Collected:
        - database_operations_total: Count by operation, table, and success
        - database_operation_duration_seconds: Duration histogram by operation and table
        
    Tracing Benefits:
        - Identify slow database operations
        - Track database operation patterns
        - Correlate database performance with business operations
        - Debug database-related errors
        - Monitor database connection usage
        
    Example Output:
        When inserting a document, you'll see:
        - Span: "db_insert" with table="documentmetadata"
        - Metrics: database_operations_total{operation="insert", table="documentmetadata", success="true"}
        - Duration: database_operation_duration_seconds{operation="insert", table="documentmetadata"}
    """
    # Get the current correlation ID for request correlation
    correlation_id = get_correlation_id()
    
    # Create span for database operation
    # This span represents the database operation and includes all relevant context
    span = create_span(f"db_{operation}", "database_operation", table=table, **attributes)
    
    # Create context manager for timing and metrics collection
    # This ensures metrics and spans are properly recorded even if exceptions occur
    class DBOperationTracker:
        """
        Context manager for tracking database operations with comprehensive observability.
        
        This class provides automatic timing, metrics collection, and span management
        for database operations. It ensures that all database operations are properly
        monitored regardless of success or failure.
        
        Attributes:
            span: OpenTelemetry span for the database operation
            operation: Type of database operation being tracked
            table: Database table being operated on
            start_time: When the operation started (set in __enter__)
        """
        
        def __init__(self, span, operation, table):
            """
            Initialize the database operation tracker.
            
            Args:
                span: OpenTelemetry span for the operation
                operation: Type of database operation
                table: Database table name
            """
            self.span = span
            self.operation = operation
            self.table = table
            self.start_time = None
            
        def __enter__(self):
            """
            Enter the database operation context.
            
            Records the start time and returns self for attribute access.
            
            Returns:
                self: The tracker instance for attribute access
            """
            self.start_time = time.time()
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            """
            Exit the database operation context.
            
            Automatically records metrics, sets span attributes, and ends the span.
            This method is called regardless of whether the operation succeeded or failed.
            
            Args:
                exc_type: Exception type if an exception occurred
                exc_val: Exception value if an exception occurred
                exc_tb: Exception traceback if an exception occurred
            """
            # Calculate operation duration
            duration = time.time() - self.start_time
            
            # Record operation count metric
            # This tracks operation volume and success rates by operation type and table
            db_operation_counter.add(1, {
                "operation": operation,           # Operation type (insert, select, update, delete)
                "table": table,                   # Database table name
                "success": exc_type is None,      # Whether operation succeeded
                "correlation_id": correlation_id, # Links to specific request
                "service": "data-store",         # Service attribution
                "service_type": "database_service" # Service type for monitoring
            })
            
            # Record operation duration metric
            # This provides performance analysis and helps identify slow operations
            db_operation_duration.record(duration, {
                "operation": operation,           # Operation type for performance analysis
                "table": table,                   # Table for table-specific performance
                "correlation_id": correlation_id, # Request correlation
                "service": "data-store",         # Service attribution
                "service_type": "database_service" # Service type for monitoring
            })
            
            # Set span attributes for debugging and monitoring
            # These attributes provide context for tracing and analysis
            self.span.set_attribute("duration", duration)           # Operation duration
            self.span.set_attribute("success", exc_type is None)    # Success status
            self.span.set_attribute("table", table)                 # Table name
            self.span.set_attribute("operation_type", operation)    # Operation type
            
            # If an exception occurred, capture error details
            if exc_type:
                self.span.set_attribute("error", str(exc_val))      # Error message
                self.span.set_attribute("error_type", exc_type.__name__)  # Error type
                
                # Log the error with context for debugging
                log_with_context(
                    f"Database operation failed: {operation} on {table}",
                    level="error",
                    operation=operation,
                    table=table,
                    error=str(exc_val),
                    duration=duration
                )
            else:
                # Log successful operation for monitoring
                log_with_context(
                    f"Database operation completed: {operation} on {table}",
                    level="debug",
                    operation=operation,
                    table=table,
                    duration=duration
                )
            
            # End the span to complete the trace
            # This ensures the span is properly exported to the collector
            self.span.end()
    
    # Return the context manager for use in with statements
    return DBOperationTracker(span, operation, table)
