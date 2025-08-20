import asyncio
import logging
import time
from datetime import datetime
from pathlib import Path

import httpx
import magic
from config import get_settings
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, Request, Response
from fastapi.responses import JSONResponse

from telemetry import init_observability
from observability import (
    ObservabilityMiddleware, 
    log_request_metrics, 
    create_span, 
    log_with_context,
    create_health_metrics
)

app = FastAPI(title="Document API", version="1.0.0")

# Add observability middleware
app.add_middleware(ObservabilityMiddleware)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOADS_DIR = Path("/app/uploads")
UPLOADS_DIR.mkdir(exist_ok=True)

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
    """Enhanced health check endpoint with metrics and detailed status."""
    start_time = time.time()
    
    try:
        # Check file system
        fs_status = "healthy" if UPLOADS_DIR.exists() and UPLOADS_DIR.is_dir() else "unhealthy"
        
        # Check data store connectivity
        settings = get_settings()
        data_store_status = "unknown"
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{settings.data_store_url}/health", timeout=5.0)
                data_store_status = "healthy" if response.status_code == 200 else "unhealthy"
        except Exception:
            data_store_status = "unhealthy"
        
        # Overall health
        overall_status = "healthy" if fs_status == "healthy" and data_store_status == "healthy" else "degraded"
        
        # Record metrics
        health_check_counter.add(1, {"status": overall_status})
        health_check_duration.record(time.time() - start_time)
        
        log_with_context(
            "Health check completed",
            level="info",
            overall_status=overall_status,
            fs_status=fs_status,
            data_store_status=data_store_status
        )
        
        return {
            "status": overall_status,
            "service": "document-api",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "file_system": fs_status,
                "data_store": data_store_status
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
            "service": "document-api",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

async def summarise_document_using_llm(file_path):
    """Summarise the document using a large language model with tracing."""
    with create_span("llm_summarization", "document_processing", file_path=str(file_path)) as span:
        try:
            # Call to real LLM API would go here - lets simulate with a sleep to fake the expensive LLM call
            await asyncio.sleep(10)
            
            summary = "This is a summary of the document."
            
            span.set_attribute("summary_length", len(summary))
            span.set_attribute("processing_success", True)
            
            log_with_context(
                "Document summarization completed",
                level="info",
                file_path=str(file_path),
                summary_length=len(summary)
            )
            
            return summary
            
        except Exception as e:
            span.set_attribute("processing_success", False)
            span.set_attribute("error", str(e))
            
            log_with_context(
                f"Document summarization failed: {str(e)}",
                level="error",
                file_path=str(file_path)
            )
            
            raise

@app.put("/clients/{client_id}/upload-document")
async def upload_document(
    client_id: str, 
    file: UploadFile = File(...), 
    settings=Depends(get_settings),
    request: Request = None
):
    """Upload a document and store its metadata for a specific client with comprehensive tracing."""
    file_path = None
    
    with create_span("upload_document", "document_upload", client_id=client_id, file_name=file.filename) as span:
        try:
            # Start file processing
            with create_span("file_processing", "file_operations", client_id=client_id) as file_span:
                content = await file.read()
                file_size = len(content)
                file_type = magic.from_buffer(content, mime=True)
                
                file_span.set_attribute("file_size", file_size)
                file_span.set_attribute("file_type", file_type)
                file_span.set_attribute("content_type", file.content_type)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"{client_id}_{timestamp}_{file.filename}"
                file_path = UPLOADS_DIR / safe_filename
                
                with open(file_path, "wb") as f:
                    f.write(content)
                
                file_span.set_attribute("file_path", str(file_path))
                
                log_with_context(
                    "File processed successfully",
                    level="info",
                    client_id=client_id,
                    file_name=file.filename,
                    file_size=file_size,
                    file_type=file_type
                )
            
            # Generate summary
            summary = await summarise_document_using_llm(file_path)
            
            # Store metadata
            with create_span("store_metadata", "data_operation", client_id=client_id) as store_span:
                metadata = {
                    "client_id": client_id,
                    "filename": file.filename,
                    "file_size": file_size,
                    "file_type": file_type,
                    "content_type": file.content_type,
                    "file_path": str(file_path),
                    "summary": summary,
                }
                
                store_span.set_attribute("metadata_keys", list(metadata.keys()))
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{settings.data_store_url}/clients/{client_id}/documents",
                        json=metadata,
                        timeout=30.0,
                    )
                    
                    if response.status_code != 200:
                        store_span.set_attribute("store_success", False)
                        store_span.set_attribute("error_status", response.status_code)
                        
                        log_with_context(
                            f"Failed to store metadata: {response.text}",
                            level="error",
                            client_id=client_id,
                            status_code=response.status_code
                        )
                        
                        raise HTTPException(
                            status_code=500, detail="Failed to store document metadata"
                        )
                    
                    stored_metadata = response.json()
                    store_span.set_attribute("store_success", True)
                    store_span.set_attribute("document_id", stored_metadata["id"])
                    
                    log_with_context(
                        "Metadata stored successfully",
                        level="info",
                        client_id=client_id,
                        document_id=stored_metadata["id"]
                    )
            
            # Set span attributes for successful upload
            span.set_attribute("upload_success", True)
            span.set_attribute("document_id", stored_metadata["id"])
            span.set_attribute("total_file_size", file_size)
            
            log_with_context(
                "Document uploaded successfully",
                level="info",
                client_id=client_id,
                file_name=file.filename,
                document_id=stored_metadata["id"]
            )
            
            return JSONResponse(
                status_code=200,
                content={
                    "message": "Document uploaded successfully",
                    "client_id": client_id,
                    "document_id": stored_metadata["id"],
                    "metadata": stored_metadata,
                },
            )
            
        except httpx.RequestError as e:
            span.set_attribute("upload_success", False)
            span.set_attribute("error_type", "request_error")
            span.set_attribute("error", str(e))
            
            log_with_context(
                f"Error communicating with data-store: {str(e)}",
                level="error",
                client_id=client_id
            )
            
            raise HTTPException(status_code=503, detail="Data store service unavailable")
            
        except Exception as e:
            span.set_attribute("upload_success", False)
            span.set_attribute("error_type", "general_error")
            span.set_attribute("error", str(e))
            
            log_with_context(
                f"Error uploading document: {str(e)}",
                level="error",
                client_id=client_id
            )
            
            raise HTTPException(status_code=500, detail="Failed to upload document")
            
        finally:
            if file_path and file_path.exists():
                file_path.unlink()
                log_with_context(
                    "Temporary file cleaned up",
                    level="debug",
                    file_path=str(file_path)
                )

@app.get("/clients/{client_id}/documents/{document_id}")
async def retrieve_document_metadata(
    client_id: str, 
    document_id: int, 
    settings=Depends(get_settings)
):
    """Retrieve document metadata by client ID and document ID with tracing."""
    with create_span("retrieve_document", "document_retrieval", client_id=client_id, document_id=document_id) as span:
        try:
            with create_span("fetch_metadata", "data_operation", client_id=client_id) as fetch_span:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{settings.data_store_url}/clients/{client_id}/documents/{document_id}",
                        timeout=30.0,
                    )
                    
                    if response.status_code == 404:
                        fetch_span.set_attribute("fetch_success", False)
                        fetch_span.set_attribute("error_type", "not_found")
                        
                        log_with_context(
                            "Document not found",
                            level="warning",
                            client_id=client_id,
                            document_id=document_id
                        )
                        
                        raise HTTPException(status_code=404, detail="Document not found")
                        
                    elif response.status_code != 200:
                        fetch_span.set_attribute("fetch_success", False)
                        fetch_span.set_attribute("error_status", response.status_code)
                        
                        log_with_context(
                            f"Failed to retrieve metadata: {response.text}",
                            level="error",
                            client_id=client_id,
                            document_id=document_id,
                            status_code=response.status_code
                        )
                        
                        raise HTTPException(
                            status_code=500, detail="Failed to retrieve document metadata"
                        )
                    
                    metadata = response.json()
                    fetch_span.set_attribute("fetch_success", True)
                    fetch_span.set_attribute("metadata_keys", list(metadata.keys()))
                    
                    log_with_context(
                        "Metadata retrieved successfully",
                        level="info",
                        client_id=client_id,
                        document_id=document_id
                    )
            
            # Set span attributes for successful retrieval
            span.set_attribute("retrieval_success", True)
            span.set_attribute("metadata_keys", list(metadata.keys()))
            
            return metadata
            
        except httpx.RequestError as e:
            span.set_attribute("retrieval_success", False)
            span.set_attribute("error_type", "request_error")
            span.set_attribute("error", str(e))
            
            log_with_context(
                f"Error communicating with data-store: {str(e)}",
                level="error",
                client_id=client_id,
                document_id=document_id
            )
            
            raise HTTPException(status_code=503, detail="Data store service unavailable")
            
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
            
            raise HTTPException(
                status_code=500, detail="Failed to retrieve document metadata"
            )

init_observability()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
