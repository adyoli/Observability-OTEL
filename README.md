# 🚀 Robin Interview - Multi-Tenant Document Management System with Enterprise Observability

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture & Components](#architecture--components)
3. [Observability Features](#observability-features)
4. [Quick Start](#quick-start)
5. [Testing & Validation](#testing--validation)
6. [Monitoring & Troubleshooting](#monitoring--troubleshooting)
7. [API Reference](#api-reference)
8. [Production Deployment](#production-deployment)

---

## 🎯 System Overview

This project demonstrates a **multi-tenant document management system with enterprise-grade observability** built using modern microservices architecture. The system provides comprehensive visibility into application performance, database operations, and request flows, enabling engineers to rapidly troubleshoot issues and optimize system performance.

### 🌟 Key Features

- **🔍 Complete Request Visibility**: Trace requests from load balancer to database
- **📊 Real-time Performance Monitoring**: Identify bottlenecks before they impact users
- **🐛 Rapid Issue Resolution**: Correlation IDs link all related telemetry data
- **📈 Capacity Planning**: Detailed metrics for infrastructure scaling
- **🔒 Multi-tenant Isolation**: Per-client performance and usage tracking
- **🏥 Health Monitoring**: Component-level health status and alerting

---

## 🏗️ Architecture & Components

### System Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        C[Client Applications]
        LB[Load Balancer<br/>nginx]
    end
    
    subgraph "Application Layer"
        DA[Document API<br/>FastAPI + OTEL]
        DS[Data Store<br/>FastAPI + SQLAlchemy + OTEL]
    end
    
    subgraph "Data Layer"
        PG[(PostgreSQL<br/>Database)]
    end
    
    subgraph "Observability Layer"
        OC[OTEL Collector<br/>Central Hub]
        M[Monitoring<br/>Grafana/Prometheus]
        L[Logging<br/>ELK/Splunk]
        T[Tracing<br/>Jaeger/Zipkin]
    end
    
    C --> LB
    LB --> DA
    DA --> DS
    DS --> PG
    
    DA --> OC
    DS --> OC
    OC --> M
    OC --> L
    OC --> T
    
    style OC fill:#ff6b6b
    style DA fill:#4ecdc4
    style DS fill:#45b7d1
    style PG fill:#96ceb4
```

### Service Communication Flow

```mermaid
sequenceDiagram
    participant Client
    participant nginx
    participant DocumentAPI
    participant DataStore
    participant PostgreSQL
    participant OTELCollector
    
    Note over Client,OTELCollector: Document Upload Flow
    
    Client->>nginx: PUT /clients/{id}/upload-document
    nginx->>DocumentAPI: Forward request
    
    DocumentAPI->>DocumentAPI: Generate correlation ID
    DocumentAPI->>DocumentAPI: Process file upload
    DocumentAPI->>DocumentAPI: LLM summarization
    DocumentAPI->>DataStore: POST /clients/{id}/documents
    
    DataStore->>PostgreSQL: INSERT document_metadata
    PostgreSQL-->>DataStore: Document ID
    DataStore-->>DocumentAPI: Document metadata
    DocumentAPI-->>nginx: Success response
    nginx-->>Client: Document uploaded
    
    Note over DocumentAPI,OTELCollector: Telemetry Export
    DocumentAPI->>OTELCollector: Traces + Metrics + Logs
    DataStore->>OTELCollector: Traces + Metrics + Logs
    PostgreSQL->>OTELCollector: Database traces
```

### Observability Data Flow

```mermaid
flowchart LR
    subgraph "Services"
        DA[Document API]
        DS[Data Store]
    end
    
    subgraph "OTEL Collector"
        R[Receivers]
        P[Processors]
        E[Exporters]
    end
    
    subgraph "Destinations"
        M[Metrics<br/>Prometheus]
        T[Traces<br/>Jaeger]
        L[Logs<br/>ELK Stack]
    end
    
    DA -->|OTLP gRPC| R
    DS -->|OTLP gRPC| R
    
    R --> P
    P --> E
    
    E --> M
    E --> T
    E --> L
    
    style R fill:#ff6b6b
    style P fill:#4ecdc4
    style E fill:#45b7d1
```

---

## 🔍 Observability Features

### 1. **🔄 Distributed Tracing**

#### **Correlation ID System**
Every request gets a unique UUID4 correlation ID that flows through all services:

```mermaid
graph LR
    subgraph "Request Flow"
        R[Request Start]
        DA[Document API]
        DS[Data Store]
        DB[(Database)]
    end
    
    R -->|corr_id: abc-123| DA
    DA -->|corr_id: abc-123| DS
    DS -->|corr_id: abc-123| DB
    
    style R fill:#ff6b6b
    style DA fill:#4ecdc4
    style DS fill:#45b7d1
    style DB fill:#96ceb4
```

#### **Span Hierarchy**
Detailed tracing of document upload flow:

```mermaid
graph TD
    Root[upload_document<br/>corr_id: abc-123]
    
    Root --> FileProc[file_processing<br/>file_size, file_type]
    Root --> LLM[llm_summarization<br/>processing_time]
    Root --> Store[store_metadata<br/>database_operation]
    
    FileProc --> FileRead[file_read<br/>content_processing]
    FileProc --> FileSave[file_save<br/>temporary_storage]
    
    Store --> DBConn[database_connection<br/>connection_pool]
    Store --> SQLExec[sql_execution<br/>query_timing]
    Store --> Commit[transaction_commit<br/>success_status]
    
    style Root fill:#ff6b6b
    style FileProc fill:#4ecdc4
    style LLM fill:#45b7d1
    style Store fill:#96ceb4
```

### 2. **📊 Metrics Collection**

#### **HTTP Request Metrics**
```mermaid
graph LR
    subgraph "Metrics Collected"
        RC[http_requests_total<br/>method, path, status]
        RD[http_request_duration_seconds<br/>histogram]
        EC[http_errors_total<br/>error rates]
    end
    
    subgraph "Dimensions"
        M[HTTP Method]
        P[Request Path]
        S[Status Code]
        C[Correlation ID]
    end
    
    RC --> M
    RC --> P
    RC --> S
    RC --> C
    
    RD --> M
    RD --> P
    RD --> C
    
    EC --> M
    EC --> P
    EC --> S
    EC --> C
```

#### **Database Operation Metrics**
```mermaid
graph LR
    subgraph "Database Metrics"
        DOC[database_operations_total<br/>operation, table, success]
        DOD[database_operation_duration_seconds<br/>performance]
        DCP[database_connection_pool<br/>usage, health]
    end
    
    subgraph "Operation Types"
        INS[INSERT]
        SEL[SELECT]
        UPD[UPDATE]
        DEL[DELETE]
    end
    
    subgraph "Tables"
        DM[document_metadata]
        US[users]
        CL[clients]
    end
    
    DOC --> INS
    DOC --> SEL
    DOC --> UPD
    DOC --> DEL
    
    DOC --> DM
    DOC --> US
    DOC --> CL
```

### 3. **📝 Structured Logging**

#### **Log Structure**
```mermaid
graph TD
    subgraph "Log Entry Structure"
        CID[correlation_id<br/>abc-123-def]
        MSG[log_message<br/>&quot;Document uploaded&quot;]
        SVC[service<br/>document-api]
        CTX[context_data<br/>client_id, file_size]
        TS[timestamp<br/>unix timestamp]
    end
    
    subgraph "Log Levels"
        D[DEBUG<br/>SQL queries, details]
        I[INFO<br/>Normal operations]
        W[WARNING<br/>Slow operations]
        E[ERROR<br/>Failed operations]
        C[CRITICAL<br/>Service failures]
    end
    
    CID --> MSG
    MSG --> SVC
    SVC --> CTX
    CTX --> TS
    
    MSG --> D
    MSG --> I
    MSG --> W
    MSG --> E
    MSG --> C
```

### 4. **🏥 Enhanced Health Checks**

#### **Health Check Architecture**
```mermaid
graph TD
    subgraph "Health Check Components"
        FS[File System<br/>uploads directory]
        DB[Database<br/>connectivity, tables]
        EXT[External Services<br/>dependencies]
    end
    
    subgraph "Health Status"
        H[Healthy<br/>all components OK]
        D[Degraded<br/>partial functionality]
        U[Unhealthy<br/>critical failures]
    end
    
    subgraph "Metrics"
        HC[health_check_total<br/>status counts]
        HD[health_check_duration_seconds<br/>response time]
    end
    
    FS --> H
    DB --> H
    EXT --> H
    
    FS --> D
    DB --> D
    EXT --> D
    
    FS --> U
    DB --> U
    EXT --> U
    
    H --> HC
    D --> HC
    U --> HC
    
    H --> HD
    D --> HD
    U --> HD
```

---

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for local development)
- Poetry (for dependency management)

### 1. **Clone and Setup**

```bash
git clone <repository-url>
cd sre-observability-interview
```

### 2. **Start All Services**

```bash
# Start the complete system
./setup-and-run.sh

# Or manually with Docker Compose
docker-compose up -d
```

### 3. **Verify System Health**

```bash
# Check all services are running
docker-compose ps

# Test health endpoints
curl http://localhost/health
curl http://localhost:8001/health
```

### 4. **Test Observability**

```bash
# Run comprehensive observability tests
python test_observability.py --all --verbose

# Test specific features
python test_observability.py --health
python test_observability.py --upload
python test_observability.py --performance
```

---

## 🧪 Testing & Validation

### **Comprehensive Test Suite**

The system includes a complete test suite that validates all observability features:

```mermaid
graph TD
    subgraph "Test Categories"
        HC[Health Checks<br/>Service availability]
        UP[Document Upload<br/>Complete flow testing]
        RT[Document Retrieval<br/>Database operations]
        ER[Error Scenarios<br/>Error handling]
        PF[Performance Testing<br/>Load testing]
    end
    
    subgraph "Test Execution"
        T1[Test 1: Health]
        T2[Test 2: Upload]
        T3[Test 3: Retrieval]
        T4[Test 4: Errors]
        T5[Test 5: Performance]
    end
    
    subgraph "Validation"
        V1[Service Health]
        V2[Correlation IDs]
        V3[Database Tracing]
        V4[Error Metrics]
        V5[Performance Metrics]
    end
    
    HC --> T1
    UP --> T2
    RT --> T3
    ER --> T4
    PF --> T5
    
    T1 --> V1
    T2 --> V2
    T3 --> V3
    T4 --> V4
    T5 --> V5
```

### **Test Commands**

```bash
# Run all tests with verbose output
python test_observability.py --all --verbose

# Test specific functionality
python test_observability.py --upload --clients 5 --files 3
python test_observability.py --performance --load-factor 3

# Health check testing only
python test_observability.py --health
```

---

## 📊 Monitoring & Troubleshooting

### **Key Metrics to Monitor**

#### **Request Performance**
```mermaid
graph LR
    subgraph "Performance Metrics"
        RPS["Requests per Second<br/>rate(http_requests_total[5m])"]
        P95["95th Percentile<br/>histogram_quantile(0.95, ...)"]
        ERR["Error Rate<br/>rate(http_errors_total[5m])"]
    end
    
    subgraph "Alerting Thresholds"
        T1["High Error Rate<br/>> 10%"]
        T2["Slow Response<br/>> 2s P95"]
        T3["Low Throughput<br/>< 100 RPS"]
    end
    
    RPS --> T3
    P95 --> T2
    ERR --> T1
```

#### **Database Performance**
```mermaid
graph LR
    subgraph "Database Metrics"
        QPS["Queries per Second<br/>rate(database_operations_total[5m])"]
        Q95["Query P95<br/>histogram_quantile(0.95, ...)"]
        CONN[Connection Pool<br/>pool_usage, pool_health]
    end
    
    subgraph "Database Alerts"
        A1["Slow Queries<br/>> 1s P95"]
        A2["High Error Rate<br/>> 5%"]
        A3[Connection Issues<br/>pool_exhausted]
    end
    
    QPS --> A3
    Q95 --> A1
    CONN --> A2
```

### **Troubleshooting Guide**

#### **Common Issues and Solutions**

```mermaid
graph TD
    subgraph "Common Issues"
        I1[Correlation ID Missing]
        I2[OTEL Collector Down]
        I3[Database Tracing Not Working]
        I4[High Memory Usage]
    end
    
    subgraph "Root Causes"
        C1[Middleware Not Added]
        C2[Network Issues]
        C3[SQLAlchemy Not Instrumented]
        C4[Memory Limits Too Low]
    end
    
    subgraph "Solutions"
        S1[Add ObservabilityMiddleware]
        S2[Check Collector Status]
        S3[Enable SQLAlchemy Instrumentation]
        S4[Increase Memory Limits]
    end
    
    I1 --> C1
    I2 --> C2
    I3 --> C3
    I4 --> C4
    
    C1 --> S1
    C2 --> S2
    C3 --> S3
    C4 --> S4
```

#### **Debugging Commands**

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs document-api --tail=50
docker-compose logs data-store --tail=50
docker-compose logs otel-collector --tail=50

# Test individual components
curl http://localhost/health
curl http://localhost:8001/health

# Check OTEL collector telemetry
docker-compose logs otel-collector | grep "correlation_id"
```

---

## 🔌 API Reference

### **Service Endpoints**

#### **Document API (Port 80)**
```mermaid
graph TD
    subgraph "Document API Endpoints"
        H1["GET /health<br/>Health check with component status"]
        U1["PUT /clients/{id}/upload-document<br/>Document upload with tracing"]
        R1["GET /clients/{id}/documents/{doc_id}<br/>Document retrieval"]
    end
    
    subgraph "Health Check Response"
        RESP1[status: healthy/degraded/unhealthy]
        RESP2[components: file_system, data_store]
        RESP3[timestamp, version]
    end
    
    H1 --> RESP1
    H1 --> RESP2
    H1 --> RESP3
```

#### **Data Store API (Port 8001)**
```mermaid
graph TD
    subgraph "Data Store Endpoints"
        H2[GET /health<br/>Database health with latency]
        C1[POST /clients/{id}/documents<br/>Create document metadata]
        G1[GET /clients/{id}/documents/{doc_id}<br/>Get document metadata]
    end
    
    subgraph "Health Check Response"
        R4[status: healthy/degraded/unhealthy]
        R5[database: status, latency_ms]
        R6[tables: status]
    end
    
    H2 --> R4
    H2 --> R5
    H2 --> R6
```

### **Request/Response Examples**

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
  "version": "1.0.0"
}
```

---

## 🚀 Production Deployment

### **Environment Configuration**

#### **Production Environment Variables**
```bash
# Service Configuration
OTEL_SERVICE_NAME=document-api
OTEL_SERVICE_VERSION=1.0.0
ENVIRONMENT=production

# Collector Configuration
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-collector:4317
OTEL_EXPORTER_OTLP_INSECURE=false

# Database Configuration
DATABASE_URL=postgresql://user:pass@db:5432/documents
```

#### **Security Considerations**
```mermaid
graph TD
    subgraph "Security Measures"
        S1[TLS Encryption<br/>OTLP over HTTPS]
        S2[Authentication<br/>API Keys, JWT]
        S3[Authorization<br/>Role-based access]
        S4[Data Sanitization<br/>PII filtering]
    end
    
    subgraph "Network Security"
        N1[Firewall Rules<br/>Port restrictions]
        N2[VPN Access<br/>Secure connectivity]
        N3[Load Balancer<br/>SSL termination]
    end
    
    S1 --> N1
    S2 --> N2
    S3 --> N3
    S4 --> N1
```

### **Scaling Considerations**

#### **Horizontal Scaling**
```mermaid
graph TD
    subgraph "Scalable Architecture"
        LB[Load Balancer<br/>nginx + HAProxy]
        DA1[Document API<br/>Instance 1]
        DA2[Document API<br/>Instance 2]
        DA3[Document API<br/>Instance N]
        DS1[Data Store<br/>Instance 1]
        DS2[Data Store<br/>Instance 2]
        OC1[OTEL Collector<br/>Instance 1]
        OC2[OTEL Collector<br/>Instance 2]
    end
    
    LB --> DA1
    LB --> DA2
    LB --> DA3
    
    DA1 --> DS1
    DA2 --> DS2
    DA3 --> DS1
    
    DA1 --> OC1
    DA2 --> OC2
    DA3 --> OC1
```

#### **Monitoring and Alerting**
```mermaid
graph TD
    subgraph "Monitoring Stack"
        P[Prometheus<br/>Metrics collection]
        G[Grafana<br/>Dashboards & alerts]
        A[AlertManager<br/>Alert routing]
    end
    
    subgraph "Alerting Rules"
        R1[High Error Rate<br/>> 5%]
        R2[Slow Response<br/>> 1s P95]
        R3[Service Down<br/>health check failed]
        R4[High Memory<br/>> 80% usage]
    end
    
    subgraph "Notification Channels"
        N1[Slack<br/>Team notifications]
        N2[Email<br/>Escalation alerts]
        N3[PagerDuty<br/>On-call alerts]
    end
    
    P --> G
    G --> A
    A --> R1
    A --> R2
    A --> R3
    A --> R4
    
    R1 --> N1
    R2 --> N1
    R3 --> N2
    R4 --> N3
```

---

## 📚 Additional Documentation

- **[Observability Dashboard](./observability-dashboard.md)** - Comprehensive observability setup and usage
- **[Test Script](./test_observability.py)** - Complete testing suite for all observability features
- **[Docker Configuration](./docker-compose.yml)** - Service orchestration and networking
- **[OTEL Collector Config](./otel-collector-config.yaml)** - Telemetry collection and processing

---

## 🎯 What Engineers Can Now Do

### **Immediate Capabilities**
- **🔍 Trace requests** across all services using correlation IDs
- **📊 Monitor performance** with detailed metrics and histograms
- **🐛 Debug issues** with comprehensive logging and spans
- **🏥 Check service health** with detailed component status
- **📈 Analyze trends** with historical performance data

### **Advanced Observability**
- **📊 Create dashboards** for business and technical metrics
- **🚨 Set up alerting** for proactive issue detection
- **🔍 Investigate incidents** with full request context
- **📈 Plan capacity** based on performance trends
- **🔒 Monitor security** with access and error tracking

---

## 🌟 Conclusion

This observability implementation provides engineers with **comprehensive visibility** into the multi-tenant document management system, enabling:

- **Faster troubleshooting** with correlation IDs and distributed tracing
- **Proactive monitoring** with health checks and performance metrics
- **Better understanding** of system behavior and performance patterns
- **Confident scaling** with detailed capacity and performance data
- **Rapid incident response** with complete request context and error tracking

The system is **production-ready** with proper security, scalability, and monitoring considerations. Start with the basic setup and gradually add more sophisticated monitoring and alerting as your needs grow.

---

**Happy Observing! 🚀📊🔍**

*For additional support or questions about the observability system, refer to the detailed documentation or contact your observability team.*
