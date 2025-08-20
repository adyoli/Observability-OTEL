#!/usr/bin/env python3
"""Simple test script to verify the client-based document API endpoints."""

import json
import os
import tempfile
from pathlib import Path

import requests

BASE_URL = "http://localhost"
TEST_CLIENT_ID = "test-client-123"


def create_test_file():
    """Create a temporary test file for uploading"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("This is a test document for the Robin interview process.\n")
        f.write("It contains some sample text to test file upload functionality.\n")
        f.write("Created for testing purposes only.\n")
        return f.name


def test_health_endpoints():
    """Test health check endpoints"""
    print("Testing health endpoints...")

    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"Document API health: {response.status_code} - {response.json()}")

        response = requests.get("http://localhost:8001/health", timeout=10)
        print(f"Data Store health: {response.status_code} - {response.json()}")

    except requests.RequestException as e:
        print(f"Health check failed: {e}")


def test_upload_document():
    """Test document upload endpoint with client ID"""
    print(f"\nTesting document upload for client: {TEST_CLIENT_ID}...")

    test_file_path = create_test_file()

    try:
        with open(test_file_path, "rb") as f:
            files = {"file": ("test_document.txt", f, "text/plain")}
            response = requests.put(
                f"{BASE_URL}/clients/{TEST_CLIENT_ID}/upload-document",
                files=files,
                timeout=30,
            )

        if response.status_code == 200:
            data = response.json()
            print(f"Upload successful! Document ID: {data['document_id']}")
            print(f"Client ID: {data['client_id']}")
            print(f"Response: {json.dumps(data, indent=2)}")
            return data["document_id"]
        else:
            print(f"Upload failed: {response.status_code} - {response.text}")
            return None

    except requests.RequestException as e:
        print(f"Upload request failed: {e}")
        return None
    finally:
        os.unlink(test_file_path)


def test_retrieve_metadata(document_id):
    """Test document metadata retrieval with client ID"""
    if not document_id:
        print("No document ID to test retrieval")
        return

    print(
        f"\nTesting metadata retrieval for client {TEST_CLIENT_ID}, document ID {document_id}..."
    )

    try:
        response = requests.get(
            f"{BASE_URL}/clients/{TEST_CLIENT_ID}/documents/{document_id}", timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            print(f"Metadata retrieval successful!")
            print(f"Response: {json.dumps(data, indent=2)}")
        else:
            print(
                f"Metadata retrieval failed: {response.status_code} - {response.text}"
            )

    except requests.RequestException as e:
        print(f"Metadata retrieval request failed: {e}")


def test_client_isolation(document_id):
    """Test that clients cannot access other clients' documents"""
    if not document_id:
        print("No document ID to test client isolation")
        return

    wrong_client_id = "different-client-456"
    print(
        f"\nTesting client isolation: trying to access {TEST_CLIENT_ID}'s document as {wrong_client_id}..."
    )

    try:
        response = requests.get(
            f"{BASE_URL}/clients/{wrong_client_id}/documents/{document_id}", timeout=10
        )

        if response.status_code == 404:
            print(
                "✅ Client isolation working correctly - document not accessible by different client"
            )
        else:
            print(
                f"❌ Client isolation failed: {response.status_code} - {response.text}"
            )

    except requests.RequestException as e:
        print(f"Client isolation test request failed: {e}")


def main():
    """Run all tests"""
    print("Robin Interview - Client-Based Document API Test Script")
    print("=" * 60)
    print(f"Testing with client ID: {TEST_CLIENT_ID}")

    test_health_endpoints()

    # Test document upload
    document_id = test_upload_document()
    test_retrieve_metadata(document_id)

    test_client_isolation(document_id)

    print("\n" + "=" * 60)
    print("Test completed!")


if __name__ == "__main__":
    main()
