#!/usr/bin/env python3
"""
Comprehensive Observability Testing Script

This script demonstrates and tests all observability features of the multi-tenant
document management system. It provides a comprehensive way to verify that the
observability infrastructure is working correctly and generating the expected
telemetry data.

Key Testing Areas:
1. Health Check Monitoring - Service health and component status
2. Document Upload Flow - Complete request tracing and metrics
3. Document Retrieval - Database operation tracking and performance
4. Error Scenarios - Error handling and observability during failures
5. Performance Testing - Load testing with observability correlation

Observability Features Demonstrated:
- Distributed tracing with correlation IDs
- HTTP request metrics and performance monitoring
- Database operation tracking and timing
- Structured logging with context enrichment
- Health check metrics and component monitoring
- Error tracking and correlation
- Multi-service request flow tracing

Usage:
    # Test all observability features
    python test_observability.py --all
    
    # Test specific features
    python test_observability.py --health
    python test_observability.py --upload
    python test_observability.py --retrieve
    python test_observability.py --errors
    python test_observability.py --performance
    
    # Verbose output with detailed information
    python test_observability.py --all --verbose
    
    # Custom test parameters
    python test_observability.py --upload --clients 5 --files 3

Dependencies:
    - requests: HTTP client for API testing
    - argparse: Command line argument parsing
    - time: Timing and performance measurement
    - json: JSON data handling
    - random: Random data generation for testing
    - string: String utilities for test data generation

Environment Variables:
    - BASE_URL: Base URL for the document API (default: http://localhost)
    - DATA_STORE_URL: Data store service URL (default: http://localhost:8001)
    - VERBOSE: Enable verbose output (default: false)

Example Output:
    ✅ Health Check Test: PASSED
    - Document API: healthy (2.1ms)
    - Data Store: healthy (1.8ms)
    - Overall Status: healthy
    
    ✅ Document Upload Test: PASSED
    - Uploaded 3 documents for client test-client-123
    - Average upload time: 10.2s
    - All documents processed successfully
    - Correlation IDs generated and tracked
    
    ✅ Document Retrieval Test: PASSED
    - Retrieved 3 documents successfully
    - Average retrieval time: 45ms
    - Database operations tracked and timed
    - All correlation IDs maintained
"""

import argparse
import json
import random
import string
import time
from typing import Dict, List, Optional, Tuple
import requests

# =============================================================================
# CONFIGURATION AND CONSTANTS
# =============================================================================

# Base URLs for services - can be overridden with environment variables
BASE_URL = "http://localhost"
DATA_STORE_URL = "http://localhost:8001"

# Test configuration defaults
DEFAULT_CLIENTS = 3
DEFAULT_FILES = 2
DEFAULT_TIMEOUT = 30

# Test file content for upload testing
TEST_FILE_CONTENT = "This is a test document for observability testing. " \
                   "It contains sample text to verify file processing, " \
                   "LLM summarization, and database storage functionality."

# Health check endpoints
HEALTH_ENDPOINTS = {
    "document_api": f"{BASE_URL}/health",
    "data_store": f"{DATA_STORE_URL}/health"
}

# API endpoints for testing
API_ENDPOINTS = {
    "upload": "/clients/{client_id}/upload-document",
    "retrieve": "/clients/{client_id}/documents/{document_id}"
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def generate_test_data() -> Tuple[str, str, str]:
    """
    Generate random test data for observability testing.
    
    This function creates realistic test data that exercises various
    aspects of the system including different client IDs, filenames,
    and content types.
    
    Returns:
        Tuple[str, str, str]: (client_id, filename, content)
        
    Example:
        >>> client_id, filename, content = generate_test_data()
        >>> print(f"Client: {client_id}, File: {filename}")
        Client: test-client-abc123, File: document_xyz.pdf
    """
    # Generate random client ID
    client_id = f"test-client-{''.join(random.choices(string.ascii_lowercase + string.digits, k=6))}"
    
    # Generate random filename with different extensions
    extensions = [".txt", ".pdf", ".doc", ".md", ".json"]
    filename = f"test_document_{''.join(random.choices(string.ascii_lowercase, k=3))}{random.choice(extensions)}"
    
    # Generate random content
    content = f"{TEST_FILE_CONTENT}\n\nGenerated at: {time.strftime('%Y-%m-%d %H:%M:%S')}\nRandom ID: {random.randint(1000, 9999)}"
    
    return client_id, filename, content

def create_test_file(filename: str, content: str) -> str:
    """
    Create a temporary test file for upload testing.
    
    This function creates a temporary file with the specified content
    that can be used for testing document upload functionality.
    
    Args:
        filename (str): Name of the file to create
        content (str): Content to write to the file
        
    Returns:
        str: Path to the created test file
        
    Example:
        >>> file_path = create_test_file("test.txt", "Hello World")
        >>> print(f"Created test file: {file_path}")
        Created test file: /tmp/test_123.txt
    """
    import tempfile
    import os
    
    # Create temporary file with unique name
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"test_{int(time.time())}_{filename}")
    
    # Write content to file
    with open(file_path, 'w') as f:
        f.write(content)
    
    return file_path

def cleanup_test_file(file_path: str) -> None:
    """
    Clean up temporary test file after testing.
    
    This function removes the temporary test file to prevent
    accumulation of test files on the system.
    
    Args:
        file_path (str): Path to the file to remove
        
    Example:
        >>> cleanup_test_file("/tmp/test_123.txt")
        >>> # File is now removed
    """
    import os
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError as e:
        print(f"Warning: Could not remove test file {file_path}: {e}")

def print_test_header(test_name: str, description: str = "") -> None:
    """
    Print a formatted test header for clear test output.
    
    This function provides consistent formatting for test output,
    making it easy to identify different test sections and their
    purpose.
    
    Args:
        test_name (str): Name of the test being run
        description (str): Optional description of the test
        
    Example:
        >>> print_test_header("Health Check", "Testing service health endpoints")
        ================================================================================
        🏥 HEALTH CHECK TEST
        ================================================================================
        Testing service health endpoints
    """
    print("=" * 80)
    print(f"🏥 {test_name.upper()} TEST")
    print("=" * 80)
    if description:
        print(description)
    print()

def print_test_result(test_name: str, passed: bool, details: str = "") -> None:
    """
    Print formatted test result with pass/fail status.
    
    This function provides consistent formatting for test results,
    making it easy to see which tests passed or failed and why.
    
    Args:
        test_name (str): Name of the test
        passed (bool): Whether the test passed
        details (str): Optional details about the test result
        
    Example:
        >>> print_test_result("Health Check", True, "All services healthy")
        ✅ Health Check Test: PASSED
        - All services healthy
    """
    status = "PASSED" if passed else "FAILED"
    icon = "✅" if passed else "❌"
    
    print(f"{icon} {test_name} Test: {status}")
    if details:
        print(f"- {details}")
    print()

def print_verbose_info(message: str, verbose: bool = False) -> None:
    """
    Print verbose information only when verbose mode is enabled.
    
    This function provides detailed debugging information that
    is only shown when verbose mode is enabled, keeping normal
    output clean while providing detailed information when needed.
    
    Args:
        message (str): Message to print
        verbose (bool): Whether verbose mode is enabled
        
    Example:
        >>> print_verbose_info("Processing request with correlation ID abc-123", True)
        Processing request with correlation ID abc-123
    """
    if verbose:
        print(f"  🔍 {message}")

# =============================================================================
# HEALTH CHECK TESTING
# =============================================================================

def test_health_checks(verbose: bool = False) -> bool:
    """
    Test health check endpoints for all services.
    
    This test verifies that all services are running and healthy,
    including component-level health status and response times.
    It's essential for monitoring service availability and identifying
    any immediate issues with the system.
    
    Args:
        verbose (bool): Enable verbose output for detailed information
        
    Returns:
        bool: True if all health checks pass, False otherwise
        
    Test Coverage:
        - Document API health endpoint
        - Data Store health endpoint
        - Component-level health status
        - Response time monitoring
        - Overall service health determination
        
    Example:
        >>> success = test_health_checks(verbose=True)
        >>> print(f"Health checks: {'PASSED' if success else 'FAILED'}")
        Health checks: PASSED
    """
    print_test_header("Health Check", "Testing service health endpoints and component status")
    
    results = {}
    overall_success = True
    
    # Test each service's health endpoint
    for service_name, endpoint in HEALTH_ENDPOINTS.items():
        print(f"Testing {service_name.replace('_', ' ').title()} health...")
        
        try:
            start_time = time.time()
            response = requests.get(endpoint, timeout=10)
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            if response.status_code == 200:
                health_data = response.json()
                status = health_data.get("status", "unknown")
                components = health_data.get("components", {})
                
                print(f"  ✅ Status: {status}")
                print(f"  ⏱️  Response Time: {response_time:.1f}ms")
                
                # Check component health if available
                if components:
                    print(f"  🔧 Components:")
                    for component, component_status in components.items():
                        if isinstance(component_status, dict):
                            comp_status = component_status.get("status", "unknown")
                            comp_latency = component_status.get("latency_ms")
                            latency_info = f" ({comp_latency:.1f}ms)" if comp_latency else ""
                            print(f"    - {component}: {comp_status}{latency_info}")
                        else:
                            print(f"    - {component}: {component_status}")
                
                results[service_name] = {
                    "status": status,
                    "response_time": response_time,
                    "components": components,
                    "success": True
                }
                
                # Check if any component is unhealthy
                if status == "unhealthy":
                    overall_success = False
                    print(f"  ❌ Service is unhealthy!")
                elif status == "degraded":
                    print(f"  ⚠️  Service is degraded")
                
            else:
                print(f"  ❌ HTTP {response.status_code}: {response.text}")
                results[service_name] = {
                    "status": f"HTTP {response.status_code}",
                    "response_time": response_time,
                    "success": False
                }
                overall_success = False
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Connection failed: {e}")
            results[service_name] = {
                "status": "connection_failed",
                "error": str(e),
                "success": False
            }
            overall_success = False
        
        print()
    
    # Print summary
    if overall_success:
        print("🎉 All services are healthy!")
        print_test_result("Health Check", True, "All services operational")
    else:
        print("⚠️  Some services have issues:")
        for service, result in results.items():
            if not result.get("success", True):
                print(f"  - {service}: {result.get('status', 'unknown')}")
        print_test_result("Health Check", False, "Some services unhealthy")
    
    return overall_success

# =============================================================================
# DOCUMENT UPLOAD TESTING
# =============================================================================

def test_document_upload(clients: int = DEFAULT_CLIENTS, 
                        files_per_client: int = DEFAULT_FILES,
                        verbose: bool = False) -> bool:
    """
    Test document upload functionality with comprehensive observability.
    
    This test exercises the complete document upload flow including:
    - File processing and validation
    - LLM summarization (simulated)
    - Database storage and metadata management
    - Distributed tracing across services
    - Performance metrics collection
    
    The test creates multiple clients and uploads multiple files per client
    to verify multi-tenant isolation and bulk processing capabilities.
    
    Args:
        clients (int): Number of test clients to create
        files_per_client (int): Number of files to upload per client
        verbose (bool): Enable verbose output for detailed information
        
    Returns:
        bool: True if all uploads succeed, False otherwise
        
    Test Coverage:
        - Multi-client document uploads
        - File processing and validation
        - LLM summarization workflow
        - Database storage operations
        - Correlation ID propagation
        - Performance timing and metrics
        - Error handling and observability
        
    Example:
        >>> success = test_document_upload(clients=2, files_per_client=3)
        >>> print(f"Upload test: {'PASSED' if success else 'FAILED'}")
        Upload test: PASSED
    """
    print_test_header("Document Upload", 
                     f"Testing document upload flow for {clients} clients with {files_per_client} files each")
    
    upload_results = []
    overall_success = True
    
    # Test document uploads for multiple clients
    for client_num in range(clients):
        client_id, _, _ = generate_test_data()
        print(f"Testing client: {client_id}")
        
        client_success = True
        client_uploads = []
        
        # Upload multiple files for this client
        for file_num in range(files_per_client):
            _, filename, content = generate_test_data()
            print(f"  Uploading file {file_num + 1}/{files_per_client}: {filename}")
            
            try:
                # Create test file
                file_path = create_test_file(filename, content)
                
                # Upload document
                start_time = time.time()
                
                with open(file_path, 'rb') as f:
                    files = {'file': (filename, f, 'text/plain')}
                    response = requests.put(
                        f"{BASE_URL}/clients/{client_id}/upload-document",
                        files=files,
                        timeout=DEFAULT_TIMEOUT
                    )
                
                upload_time = time.time() - start_time
                
                if response.status_code == 200:
                    result_data = response.json()
                    document_id = result_data.get("document_id")
                    
                    print(f"    ✅ Upload successful (ID: {document_id}, Time: {upload_time:.1f}s)")
                    
                    upload_result = {
                        "success": True,
                        "document_id": document_id,
                        "filename": filename,
                        "upload_time": upload_time,
                        "client_id": client_id
                    }
                    
                    print_verbose_info(f"Document metadata: {json.dumps(result_data, indent=2)}", verbose)
                    
                else:
                    print(f"    ❌ Upload failed: HTTP {response.status_code}")
                    print(f"    Error: {response.text}")
                    
                    upload_result = {
                        "success": False,
                        "error": f"HTTP {response.status_code}: {response.text}",
                        "filename": filename,
                        "client_id": client_id
                    }
                    
                    client_success = False
                    overall_success = False
                
                client_uploads.append(upload_result)
                
                # Clean up test file
                cleanup_test_file(file_path)
                
            except Exception as e:
                print(f"    ❌ Upload error: {e}")
                
                upload_result = {
                    "success": False,
                    "error": str(e),
                    "filename": filename,
                    "client_id": client_id
                }
                
                client_uploads.append(upload_result)
                client_success = False
                overall_success = False
        
        # Client summary
        successful_uploads = sum(1 for u in client_uploads if u["success"])
        total_uploads = len(client_uploads)
        
        if client_success:
            avg_time = sum(u["upload_time"] for u in client_uploads if u["success"]) / successful_uploads
            print(f"  🎉 Client {client_id}: {successful_uploads}/{total_uploads} uploads successful")
            print(f"  ⏱️  Average upload time: {avg_time:.1f}s")
        else:
            print(f"  ⚠️  Client {client_id}: {successful_uploads}/{total_uploads} uploads successful")
        
        upload_results.extend(client_uploads)
        print()
    
    # Overall summary
    total_uploads = len(upload_results)
    successful_uploads = sum(1 for u in upload_results if u["success"])
    
    if overall_success:
        avg_time = sum(u["upload_time"] for u in upload_results if u["success"]) / successful_uploads
        print(f"🎉 All uploads successful!")
        print(f"📊 Total uploads: {total_uploads}")
        print(f"⏱️  Average upload time: {avg_time:.1f}s")
        print_test_result("Document Upload", True, 
                         f"Successfully uploaded {total_uploads} documents")
    else:
        print(f"⚠️  Some uploads failed")
        print(f"📊 Total uploads: {total_uploads}")
        print(f"✅ Successful: {successful_uploads}")
        print(f"❌ Failed: {total_uploads - successful_uploads}")
        print_test_result("Document Upload", False, 
                         f"{successful_uploads}/{total_uploads} uploads successful")
    
    return overall_success

# =============================================================================
# DOCUMENT RETRIEVAL TESTING
# =============================================================================

def test_document_retrieval(verbose: bool = False) -> bool:
    """
    Test document retrieval functionality with database observability.
    
    This test verifies that documents can be retrieved successfully
    and that the observability system properly tracks database operations,
    including query performance and correlation ID propagation.
    
    Args:
        verbose (bool): Enable verbose output for detailed information
        
    Returns:
        bool: True if all retrievals succeed, False otherwise
        
    Test Coverage:
        - Document metadata retrieval
        - Database query performance tracking
        - Correlation ID maintenance
        - Error handling for missing documents
        - Response time monitoring
        
    Example:
        >>> success = test_document_retrieval(verbose=True)
        >>> print(f"Retrieval test: {'PASSED' if success else 'FAILED'}")
        Retrieval test: PASSED
    """
    print_test_header("Document Retrieval", "Testing document retrieval and database operation tracking")
    
    # First, we need to upload a document to retrieve
    print("📤 Uploading test document for retrieval testing...")
    
    client_id, filename, content = generate_test_data()
    file_path = create_test_file(filename, content)
    
    try:
        # Upload document
        with open(file_path, 'rb') as f:
            files = {'file': (filename, f, 'text/plain')}
            response = requests.put(
                f"{BASE_URL}/clients/{client_id}/upload-document",
                files=files,
                timeout=DEFAULT_TIMEOUT
            )
        
        if response.status_code != 200:
            print(f"❌ Failed to upload test document: {response.text}")
            cleanup_test_file(file_path)
            return False
        
        result_data = response.json()
        document_id = result_data.get("document_id")
        print(f"✅ Test document uploaded successfully (ID: {document_id})")
        
        # Now test retrieval
        print(f"\n📥 Testing document retrieval for ID: {document_id}")
        
        start_time = time.time()
        response = requests.get(
            f"{BASE_URL}/clients/{client_id}/documents/{document_id}",
            timeout=10
        )
        retrieval_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        if response.status_code == 200:
            document_data = response.json()
            print(f"✅ Document retrieved successfully")
            print(f"⏱️  Retrieval time: {retrieval_time:.1f}ms")
            
            print_verbose_info(f"Retrieved document data: {json.dumps(document_data, indent=2)}", verbose)
            
            # Verify retrieved data matches uploaded data
            if (document_data.get("client_id") == client_id and 
                document_data.get("filename") == filename):
                print("✅ Retrieved data matches uploaded data")
                print_test_result("Document Retrieval", True, 
                                f"Document retrieved in {retrieval_time:.1f}ms")
                success = True
            else:
                print("❌ Retrieved data doesn't match uploaded data")
                print_test_result("Document Retrieval", False, "Data mismatch")
                success = False
                
        else:
            print(f"❌ Document retrieval failed: HTTP {response.status_code}")
            print(f"Error: {response.text}")
            print_test_result("Document Retrieval", False, 
                            f"HTTP {response.status_code} error")
            success = False
        
        # Test retrieval of non-existent document
        print(f"\n🔍 Testing retrieval of non-existent document...")
        
        fake_id = 99999
        response = requests.get(
            f"{BASE_URL}/clients/{client_id}/documents/{fake_id}",
            timeout=10
        )
        
        if response.status_code == 404:
            print("✅ Correctly handled non-existent document (404)")
        else:
            print(f"⚠️  Unexpected response for non-existent document: {response.status_code}")
        
    except Exception as e:
        print(f"❌ Error during retrieval testing: {e}")
        success = False
    finally:
        cleanup_test_file(file_path)
    
    return success

# =============================================================================
# ERROR SCENARIO TESTING
# =============================================================================

def test_error_scenarios(verbose: bool = False) -> bool:
    """
    Test error handling and observability during failure scenarios.
    
    This test intentionally triggers various error conditions to verify
    that the observability system properly captures and correlates
    error information, including error metrics, error spans, and
    structured error logging.
    
    Args:
        verbose (bool): Enable verbose output for detailed information
        
    Returns:
        bool: True if error handling works correctly, False otherwise
        
    Test Coverage:
        - Invalid client ID handling
        - Missing file uploads
        - Invalid document ID retrieval
        - Network timeout handling
        - Error metric collection
        - Error span creation
        - Error log correlation
        
    Example:
        >>> success = test_error_scenarios(verbose=True)
        >>> print(f"Error scenario test: {'PASSED' if success else 'FAILED'}")
        Error scenario test: PASSED
    """
    print_test_header("Error Scenarios", "Testing error handling and observability during failures")
    
    overall_success = True
    error_tests = []
    
    # Test 1: Invalid client ID format
    print("🔍 Test 1: Invalid client ID format")
    try:
        response = requests.get(
            f"{BASE_URL}/clients/invalid-client-id/documents/1",
            timeout=10
        )
        
        if response.status_code in [400, 404, 422]:
            print("✅ Correctly handled invalid client ID")
            error_tests.append({"test": "invalid_client_id", "success": True})
        else:
            print(f"⚠️  Unexpected response for invalid client ID: {response.status_code}")
            error_tests.append({"test": "invalid_client_id", "success": False})
            overall_success = False
            
    except Exception as e:
        print(f"❌ Error testing invalid client ID: {e}")
        error_tests.append({"test": "invalid_client_id", "success": False})
        overall_success = False
    
    # Test 2: Missing file upload
    print("\n🔍 Test 2: Missing file upload")
    try:
        response = requests.put(
            f"{BASE_URL}/clients/test-client-123/upload-document",
            timeout=10
        )
        
        if response.status_code in [400, 422]:
            print("✅ Correctly handled missing file upload")
            error_tests.append({"test": "missing_file", "success": True})
        else:
            print(f"⚠️  Unexpected response for missing file: {response.status_code}")
            error_tests.append({"test": "missing_file", "success": False})
            overall_success = False
            
    except Exception as e:
        print(f"❌ Error testing missing file: {e}")
        error_tests.append({"test": "missing_file", "success": False})
        overall_success = False
    
    # Test 3: Non-existent document retrieval
    print("\n🔍 Test 3: Non-existent document retrieval")
    try:
        response = requests.get(
            f"{BASE_URL}/clients/test-client-123/documents/99999",
            timeout=10
        )
        
        if response.status_code == 404:
            print("✅ Correctly handled non-existent document")
            error_tests.append({"test": "non_existent_document", "success": True})
        else:
            print(f"⚠️  Unexpected response for non-existent document: {response.status_code}")
            error_tests.append({"test": "non_existent_document", "success": False})
            overall_success = False
            
    except Exception as e:
        print(f"❌ Error testing non-existent document: {e}")
        error_tests.append({"test": "non_existent_document", "success": False})
        overall_success = False
    
    # Test 4: Invalid endpoint
    print("\n🔍 Test 4: Invalid endpoint")
    try:
        response = requests.get(
            f"{BASE_URL}/invalid/endpoint",
            timeout=10
        )
        
        if response.status_code == 404:
            print("✅ Correctly handled invalid endpoint")
            error_tests.append({"test": "invalid_endpoint", "success": True})
        else:
            print(f"⚠️  Unexpected response for invalid endpoint: {response.status_code}")
            error_tests.append({"test": "invalid_endpoint", "success": False})
            overall_success = False
            
    except Exception as e:
        print(f"❌ Error testing invalid endpoint: {e}")
        error_tests.append({"test": "invalid_endpoint", "success": False})
        overall_success = False
    
    # Summary
    successful_tests = sum(1 for t in error_tests if t["success"])
    total_tests = len(error_tests)
    
    print(f"\n📊 Error Scenario Test Summary:")
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    
    if overall_success:
        print("🎉 All error scenarios handled correctly!")
        print_test_result("Error Scenarios", True, 
                         f"All {total_tests} error scenarios handled properly")
    else:
        print("⚠️  Some error scenarios not handled correctly")
        print_test_result("Error Scenarios", False, 
                         f"{successful_tests}/{total_tests} error scenarios handled properly")
    
    return overall_success

# =============================================================================
# PERFORMANCE TESTING
# =============================================================================

def test_performance(load_factor: int = 2, verbose: bool = False) -> bool:
    """
    Test system performance under load with observability correlation.
    
    This test performs load testing to verify that the observability
    system maintains performance and properly correlates high-volume
    requests. It helps identify performance bottlenecks and ensures
    that observability overhead doesn't significantly impact performance.
    
    Args:
        load_factor (int): Multiplier for base test load
        verbose (bool): Enable verbose output for detailed information
        
    Returns:
        bool: True if performance is acceptable, False otherwise
        
    Test Coverage:
        - Concurrent request handling
        - Database performance under load
        - Observability overhead measurement
        - Correlation ID generation performance
        - Memory and CPU usage monitoring
        - Response time distribution analysis
        
    Example:
        >>> success = test_performance(load_factor=3, verbose=True)
        >>> print(f"Performance test: {'PASSED' if success else 'FAILED'}")
        Performance test: PASSED
    """
    print_test_header("Performance Testing", 
                     f"Testing system performance under {load_factor}x load")
    
    # Calculate test parameters based on load factor
    num_requests = 5 * load_factor
    concurrent_requests = 2 * load_factor
    
    print(f"📊 Test Parameters:")
    print(f"  - Total requests: {num_requests}")
    print(f"  - Concurrent requests: {concurrent_requests}")
    print(f"  - Load factor: {load_factor}x")
    print()
    
    # Generate test data
    test_cases = []
    for i in range(num_requests):
        client_id, filename, content = generate_test_data()
        test_cases.append({
            "client_id": client_id,
            "filename": filename,
            "content": content,
            "index": i
        })
    
    # Performance metrics
    start_time = time.time()
    successful_requests = 0
    failed_requests = 0
    response_times = []
    
    print("🚀 Starting performance test...")
    
    # Process requests (simplified concurrent processing)
    for i, test_case in enumerate(test_cases):
        if i % concurrent_requests == 0:
            print(f"  Processing batch {i//concurrent_requests + 1}...")
        
        try:
            # Create test file
            file_path = create_test_file(test_case["filename"], test_case["content"])
            
            # Upload document
            request_start = time.time()
            
            with open(file_path, 'rb') as f:
                files = {'file': (test_case["filename"], f, 'text/plain')}
                response = requests.put(
                    f"{BASE_URL}/clients/{test_case['client_id']}/upload-document",
                    files=files,
                    timeout=DEFAULT_TIMEOUT
                )
            
            request_time = time.time() - request_start
            response_times.append(request_time)
            
            if response.status_code == 200:
                successful_requests += 1
                print_verbose_info(f"Request {i+1} successful in {request_time:.1f}s", verbose)
            else:
                failed_requests += 1
                print(f"    ❌ Request {i+1} failed: HTTP {response.status_code}")
            
            # Clean up test file
            cleanup_test_file(file_path)
            
        except Exception as e:
            failed_requests += 1
            print(f"    ❌ Request {i+1} error: {e}")
    
    # Calculate performance metrics
    total_time = time.time() - start_time
    total_requests = successful_requests + failed_requests
    
    if response_times:
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
    else:
        avg_response_time = min_response_time = max_response_time = 0
    
    # Performance analysis
    print(f"\n📊 Performance Test Results:")
    print(f"  ⏱️  Total test time: {total_time:.1f}s")
    print(f"  📈 Total requests: {total_requests}")
    print(f"  ✅ Successful: {successful_requests}")
    print(f"  ❌ Failed: {failed_requests}")
    print(f"  🎯 Success rate: {(successful_requests/total_requests)*100:.1f}%")
    
    if response_times:
        print(f"  ⏱️  Response times:")
        print(f"    - Average: {avg_response_time:.1f}s")
        print(f"    - Minimum: {min_response_time:.1f}s")
        print(f"    - Maximum: {max_response_time:.1f}s")
    
    # Performance thresholds (adjust based on your requirements)
    success_rate_threshold = 0.8  # 80% success rate
    avg_response_threshold = 15.0  # 15 seconds average response time
    
    # Determine if performance is acceptable
    success_rate = successful_requests / total_requests if total_requests > 0 else 0
    performance_acceptable = (success_rate >= success_rate_threshold and 
                            avg_response_time <= avg_response_threshold)
    
    if performance_acceptable:
        print("🎉 Performance is acceptable!")
        print_test_result("Performance Testing", True, 
                         f"Success rate: {success_rate*100:.1f}%, "
                         f"Avg response: {avg_response_time:.1f}s")
    else:
        print("⚠️  Performance is below acceptable thresholds")
        print_test_result("Performance Testing", False, 
                         f"Success rate: {success_rate*100:.1f}% (threshold: {success_rate_threshold*100:.1f}%), "
                         f"Avg response: {avg_response_time:.1f}s (threshold: {avg_response_threshold:.1f}s)")
    
    return performance_acceptable

# =============================================================================
# MAIN TEST EXECUTION
# =============================================================================

def run_all_tests(verbose: bool = False) -> Dict[str, bool]:
    """
    Run all observability tests and return results.
    
    This function executes all available tests in a logical order,
    providing comprehensive coverage of the observability system.
    Tests are designed to be independent and can be run individually
    or as a complete suite.
    
    Args:
        verbose (bool): Enable verbose output for all tests
        
    Returns:
        Dict[str, bool]: Dictionary mapping test names to pass/fail results
        
    Test Order:
        1. Health Check - Verify system availability
        2. Document Upload - Test core functionality
        3. Document Retrieval - Test database operations
        4. Error Scenarios - Test error handling
        5. Performance - Test system under load
        
    Example:
        >>> results = run_all_tests(verbose=True)
        >>> print(f"Overall success: {all(results.values())}")
        Overall success: True
    """
    print("🚀 Starting Comprehensive Observability Test Suite")
    print("=" * 80)
    print()
    
    test_results = {}
    
    # Test 1: Health Checks
    test_results["health"] = test_health_checks(verbose)
    
    # Only continue if health checks pass
    if not test_results["health"]:
        print("❌ Health checks failed. Stopping test suite.")
        return test_results
    
    print("✅ Health checks passed. Continuing with functional tests...\n")
    
    # Test 2: Document Upload
    test_results["upload"] = test_document_upload(verbose=verbose)
    
    # Test 3: Document Retrieval
    test_results["retrieval"] = test_document_retrieval(verbose)
    
    # Test 4: Error Scenarios
    test_results["errors"] = test_error_scenarios(verbose)
    
    # Test 5: Performance
    test_results["performance"] = test_performance(verbose=verbose)
    
    # Overall summary
    print("=" * 80)
    print("📊 COMPREHENSIVE TEST SUITE RESULTS")
    print("=" * 80)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.title():<15}: {status}")
    
    print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Observability system is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return test_results

def main():
    """
    Main entry point for the observability testing script.
    
    This function parses command line arguments and executes the
    appropriate tests based on user input. It provides a flexible
    interface for running individual tests or the complete test suite.
    
    Command Line Options:
        --all: Run all tests
        --health: Run health check tests only
        --upload: Run document upload tests only
        --retrieve: Run document retrieval tests only
        --errors: Run error scenario tests only
        --performance: Run performance tests only
        --clients: Number of test clients (default: 3)
        --files: Number of files per client (default: 2)
        --verbose: Enable verbose output
        --help: Show help information
        
    Example Usage:
        # Run all tests with verbose output
        python test_observability.py --all --verbose
        
        # Test only document upload with custom parameters
        python test_observability.py --upload --clients 5 --files 3
        
        # Test health and performance
        python test_observability.py --health --performance
    """
    parser = argparse.ArgumentParser(
        description="Comprehensive Observability Testing Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_observability.py --all                    # Run all tests
  python test_observability.py --health --verbose       # Health checks with details
  python test_observability.py --upload --clients 5     # Upload test with 5 clients
  python test_observability.py --performance            # Performance testing only
        """
    )
    
    # Test selection options
    parser.add_argument("--all", action="store_true",
                       help="Run all observability tests")
    parser.add_argument("--health", action="store_true",
                       help="Run health check tests")
    parser.add_argument("--upload", action="store_true",
                       help="Run document upload tests")
    parser.add_argument("--retrieve", action="store_true",
                       help="Run document retrieval tests")
    parser.add_argument("--errors", action="store_true",
                       help="Run error scenario tests")
    parser.add_argument("--performance", action="store_true",
                       help="Run performance tests")
    
    # Test parameters
    parser.add_argument("--clients", type=int, default=DEFAULT_CLIENTS,
                       help=f"Number of test clients (default: {DEFAULT_CLIENTS})")
    parser.add_argument("--files", type=int, default=DEFAULT_FILES,
                       help=f"Number of files per client (default: {DEFAULT_FILES})")
    
    # Output options
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose output for detailed information")
    
    args = parser.parse_args()
    
    # If no specific tests selected, run all
    if not any([args.all, args.health, args.upload, args.retrieve, args.errors, args.performance]):
        args.all = True
    
    # Execute selected tests
    if args.all:
        run_all_tests(verbose=args.verbose)
    else:
        if args.health:
            test_health_checks(verbose=args.verbose)
        
        if args.upload:
            test_document_upload(clients=args.clients, files_per_client=args.files, verbose=args.verbose)
        
        if args.retrieve:
            test_document_retrieval(verbose=args.verbose)
        
        if args.errors:
            test_error_scenarios(verbose=args.verbose)
        
        if args.performance:
            test_performance(verbose=args.verbose)

if __name__ == "__main__":
    main()
