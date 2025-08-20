import logging
import time
from datetime import datetime

import models
from database import engine, get_db
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from models import DocumentMetadata
from schemas import DocumentMetadataCreate, DocumentMetadataResponse
from sqlalchemy.orm import Session
from sqlalchemy import text

from telemetry import init_observability
from observability import (
    ObservabilityMiddleware, 
    log_request_metrics, 
    create_span, 
    log_with_context,
    create_health_metrics,
    track_db_operation
)

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Data Store API", version="1.0.0")

# Add observability middleware
app.add_middleware(ObservabilityMiddleware)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create health metrics
health_check_counter, health_check_duration = create_health_metrics()

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Middleware to add process time header and log metrics."""
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    # Calculate duration
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log metrics
    log_request_metrics(request, response, process_time)
    
    return response

@app.get("/health")
async def health_check():
    """Enhanced health check endpoint with database connectivity and detailed status."""
    start_time = time.time()
    
    try:
        # Check database connectivity (simplified to avoid connection pool issues)
        db_status = "unknown"
        db_latency = 0
        
        try:
            db = next(get_db())
            # Test database connection with a simple query
            result = db.execute(text("SELECT 1"))
            result.fetchone()
            db_status = "healthy"
            db_latency = time.time() - start_time
            db.close()  # Explicitly close the connection
        except Exception as e:
            db_status = "unhealthy"
            log_with_context(
                f"Database health check failed: {str(e)}",
                level="error"
            )
        
        # Check table existence (simplified)
        tables_status = "unknown"
        try:
            db = next(get_db())
            # Check if our main table exists
            result = db.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'document_metadata'
                )
            """))
            table_exists = result.fetchone()[0]
            tables_status = "healthy" if table_exists else "missing_tables"
            db.close()  # Explicitly close the connection
        except Exception as e:
            tables_status = "unhealthy"
            log_with_context(
                f"Table check failed: {str(e)}",
                level="error"
            )
        
        # Overall health
        overall_status = "healthy"
        if db_status != "healthy" or tables_status != "healthy":
            overall_status = "degraded"
        if db_status == "unhealthy":
            overall_status = "unhealthy"
        
        # Record metrics
        health_check_counter.add(1, {"status": overall_status})
        health_check_duration.record(time.time() - start_time)
        
        log_with_context(
            "Health check completed",
            level="info",
            overall_status=overall_status,
            db_status=db_status,
            tables_status=tables_status,
            db_latency=db_latency
        )
        
        return {
            "status": overall_status,
            "service": "data-store",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "database": {
                    "status": db_status,
                    "latency_ms": round(db_latency * 1000, 2) if db_latency > 0 else None
                },
                "tables": tables_status
            },
            "version": "1.0.0"
        }
        
    except Exception as e:
        health_check_counter.add(1, {"status": "unhealthy"})
        health_check_duration.record(time.time() - start_time)
        
        log_with_context(
            f"Health check failed: {str(e)}",
            level="error"
        )
        
        return {
            "status": "unhealthy",
            "service": "data-store",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/clients/{client_id}/documents", response_model=DocumentMetadataResponse)
async def create_client_document_metadata(
    client_id: str, 
    document: DocumentMetadataCreate, 
    db: Session = Depends(get_db)
):
    """Store document metadata for a specific client with comprehensive tracing."""
    with create_span("create_document", "document_creation", client_id=client_id) as span:
        try:
            document_data = document.dict()
            document_data["client_id"] = client_id
            
            span.set_attribute("document_keys", list(document_data.keys()))
            span.set_attribute("filename", document_data.get("filename"))
            span.set_attribute("file_size", document_data.get("file_size"))
            
            # Store in database with tracking
            with track_db_operation("insert", "documentmetadata", client_id=client_id) as db_tracker:
                db_document = DocumentMetadata(**document_data)
                db.add(db_document)
                db.commit()
                db.refresh(db_document)
                
                db_tracker.span.set_attribute("document_id", db_document.id)
            
            span.set_attribute("creation_success", True)
            span.set_attribute("document_id", db_document.id)
            
            log_with_context(
                "Document metadata stored successfully",
                level="info",
                client_id=client_id,
                document_id=db_document.id,
                file_name=document_data.get("filename")
            )
            
            return db_document
            
        except Exception as e:
            span.set_attribute("creation_success", False)
            span.set_attribute("error", str(e))
            
            log_with_context(
                f"Error storing document metadata: {str(e)}",
                level="error",
                client_id=client_id
            )
            
            db.rollback()
            raise HTTPException(status_code=500, detail="Failed to store document metadata")

@app.get(
    "/clients/{client_id}/documents/{document_id}",
    response_model=DocumentMetadataResponse,
)
async def get_document_metadata(
    client_id: str, 
    document_id: int, 
    db: Session = Depends(get_db)
):
    """Retrieve document metadata by client ID and document ID with tracing."""
    with create_span("get_document", "document_retrieval", client_id=client_id, document_id=document_id) as span:
        try:
            # Query database with tracking
            with track_db_operation("select", "documentmetadata", client_id=client_id, document_id=document_id) as db_tracker:
                document = (
                    db.query(DocumentMetadata)
                    .filter(
                        DocumentMetadata.client_id == client_id, 
                        DocumentMetadata.id == document_id
                    )
                    .first()
                )
                
                if not document:
                    db_tracker.span.set_attribute("found", False)
                    span.set_attribute("retrieval_success", False)
                    span.set_attribute("error_type", "not_found")
                    
                    log_with_context(
                        "Document not found",
                        level="warning",
                        client_id=client_id,
                        document_id=document_id
                    )
                    
                    raise HTTPException(status_code=404, detail="Document not found")
                
                db_tracker.span.set_attribute("found", True)
                db_tracker.span.set_attribute("document_id", document.id)
            
            # Set span attributes for successful retrieval
            span.set_attribute("retrieval_success", True)
            span.set_attribute("document_id", document.id)
            span.set_attribute("filename", document.filename)
            span.set_attribute("file_size", document.file_size)
            
            log_with_context(
                "Document metadata retrieved successfully",
                level="info",
                client_id=client_id,
                document_id=document_id,
                file_name=document.filename
            )
            
            return document
            
        except HTTPException:
            raise
            
        except Exception as e:
            span.set_attribute("retrieval_success", False)
            span.set_attribute("error_type", "general_error")
            span.set_attribute("error", str(e))
            
            log_with_context(
                f"Error retrieving document metadata: {str(e)}",
                level="error",
                client_id=client_id,
                document_id=document_id
            )
            
            raise HTTPException(status_code=500, detail="Failed to retrieve document metadata")

init_observability()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
