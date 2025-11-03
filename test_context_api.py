#!/usr/bin/env python3
"""
Simple test script for Context Engineering API endpoints.
Run this to verify basic functionality.
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def test_list_contexts():
    """Test listing contexts."""
    print("🧪 Testing: List contexts...")
    try:
        r = requests.get(f"{BASE_URL}/contexts")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            contexts = r.json()
            print(f"   Found {len(contexts)} contexts")
            return contexts
        else:
            print(f"   Error: {r.text[:200]}")
            return []
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return []

def test_create_context(name: str = "Test Context"):
    """Test creating a context."""
    print(f"🧪 Testing: Create context '{name}'...")
    try:
        r = requests.post(
            f"{BASE_URL}/contexts",
            json={
                "name": name,
                "description": "Test context for API testing",
                "org_id": "demo"
            }
        )
        print(f"   Status: {r.status_code}")
        if r.status_code in [200, 201]:
            data = r.json()
            print(f"   ✅ Created: {data.get('context_id')}")
            return data.get('context_id')
        else:
            print(f"   Error: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return None

def test_upload_document(context_id: str, file_path: str):
    """Test uploading a document."""
    print(f"🧪 Testing: Upload document to context {context_id[:8]}...")
    try:
        if not Path(file_path).exists():
            # Create a test file
            test_content = "This is a test document for API testing.\n" * 10
            Path(file_path).write_text(test_content)
        
        with open(file_path, 'rb') as f:
            files = {'file': (Path(file_path).name, f, 'text/plain')}
            data = {'auto_summarize': 'true'}
            r = requests.post(
                f"{BASE_URL}/contexts/{context_id}/documents",
                files=files,
                data=data
            )
        
        print(f"   Status: {r.status_code}")
        if r.status_code in [200, 201]:
            data = r.json()
            print(f"   ✅ Uploaded: {data.get('document_id')}")
            print(f"   Summary: {data.get('summary', 'None')[:100]}...")
            return data.get('document_id')
        else:
            print(f"   Error: {r.text[:200]}")
            return None
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return None

def test_get_documents(context_id: str):
    """Test getting documents for a context."""
    print(f"🧪 Testing: Get documents for context {context_id[:8]}...")
    try:
        r = requests.get(f"{BASE_URL}/contexts/{context_id}/documents")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            docs = data.get('documents', [])
            print(f"   ✅ Found {len(docs)} documents")
            return docs
        else:
            print(f"   Error: {r.text[:200]}")
            return []
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return []

def test_health():
    """Test health endpoint."""
    print("🧪 Testing: Health check...")
    try:
        r = requests.get("http://localhost:8000/health")
        print(f"   Status: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            print(f"   ✅ Status: {data.get('status')}")
            print(f"   Database: {data.get('database', 'unknown')}")
            return True
        else:
            print(f"   ⚠️  Health check failed")
            return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Context Engineering API Test Suite")
    print("=" * 60)
    
    # Health check
    if not test_health():
        print("\n❌ Backend not available. Is it running?")
        return
    
    print()
    
    # List contexts
    contexts = test_list_contexts()
    print()
    
    # Create context if none exist
    if not contexts:
        context_id = test_create_context()
        if not context_id:
            print("\n❌ Failed to create test context")
            return
    else:
        context_id = contexts[0].get('id')
    
    print()
    
    # Upload document
    test_file = "test_document.txt"
    doc_id = test_upload_document(context_id, test_file)
    print()
    
    # Get documents
    if doc_id:
        docs = test_get_documents(context_id)
        print()
    
    print("=" * 60)
    print("✅ Test suite completed!")
    print("=" * 60)
    
    # Cleanup
    if Path(test_file).exists():
        Path(test_file).unlink()
        print(f"🧹 Cleaned up {test_file}")

if __name__ == "__main__":
    main()

