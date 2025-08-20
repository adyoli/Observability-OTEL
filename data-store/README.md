# 🗄️ Data Store Service - Comprehensive Documentation

## 📋 Table of Contents

1. [Service Overview](#service-overview)
2. [Architecture & Components](#architecture--components)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Observability Features](#observability-features)
6. [Database Operations](#database-operations)
7. [Development & Testing](#development--testing)
8. [Deployment & Configuration](#deployment--configuration)

---

## 🎯 Service Overview

The **Data Store Service** is a FastAPI-based microservice that manages document metadata and provides database operations for the multi-tenant document management system. It features comprehensive observability with SQLAlchemy instrumentation, distributed tracing, and detailed database performance monitoring.

### 🌟 Key Features

- **🗄️ Database Management**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **🔍 Complete Observability**: Database operation tracing, metrics, and performance monitoring
- **🔒 Multi-tenant Isolation**: Client-based data separation and access control
- **🏥 Health Monitoring**: Database connectivity, table status, and performance checks
- **📊 Performance Tracking**: Query timing, connection pool monitoring, and transaction metrics
- **🔄 Correlation ID System**: End-to-end request tracing including database operations

---

## 🏗️ Architecture & Components

### Service Architecture Diagram

```mermaid
graph TB
    subgraph "Client Layer"
        DA[Document API Service<br/>Port 8000]
        C[Client Applications]
    end
    
    subgraph "Data Store Service"
        API[FastAPI Application<br/>Port 8001]
        MW[ObservabilityMiddleware<br/>Correlation IDs]
        DBH[Database Handler<br/>SQLAlchemy ORM]
        HC[Health Checker<br/>Database Status]
        MIG[Alembic Migrations<br/>Schema Management]
    end
    
    subgraph "Database Layer"
        PG[(PostgreSQL<br/>Port 5432)]
        CP[Connection Pool<br/>Connection Management]
        SC[Schema<br/>Tables & Indexes]
        TX[Transactions<br/>ACID Operations]
    end
    
    subgraph "Observability Layer"
        OTEL[OpenTelemetry<br/>Tracing & Metrics]
        SQL[Metrics Collection<br/>Database Performance]
        LOG[Structured Logging<br/>Query Logging]
        TRC[Trace Collection<br/>Operation Tracing]
    end
    
    DA --> API
    C --> API
    
    API --> MW
    MW --> DBH
    MW --> HC
    MW --> MIG
    
    DBH --> PG
    DBH --> CP
    DBH --> SC
    DBH --> TX
    
    API --> OTEL
    API --> SQL
    API --> LOG
    API --> TRC
    
    style API fill:#ff6b6b
    style MW fill:#4ecdc4
    style PG fill:#45b7d1
    style OTEL fill:#96ceb4
```

### Database Operation Flow

```mermaid
sequenceDiagram
    participant DocumentAPI
    participant DataStore
    participant Middleware
    participant DatabaseHandler
    participant PostgreSQL
    participant OTELCollector
    
    Note over DocumentAPI,OTELCollector: Document Metadata Storage Flow
    
    DocumentAPI->>DataStore: POST /clients/{id}/documents
    
    DataStore->>Middleware: Process request
    Middleware->>Middleware: Generate correlation ID
    Middleware->>Middleware: Log request start
    
    Middleware->>DatabaseHandler: Store document metadata
    
    DatabaseHandler->>DatabaseHandler: Create database connection
    DatabaseHandler->>DatabaseHandler: Begin transaction
    
    DatabaseHandler->>PostgreSQL: INSERT INTO document_metadata
    PostgreSQL-->>DatabaseHandler: Document ID
    
    DatabaseHandler->>DatabaseHandler: Commit transaction
    DatabaseHandler->>DatabaseHandler: Close connection
    
    DatabaseHandler-->>Middleware: Metadata stored
    Middleware->>Middleware: Log operation completion
    
    Middleware-->>DataStore: Success response
    DataStore-->>DocumentAPI: Document metadata
    
    Note over DataStore,OTELCollector: Telemetry Export
    DataStore->>OTELCollector: Database traces + metrics
    PostgreSQL->>OTELCollector: Query performance data
```

### Component Interaction Diagram

```mermaid
graph LR
    subgraph "Core Components"
        C1[FastAPI App<br/>Main Application]
        C2[ObservabilityMiddleware<br/>Request Tracking]
        C3[Database Handler<br/>SQLAlchemy ORM]
        C4[Health Checker<br/>Database Monitoring]
        C5[Migration Manager<br/>Alembic]
    end
    
    subgraph "Database Layer"
        D1[Connection Pool<br/>Connection Management]
        D2[Transaction Manager<br/>ACID Operations]
        D3[Query Builder<br/>SQL Generation]
        D4[Result Processor<br/>Data Mapping]
    end
    
    subgraph "Supporting Modules"
        S1[Telemetry<br/>OTEL Configuration]
        S2[Observability<br/>Database Utilities]
        S3[Models<br/>SQLAlchemy Models]
        S4[Schemas<br/>Pydantic Validation]
    end
    
    subgraph "External Dependencies"
        E1[PostgreSQL<br/>Database Engine]
        E2[OTEL Collector<br/>Telemetry Hub]
        E3[Document API<br/>Client Service]
        E4[File System<br/>Document Storage]
    end
    
    C1 --> C2
    C1 --> C3
    C1 --> C4
    C1 --> C5
    
    C3 --> D1
    C3 --> D2
    C3 --> D3
    C3 --> D4
    
    C3 --> S1
    C4 --> S2
    C5 --> S3
    C3 --> S4
    
    D1 --> E1
    S1 --> E2
    C1 --> E3
    C4 --> E4
    
    style C1 fill:#ff6b6b
    style C3 fill:#4ecdc4
    style D1 fill:#45b7d1
    style E1 fill:#96ceb4
```

---

## 🗄️ Database Schema

### **Database Schema Overview**

```mermaid
erDiagram
    document_metadata {
        int id PK
        string client_id FK
        string filename
        int file_size
        string file_type
        string content_type
        timestamp upload_timestamp
        string file_path
        string summary
        json metadata
    }
    
    clients {
        string id PK
        string name
        string email
        timestamp created_at
        timestamp updated_at
        string status
    }
    
    users {
        int id PK
        string username
        string email
        string password_hash
        timestamp created_at
        timestamp last_login
        string role
    }
    
    document_metadata ||--o{ clients : "belongs_to"
    document_metadata ||--o{ users : "uploaded_by"
    clients ||--o{ users : "has_users"
```

### **Table Structure Details**

```mermaid
graph TD
    subgraph "Core Tables"
        T1["document_metadata<br/>Document Information"]
        T2["clients<br/>Client Management"]
        T3["users<br/>User Accounts"]
    end
    
    subgraph "document_metadata Fields"
        direction LR
        subgraph "Fields 1-5"
            F1["id: SERIAL PRIMARY KEY"]
            F2["client_id: VARCHAR(255)"]
            F3["filename: VARCHAR(500)"]
            F4["file_size: BIGINT"]
            F5["file_type: VARCHAR(100)"]
        end
        subgraph "Fields 6-9"
            F6["upload_timestamp: TIMESTAMP"]
            F7["file_path: VARCHAR(1000)"]
            F8["summary: TEXT"]
            F9["metadata: JSONB"]
        end
    end
    
    subgraph "Indexes & Constraints"
        I1["PRIMARY KEY: id"]
        I2["INDEX: client_id"]
        I3["INDEX: upload_timestamp"]
        I4["FOREIGN KEY: client_id -> clients.id"]
        I5["UNIQUE: client_id + filename"]
    end
    
    T1 --> F1
    T1 --> F2
    T1 --> F3
    T1 --> F4
    T1 --> F5
    T1 --> F6
    T1 --> F7
    T1 --> F8
    T1 --> F9
    
    T1 --> I1
    T1 --> I2
    T1 --> I3
    T1 --> I4
    T1 --> I5
    
    style T1 fill:#ff6b6b
    style F1 fill:#4ecdc4
    style I1 fill:#45b7d1
```

### **Migration History**

```mermaid
graph LR
    subgraph "Migration Timeline"
        M1[001_initial<br/>Base Schema]
        M2[002_add_client_id<br/>Client Isolation]
        M3[003_add_metadata<br/>JSON Metadata]
        M4[004_add_indexes<br/>Performance]
    end
    
    subgraph "Migration Types"
        MT1[Schema Changes<br/>Table Creation]
        MT2[Data Changes<br/>Data Migration]
        MT3[Index Changes<br/>Performance]
        MT4[Constraint Changes<br/>Data Integrity]
    end
    
    subgraph "Migration Status"
        MS1[Applied<br/>Successfully Applied]
        MS2[Pending<br/>Ready to Apply]
        MS3[Failed<br/>Rollback Required]
        MS4[Rolled Back<br/>Previous State]
    end
    
    M1 --> MT1
    M2 --> MT2
    M3 --> MT3
    M4 --> MT4
    
    MT1 --> MS1
    MT2 --> MS2
    MT3 --> MS3
    MT4 --> MS4
    
    style M1 fill:#ff6b6b
    style MT1 fill:#4ecdc4
    style MS1 fill:#45b7d1
```

---

## 🔌 API Endpoints

### **Endpoint Overview**

```mermaid
graph TD
    subgraph "API Endpoints"
        E1["GET /health<br/>Health Check"]
        E2["POST /clients/{id}/documents<br/>Create Document"]
        E3["GET /clients/{id}/documents/{doc_id}<br/>Get Document"]
        E4["GET /clients/{id}/documents<br/>List Documents"]
    end
    
    subgraph "Health Check Response"
        H1[status: healthy/degraded/unhealthy]
        H2[database: status, latency_ms]
        H3[tables: status, count]
        H4[version, timestamp]
    end
    
    subgraph "Document Operations"
        DO1[Create: INSERT metadata]
        DO2[Read: SELECT by ID]
        DO3[List: SELECT with filters]
        DO4[Update: UPDATE metadata]
        DO5[Delete: DELETE record]
    end
    
    subgraph "Response Structure"
        RS1[success: boolean]
        RS2[data: document object]
        RS3[message: status message]
        RS4[correlation_id: request ID]
    end
    
    E1 --> H1
    E1 --> H2
    E1 --> H3
    E1 --> H4
    
    E2 --> DO1
    E3 --> DO2
    E4 --> DO3
    
    DO1 --> RS1
    DO1 --> RS2
    DO1 --> RS3
    DO1 --> RS4

    DO2 --> RS1
    DO2 --> RS2
    DO2 --> RS3
    DO2 --> RS4
    
    DO3 --> RS1
    DO3 --> RS2
    DO3 --> RS3
    DO3 --> RS4

    style E1 fill:#ff6b6b
    style DO1 fill:#4ecdc4
    style RS1 fill:#45b7d1
```

### **Request/Response Examples**

#### **Health Check**
```bash
curl http://localhost:8001/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "data-store",
  "timestamp": "2025-08-20T08:13:49.822329",
  "database": {
    "status": "healthy",
    "latency_ms": 12.5,
    "connection_pool": {
      "active": 2,
      "idle": 8,
      "total": 10
    }
  },
  "tables": {
    "document_metadata": "healthy",
    "clients": "healthy",
    "users": "healthy"
  },
  "version": "1.0.0"
}
```

#### **Create Document Metadata**
```bash
curl -X POST http://localhost:8001/clients/test-client-123/documents \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test_file.txt",
    "file_size": 50,
    "file_type": "text/plain",
    "file_path": "/uploads/test_file.txt"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 5,
    "client_id": "test-client-123",
    "filename": "test_file.txt",
    "file_size": 50,
    "file_type": "text/plain",
    "upload_timestamp": "2025-08-20T08:10:48.108442Z",
    "file_path": "/uploads/test_file.txt"
  },
  "message": "Document metadata created successfully",
  "correlation_id": "abc-123-def"
}
```

---

## 🔍 Observability Features

### **Database Operation Tracing**

```mermaid
graph TD
    subgraph "Database Operation Flow"
        DO1[SQL Query Start<br/>Correlation ID]
        DO2[Connection Acquisition<br/>Pool Management]
        DO3[Query Execution<br/>SQL Processing]
        DO4[Result Processing<br/>Data Mapping]
        DO5[Transaction Commit<br/>ACID Operations]
        DO6[Connection Release<br/>Pool Return]
    end
    
    subgraph "Trace Attributes"
        TA1[correlation_id<br/>Request Identifier]
        TA2[operation_type<br/>SELECT, INSERT, UPDATE, DELETE]
        TA3[table_name<br/>Target Table]
        TA4[query_duration<br/>Execution Time]
        TA5[rows_affected<br/>Result Count]
        TA6[connection_id<br/>Database Connection]
    end
    
    subgraph "Performance Metrics"
        PM1[query_duration_seconds<br/>Execution Time]
        PM2[connection_pool_usage<br/>Pool Utilization]
        PM3[transaction_duration<br/>Transaction Time]
        PM4[rows_processed<br/>Data Volume]
    end
    
    DO1 --> DO2
    DO2 --> DO3
    DO3 --> DO4
    DO4 --> DO5
    DO5 --> DO6
    
    DO1 --> TA1
    DO2 --> TA2
    DO3 --> TA3
    DO4 --> TA4
    DO5 --> TA5
    DO6 --> TA6
    
    DO3 --> PM1
    DO2 --> PM2
    DO5 --> PM3
    DO4 --> PM4
    
    style DO1 fill:#ff6b6b
    style TA1 fill:#4ecdc4
    style PM1 fill:#45b7d1
```

### **Database Metrics Collection**

```mermaid
graph LR
    subgraph "Database Metrics"
        DM1[database_operations_total<br/>Operation Count]
        DM2[database_operation_duration_seconds<br/>Performance]
        DM3[database_connection_pool<br/>Pool Status]
        DM4[database_transactions<br/>Transaction Count]
    end
    
    subgraph "Operation Types"
        OT1[SELECT<br/>Read Operations]
        OT2[INSERT<br/>Create Operations]
        OT3[UPDATE<br/>Modify Operations]
        OT4[DELETE<br/>Remove Operations]
    end
    
    subgraph "Table Metrics"
        TM1[document_metadata<br/>Document Operations]
        TM2[clients<br/>Client Operations]
        TM3[users<br/>User Operations]
        TM4[system_tables<br/>System Operations]
    end
    
    subgraph "Performance Dimensions"
        PD1[operation_type<br/>SQL Operation]
        PD2[table_name<br/>Target Table]
        PD3[client_id<br/>Tenant Identifier]
        PD4[success_status<br/>Success/Failure]
        PD5[correlation_id<br/>Request Link]
    end
    
    DM1 --> OT1
    DM2 --> OT2
    DM3 --> OT3
    DM4 --> OT4
    
    OT1 --> TM1
    OT2 --> TM2
    OT3 --> TM3
    OT4 --> TM4
    
    TM1 --> PD1
    TM2 --> PD2
    TM3 --> PD3
    TM4 --> PD4
    
    PD1 --> PD5
    PD2 --> PD5
    PD3 --> PD5
    PD4 --> PD5
    
    style DM1 fill:#ff6b6b
    style OT1 fill:#4ecdc4
    style TM1 fill:#45b7d1
    style PD1 fill:#96ceb4
```

### **Connection Pool Monitoring**

```mermaid
flowchart TD
    subgraph "Connection Pool States"
        PS1[Available<br/>Idle Connections]
        PS2[Active<br/>In-Use Connections]
        PS3[Creating<br/>New Connections]
        PS4[Closing<br/>Terminating Connections]
        PS5[Failed<br/>Broken Connections]
    end
    
    subgraph "Pool Metrics"
        PM1[pool_size_total<br/>Total Connections]
        PM2[pool_size_active<br/>Active Connections]
        PM3[pool_size_idle<br/>Idle Connections]
        PM4[pool_wait_time<br/>Connection Wait Time]
        PM5[pool_acquire_time<br/>Acquisition Time]
    end
    
    subgraph "Pool Alerts"
        PA1[High Utilization<br/>> 80% active]
        PA2[Long Wait Times<br/>> 1s wait]
        PA3[Connection Failures<br/>> 5% failure rate]
        PA4[Pool Exhaustion<br/>No available connections]
    end
    
    PS1 --> PM1
    PS2 --> PM2
    PS3 --> PM3
    PS4 --> PM4
    PS5 --> PM5
    
    PM2 --> PA1
    PM4 --> PA2
    PM5 --> PA3
    PM1 --> PA4
    
    style PS1 fill:#ff6b6b
    style PM1 fill:#4ecdc4
    style PA1 fill:#45b7d1
```

---

## 🗄️ Database Operations

### **CRUD Operations Flow**

```mermaid
graph TD
    subgraph "Create Operation"
        C1[Validate Input<br/>Pydantic Schema]
        C2[Acquire Connection<br/>Connection Pool]
        C3[Begin Transaction<br/>ACID Start]
        C4[Execute INSERT<br/>SQL Query]
        C5[Commit Transaction<br/>ACID Commit]
        C6[Release Connection<br/>Pool Return]
    end
    
    subgraph "Read Operation"
        R1[Parse Query<br/>Parameters]
        R2[Acquire Connection<br/>Connection Pool]
        R3[Execute SELECT<br/>SQL Query]
        R4[Process Results<br/>Data Mapping]
        R5[Release Connection<br/>Pool Return]
    end
    
    subgraph "Update Operation"
        U1[Validate Changes<br/>Business Rules]
        U2[Acquire Connection<br/>Connection Pool]
        U3[Begin Transaction<br/>ACID Start]
        U4[Execute UPDATE<br/>SQL Query]
        U5[Commit Transaction<br/>ACID Commit]
        U6[Release Connection<br/>Pool Return]
    end
    
    subgraph "Delete Operation"
        D1[Check Dependencies<br/>Referential Integrity]
        D2[Acquire Connection<br/>Connection Pool]
        D3[Begin Transaction<br/>ACID Start]
        D4[Execute DELETE<br/>SQL Query]
        D5[Commit Transaction<br/>ACID Commit]
        D6[Release Connection<br/>Pool Return]
    end
    
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5
    C5 --> C6
    
    R1 --> R2
    R2 --> R3
    R3 --> R4
    R4 --> R5
    
    U1 --> U2
    U2 --> U3
    U3 --> U4
    U4 --> U5
    U5 --> U6
    
    D1 --> D2
    D2 --> D3
    D3 --> D4
    D4 --> D5
    D5 --> D6
    
    style C1 fill:#ff6b6b
    style R1 fill:#4ecdc4
    style U1 fill:#45b7d1
    style D1 fill:#96ceb4
```

### **Transaction Management**

```mermaid
graph LR
    subgraph "Transaction States"
        TS1[Not Started<br/>No Transaction]
        TS2[Started<br/>Transaction Active]
        TS3[Committed<br/>Changes Saved]
        TS4[Rolled Back<br/>Changes Undone]
        TS5[Failed<br/>Error Occurred]
    end
    
    subgraph "Transaction Operations"
        TO1[BEGIN<br/>Start Transaction]
        TO2[COMMIT<br/>Save Changes]
        TO3[ROLLBACK<br/>Undo Changes]
        TO4[SAVEPOINT<br/>Checkpoint]
        TO5[ROLLBACK TO<br/>Return to Checkpoint]
    end
    
    subgraph "Transaction Properties"
        TP1[Atomicity<br/>All or Nothing]
        TP2[Consistency<br/>Valid State]
        TP3[Isolation<br/>Concurrent Access]
        TP4[Durability<br/>Permanent Changes]
    end
    
    TS1 --> TO1
    TO1 --> TS2
    TS2 --> TO2
    TO2 --> TS3
    
    TS2 --> TO3
    TO3 --> TS4
    
    TS2 --> TO4
    TO4 --> TS2
    
    TO4 --> TO5
    TO5 --> TS2
    
    TS2 --> TP1
    TS2 --> TP2
    TS2 --> TP3
    TS2 --> TP4
    
    style TS1 fill:#ff6b6b
    style TO1 fill:#4ecdc4
    style TP1 fill:#45b7d1
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
    
    subgraph "Database Dependencies"
        DD1[PostgreSQL<br/>Database Engine]
        DD2[SQLAlchemy<br/>ORM Framework]
        DD3[Alembic<br/>Migration Tool]
        DD4[psycopg2<br/>PostgreSQL Driver]
    end
    
    subgraph "Development Tools"
        DT1[Black<br/>Code Formatting]
        DT2[Flake8<br/>Linting]
        DT3[Pytest<br/>Testing]
        DT4[Pre-commit<br/>Git Hooks]
    end
    
    subgraph "Testing"
        T1[Unit Tests<br/>Component Testing]
        T2[Integration Tests<br/>Database Testing]
        T3[Observability Tests<br/>Telemetry Validation]
        T4[Performance Tests<br/>Query Performance]
    end
    
    LD1 --> DD1
    LD2 --> DD2
    LD3 --> DD3
    LD4 --> DD4
    
    DD1 --> DT1
    DD2 --> DT2
    DD3 --> DT3
    DD4 --> DT4
    
    DT1 --> T1
    DT2 --> T2
    DT3 --> T3
    DT4 --> T4
    
    style LD1 fill:#ff6b6b
    style DD1 fill:#4ecdc4
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
poetry run pytest tests/test_database.py
poetry run pytest tests/test_observability.py
poetry run pytest tests/test_health.py

# Run database tests
poetry run pytest tests/test_models.py -v

# Run with observability validation
poetry run pytest --observability --verbose

# Run migration tests
poetry run pytest tests/test_migrations.py
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
        C5[Health Check<br/>Database Readiness]
    end
    
    subgraph "Environment Variables"
        EV1[DATABASE_URL<br/>PostgreSQL Connection]
        EV2[OTEL_ENDPOINT<br/>Collector Address]
        EV3[ENVIRONMENT<br/>dev/staging/prod]
        EV4[LOG_LEVEL<br/>DEBUG/INFO/WARNING]
        EV5[DB_POOL_SIZE<br/>Connection Pool Size]
    end
    
    subgraph "Resource Limits"
        RL1[Memory<br/>1GB - 4GB]
        RL2[CPU<br/>1 - 4 cores]
        RL3[Disk<br/>2GB - 10GB]
        RL4[Network<br/>Bandwidth Limits]
    end
    
    subgraph "Health Monitoring"
        HM1[Readiness Probe<br/>Database Ready]
        HM2[Liveness Probe<br/>Service Alive]
        HM3[Startup Probe<br/>Service Started]
        HM4[Resource Monitoring<br/>CPU/Memory/DB]
    end
    
    C1 --> C2
    C2 --> C3
    C3 --> C4
    C4 --> C5
    
    C5 --> EV1
    C5 --> EV2
    C5 --> EV3
    C5 --> EV4
    C5 --> EV5
    
    EV1 --> RL1
    EV2 --> RL2
    EV3 --> RL3
    EV4 --> RL4
    EV5 --> RL4
    
    RL1 --> HM1
    RL2 --> HM2
    RL3 --> HM3
    RL4 --> HM4
    
    style C1 fill:#ff6b6b
    style EV1 fill:#4ecdc4
    style RL1 fill:#45b7d1
    style HM1 fill:#96ceb4
```

### **Database Configuration**

```python
# database.py - Database Configuration
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database connection configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/documents")

# Engine configuration with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
    max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
    echo=os.getenv("DB_ECHO", "false").lower() == "true"
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### **Migration Configuration**

```ini
# alembic.ini - Migration Configuration
[alembic]
script_location = alembic
sqlalchemy.url = postgresql://user:pass@localhost:5432/documents

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

---

## 🌟 Conclusion

The **Data Store Service** provides a robust, observable, and scalable foundation for database operations in the multi-tenant document management system. With comprehensive observability features, engineers can:

- **🔍 Trace database operations** with correlation IDs and detailed spans
- **📊 Monitor performance** with query timing and connection pool metrics
- **🐛 Debug issues** with structured logging and transaction tracing
- **🏥 Ensure reliability** with database health monitoring and connection management
- **📈 Scale confidently** with performance insights and capacity planning

### **Key Benefits**

1. **Complete Database Visibility**: End-to-end operation tracing and monitoring
2. **Rapid Troubleshooting**: Correlation IDs link all database operations
3. **Proactive Monitoring**: Health checks and alerting prevent database issues
4. **Performance Insights**: Detailed metrics for query optimization
5. **Production Ready**: Enterprise-grade observability and monitoring

---

**Happy Data Storing! 🚀🗄️🔍**

*For additional support or questions about the Data Store service, refer to the main project documentation or contact your development team.*
