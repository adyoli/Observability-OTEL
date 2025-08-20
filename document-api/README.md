# 🚀 Document API Service - Comprehensive Documentation

## 📋 Table of Contents

1. [Service Overview](#service-overview)
2. [Architecture & Components](#architecture--components)
3. [API Endpoints](#api-endpoints)
4. [Observability Features](#observability-features)
5. [Development & Testing](#development--testing)
6. [Deployment & Configuration](#deployment--configuration)

---

## 🎯 Service Overview

The **Document API Service** is a FastAPI-based microservice that handles document uploads, processing, and management for the multi-tenant document management system. It provides a RESTful API interface with comprehensive observability, automatic instrumentation, and enterprise-grade monitoring capabilities.

### 🌟 Key Features

- **📤 Document Upload & Processing**: Multi-format file handling with LLM summarization
- **🔍 Complete Observability**: Distributed tracing, metrics, and structured logging
- **🔒 Multi-tenant Support**: Client-based isolation and routing
- **🏥 Health Monitoring**: Component-level health checks with detailed status
- **📊 Performance Tracking**: Request timing, error rates, and resource usage
- **🔄 Correlation ID System**: End-to-end request tracing across services

---

## 🏗️ Architecture & Components

### Service Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        C[Client Applications]
        LB[Load Balancer<br/>nginx]
    end
    
    subgraph "Document API Service"
        API[FastAPI Application<br/>Port 8000]
        MW[ObservabilityMiddleware<br/>Correlation IDs]
        UP[Upload Handler<br/>File Processing]
        LLM[LLM Integration<br/>Document Summarization]
        HC[Health Checker<br/>Component Status]
    end
    
    subgraph "External Services"
        DS[Data Store Service<br/>Port 8001]
        FS[File System<br/>uploads/ directory]
        AI[AI/LLM Service<br/>Document Analysis]
    end
    
    subgraph "Observability Layer"
        OTEL[OpenTelemetry<br/>Tracing & Metrics]
        LOG[Structured Logging<br/>Correlation IDs]
        MET[Metrics Collection<br/>Prometheus Format]
    end
    
    C --> LB
    LB --> API
    
    API --> MW
    MW --> UP
    MW --> LLM
    MW --> HC
    
    UP --> FS
    UP --> DS
    LLM --> AI
    HC --> DS
    HC --> FS
    
    API --> OTEL
    API --> LOG
    API --> MET
    
    style API fill:#ff6b6b
    style MW fill:#4ecdc4
    style DS fill:#45b7d1
    style OTEL fill:#96ceb4
```

### Request Flow Architecture

```mermaid
sequenceDiagram
    participant Client
    participant nginx
    participant DocumentAPI
    participant Middleware
    participant UploadHandler
    participant LLMService
    participant DataStore
    participant FileSystem
    
    Note over Client,FileSystem: Document Upload Flow with Observability
    
    Client->>nginx: PUT /clients/{id}/upload-document
    nginx->>DocumentAPI: Forward request
    
    DocumentAPI->>Middleware: Process request
    Middleware->>Middleware: Generate correlation ID
    Middleware->>Middleware: Log request start
    Middleware->>UploadHandler: Handle file upload
    
    UploadHandler->>FileSystem: Save temporary file
    FileSystem-->>UploadHandler: File saved
    
    UploadHandler->>LLMService: Process with LLM
    LLMService-->>UploadHandler: Document summary
    
    UploadHandler->>DataStore: Store metadata
    DataStore-->>UploadHandler: Document ID
    
    UploadHandler->>FileSystem: Move to permanent location
    FileSystem-->>UploadHandler: File moved
    
    UploadHandler-->>Middleware: Upload complete
    Middleware->>Middleware: Log request completion
    Middleware-->>DocumentAPI: Response with correlation ID
    DocumentAPI-->>nginx: Success response
    nginx-->>Client: Document uploaded
    
    Note over DocumentAPI,FileSystem: Telemetry Export
    DocumentAPI->>OTELCollector: Traces + Metrics + Logs
```

### Component Interaction Diagram

```mermaid
graph LR
    subgraph "Core Components"
        C1[FastAPI App<br/>Main Application]
        C2[ObservabilityMiddleware<br/>Request Tracking]
        C3[Upload Handler<br/>File Processing]
        C4[Health Checker<br/>Service Monitoring]
        C5[LLM Integration<br/>AI Processing]
    end
    
    subgraph "Supporting Modules"
        S1[Telemetry<br/>OTEL Configuration]
        S2[Observability<br/>Utilities & Helpers]
        S3[Config<br/>Environment Settings]
        S4[Schemas<br/>Data Validation]
    end
    
    subgraph "External Dependencies"
        E1[Data Store<br/>Metadata Storage]
        E2[File System<br/>Document Storage]
        E3[LLM Service<br/>AI Processing]
        E4[OTEL Collector<br/>Telemetry Hub]
    end
    
    C1 --> C2
    C1 --> C3
    C1 --> C4
    C1 --> C5
    
    C2 --> S1
    C3 --> S2
    C4 --> S3
    C5 --> S4
    
    C3 --> E1
    C3 --> E2
    C5 --> E3
    S1 --> E4
    
    style C1 fill:#ff6b6b
    style C2 fill:#4ecdc4
    style S1 fill:#45b7d1
    style E1 fill:#96ceb4
```

---

## 🔌 API Endpoints

### **Endpoint Overview**

```mermaid
graph TD
    subgraph "API Endpoints"
        E1["GET /health<br/>Health Check"]
        E2["PUT /clients/{id}/upload-document<br/>Document Upload"]
        E3["GET /clients/{id}/documents/{doc_id}<br/>Document Retrieval"]
    end
    
    subgraph "Health Check Response"
        H1[status: healthy/degraded/unhealthy]
        H2[components: file_system, data_store]
        H3[timestamp, version, uptime]
    end
    
    subgraph "Upload Response"
        U1[message: success/error]
        U2[client_id, document_id]
        U3[metadata: filename, size, type]
        U4[upload_timestamp]
    end
    
    subgraph "Retrieval Response"
        R1[document metadata]
        R2[client_id, document_id]
        R3[file information]
        R4[processing status]
    end
    
    E1 --> H1 & H2 & H3
    E2 --> U1 & U2 & U3 & U4
    E3 --> R1 & R2 & R3 & R4
    
    style E1 fill:#ff6b6b
    style E2 fill:#4ecdc4
    style E3 fill:#45b7d1
```

### **Request/Response Examples**

#### **Health Check**
```bash
curl http://localhost/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "document-api",
  "timestamp": "2025-08-20T08:13:49.822329",
  "components": {
    "file_system": "healthy",
    "data_store": "healthy"
  },
  "version": "1.0.0",
  "uptime_seconds": 86400
}
```

#### **Document Upload**
```bash
curl -X PUT http://localhost/clients/test-client-123/upload-document \
  -F "file=@test_file.txt"
```

**Response:**
```json
{
  "message": "Document uploaded successfully",
  "client_id": "test-client-123",
  "document_id": 5,
  "metadata": {
    "id": 5,
    "client_id": "test-client-123",
    "filename": "test_file.txt",
    "file_size": 50,
    "file_type": "text/plain",
    "upload_timestamp": "2025-08-20T08:10:48.108442Z"
  }
}
```

---

## 🔍 Observability Features

### **Distributed Tracing Architecture**

```mermaid
graph TD
    subgraph "Request Tracing"
        RT1[Request Start<br/>Correlation ID Generated]
        RT2[File Processing<br/>Upload & Validation]
        RT3[LLM Processing<br/>Document Analysis]
        RT4[Storage Operation<br/>Metadata & File]
        RT5[Response Complete<br/>Success/Error]
    end
    
    subgraph "Span Attributes"
        SA1[correlation_id<br/>Unique Request ID]
        SA2[client_id<br/>Tenant Identifier]
        SA3[file_size<br/>Document Size]
        SA4[file_type<br/>Document Format]
        SA5[processing_time<br/>Operation Duration]
    end
    
    subgraph "Trace Export"
        TE1[OTEL Collector<br/>Central Hub]
        TE2[Batch Processing<br/>Efficient Export]
        TE3[Storage Backends<br/>Jaeger, Zipkin]
        TE4[Visualization<br/>Trace Analysis]
    end
    
    RT1 --> RT2
    RT2 --> RT3
    RT3 --> RT4
    RT4 --> RT5
    
    RT1 --> SA1
    RT2 --> SA2
    RT3 --> SA3
    RT4 --> SA4
    RT5 --> SA5
    
    RT5 --> TE1
    TE1 --> TE2
    TE2 --> TE3
    TE3 --> TE4
    
    style RT1 fill:#ff6b6b
    style SA1 fill:#4ecdc4
    style TE1 fill:#45b7d1
```

### **Metrics Collection Structure**

```mermaid
graph LR
    subgraph "HTTP Metrics"
        HM1[http_requests_total<br/>Request Count]
        HM2[http_request_duration_seconds<br/>Response Time]
        HM3[http_errors_total<br/>Error Count]
        HM4[http_request_size_bytes<br/>Payload Size]
    end
    
    subgraph "Business Metrics"
        BM1[documents_uploaded_total<br/>Upload Volume]
        BM2[file_processing_duration<br/>Processing Time]
        BM3[llm_processing_duration<br/>AI Processing]
        BM4[client_activity_total<br/>Client Usage]
    end
    
    subgraph "System Metrics"
        SM1[health_check_total<br/>Health Status]
        SM2[health_check_duration<br/>Check Latency]
        SM3[file_system_status<br/>Storage Health]
        SM4[external_service_status<br/>Dependencies]
    end
    
    subgraph "Metric Dimensions"
        D1[service: document-api]
        D2[method: GET, PUT, POST]
        D3[path: /health, /upload, /documents]
        D4[status_code: 200, 400, 500]
        D5[client_id: tenant identifier]
    end
    
    HM1 --> D1
    HM2 --> D2
    HM3 --> D3
    HM4 --> D4
    
    BM1 --> D1
    BM2 --> D2
    BM3 --> D3
    BM4 --> D4
    
    SM1 --> D1
    SM2 --> D2
    SM3 --> D3
    SM4 --> D4
    
    style HM1 fill:#ff6b6b
    style BM1 fill:#4ecdc4
    style SM1 fill:#45b7d1
    style D1 fill:#96ceb4
```

### **Structured Logging Flow**

```mermaid
flowchart TD
    subgraph "Log Generation"
        LG1[Request Start<br/>Correlation ID]
        LG2[File Processing<br/>Upload Details]
        LG3[LLM Processing<br/>AI Analysis]
        LG4[Storage Operation<br/>Database Call]
        LG5[Response Complete<br/>Success/Error]
    end
    
    subgraph "Log Structure"
        LS1[correlation_id<br/>Request Identifier]
        LS2[timestamp<br/>Unix Timestamp]
        LS3[level<br/>DEBUG, INFO, WARNING, ERROR]
        LS4[message<br/>Human Readable]
        LS5[context<br/>Additional Data]
    end
    
    subgraph "Log Context"
        LC1[client_id<br/>Tenant ID]
        LC2[file_name<br/>Document Name]
        LC3[file_size<br/>Document Size]
        LC4[operation<br/>Business Operation]
        LC5[duration<br/>Processing Time]
    end
    
    subgraph "Log Export"
        LE1[Console Output<br/>Development]
        LE2[File Output<br/>Production]
        LE3[OTEL Collector<br/>Centralized]
        LE4[Log Aggregation<br/>ELK Stack]
    end
    
    LG1 --> LS1
    LG2 --> LS2
    LG3 --> LS3
    LG4 --> LS4
    LG5 --> LS5
    
    LS5 --> LC1
    LS5 --> LC2
    LS5 --> LC3
    LS5 --> LC4
    LS5 --> LC5
    
    LG5 --> LE1
    LG5 --> LE2
    LG5 --> LE3
    LG5 --> LE4
    
    style LG1 fill:#ff6b6b
    style LS1 fill:#4ecdc4
    style LC1 fill:#45b7d1
    style LE1 fill:#96ceb4
```

---

## 🧪 Development & Testing

### **Development Environment Setup**

```mermaid
graph TD
    subgraph "Local Development"
        LD1[Python 3.8+<br/>Runtime Environment]
        LD2[Poetry<br/>Dependency Management]
        LD3[Virtual Environment<br/>Isolation]
        LD4[Code Editor<br/>VS Code, PyCharm]
    end
    
    subgraph "Dependencies"
        D1[FastAPI<br/>Web Framework]
        D2[OpenTelemetry<br/>Observability]
        D3[HTTPX<br/>HTTP Client]
        D4[Pydantic<br/>Data Validation]
    end
    
    subgraph "Development Tools"
        DT1[Black<br/>Code Formatting]
        DT2[Flake8<br/>Linting]
        DT3[Pytest<br/>Testing]
        DT4[Pre-commit<br/>Git Hooks]
    end
    
    subgraph "Testing"
        T1[Unit Tests<br/>Component Testing]
        T2[Integration Tests<br/>Service Testing]
        T3[Observability Tests<br/>Telemetry Validation]
        T4[Performance Tests<br/>Load Testing]
    end
    
    LD1 --> D1
    LD2 --> D2
    LD3 --> D3
    LD4 --> D4
    
    D1 --> DT1
    D2 --> DT2
    D3 --> DT3
    D4 --> DT4
    
    DT1 --> T1
    DT2 --> T2
    DT3 --> T3
    DT4 --> T4
    
    style LD1 fill:#ff6b6b
    style D1 fill:#4ecdc4
    style DT1 fill:#45b7d1
    style T1 fill:#96ceb4
```

### **Testing Commands**

```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=.

# Run specific test categories
poetry run pytest tests/test_observability.py
poetry run pytest tests/test_health.py
poetry run pytest tests/test_upload.py

# Run performance tests
poetry run pytest tests/test_performance.py -v

# Run with observability validation
poetry run pytest --observability --verbose
```

---

## 🚀 Deployment & Configuration

### **Docker Deployment Architecture**

```mermaid
graph TD
    subgraph "Container Configuration"
        C1[Dockerfile<br/>Multi-stage Build]
        C2[Base Image<br/>Python 3.8-slim]
        C3[Dependencies<br/>Poetry Installation]
        C4[Application<br/>FastAPI App]
        C5[Health Check<br/>Readiness Probe]
    end
    
    subgraph "Environment Variables"
        EV1[OTEL_ENDPOINT<br/>Collector Address]
        EV2[ENVIRONMENT<br/>dev/staging/prod]
        EV3[LOG_LEVEL<br/>DEBUG/INFO/WARNING]
        EV4[HEALTH_CHECK_INTERVAL<br/>Check Frequency]
    end
    
    subgraph "Resource Limits"
        RL1[Memory<br/>512MB - 2GB]
        RL2[CPU<br/>0.5 - 2 cores]
        RL3[Disk<br/>1GB - 5GB]
        RL4[Network<br/>Bandwidth Limits]
    end
    
    subgraph "Health Monitoring"
        HM1[Readiness Probe<br/>Service Ready]
        HM2[Liveness Probe<br/>Service Alive]
        HM3[Startup Probe<br/>Service Started]
        HM4[Resource Monitoring<br/>CPU/Memory]
    end
    
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5
    
    C5 --> EV1
    C5 --> EV2
    C5 --> EV3
    C5 --> EV4
    
    EV1 --> RL1
    EV2 --> RL2
    EV3 --> RL3
    EV4 --> RL4
    
    RL1 --> HM1
    RL2 --> HM2
    RL3 --> HM3
    RL4 --> HM4
    
    style C1 fill:#ff6b6b
    style EV1 fill:#4ecdc4
    style RL1 fill:#45b7d1
    style HM1 fill:#96ceb4
```

### **Configuration Management**

```python
# config.py - Environment Configuration
import os
from typing import Optional

class Settings:
    # Service Configuration
    SERVICE_NAME: str = "document-api"
    SERVICE_VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    
    # Observability Configuration
    OTEL_ENDPOINT: str = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4317")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Health Check Configuration
    HEALTH_CHECK_INTERVAL: int = int(os.getenv("HEALTH_CHECK_INTERVAL", "30"))
    
    # File Upload Configuration
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", "10485760"))  # 10MB
    ALLOWED_EXTENSIONS: list = os.getenv("ALLOWED_EXTENSIONS", "txt,pdf,doc,docx").split(",")
    
    # External Service Configuration
    DATA_STORE_URL: str = os.getenv("DATA_STORE_URL", "http://data-store:8001")
    LLM_SERVICE_URL: str = os.getenv("LLM_SERVICE_URL", "http://llm-service:8002")

settings = Settings()
```

### **Health Check Configuration**

```python
# Health check endpoint with detailed component status
@app.get("/health")
async def health_check():
    """Comprehensive health check with component status."""
    
    # Check file system health
    file_system_healthy = check_file_system_health()
    
    # Check data store connectivity
    data_store_healthy = await check_data_store_health()
    
    # Determine overall status
    if file_system_healthy and data_store_healthy:
        status = "healthy"
    elif file_system_healthy or data_store_healthy:
        status = "degraded"
    else:
        status = "unhealthy"
    
    return {
        "status": status,
        "service": "document-api",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "file_system": "healthy" if file_system_healthy else "unhealthy",
            "data_store": "healthy" if data_store_healthy else "unhealthy"
        },
        "version": "1.0.0"
    }
```

---

## 🌟 Conclusion

The **Document API Service** provides a robust, observable, and scalable foundation for document management operations. With comprehensive observability features, engineers can:

- **🔍 Trace requests** from client to storage with correlation IDs
- **📊 Monitor performance** with detailed metrics and histograms
- **🐛 Debug issues** with structured logging and distributed tracing
- **🏥 Ensure reliability** with component-level health monitoring
- **📈 Scale confidently** with performance insights and capacity planning

### **Key Benefits**

1. **Complete Visibility**: End-to-end request tracing and monitoring
2. **Rapid Troubleshooting**: Correlation IDs link all related operations
3. **Proactive Monitoring**: Health checks and alerting prevent issues
4. **Performance Insights**: Detailed metrics for optimization
5. **Production Ready**: Enterprise-grade observability and monitoring

---

**Happy Document Processing! 🚀📄🔍**

*For additional support or questions about the Document API service, refer to the main project documentation or contact your development team.*
