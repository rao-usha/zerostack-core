#!/usr/bin/env python3
"""
Test script for document upload and summarization.
This test reproduces the upload error and helps identify the issue.
"""
import requests
import json
from pathlib import Path
import traceback
import sys

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_create_context():
    """Create a test context."""
    print_section("Step 1: Create Test Context")
    try:
        response = requests.post(
            f"{BASE_URL}/contexts",
            json={
                "name": "Document Upload Test Context",
                "description": "Testing document upload functionality",
                "org_id": "demo"
            },
            timeout=10
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code in [200, 201]:
            data = response.json()
            context_id = data.get('context_id')
            print(f"✅ Context created: {context_id}")
            return context_id
        else:
            print(f"❌ Failed to create context")
            print(f"Response: {response.text[:500]}")
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        traceback.print_exc()
        return None

def test_upload_text_file(context_id: str):
    """Test uploading a simple text file."""
    print_section("Step 2: Upload Text Document (with auto_summarize=True)")
    
    # Create a test file
    test_content = """This is a test document for upload testing.
    
It contains multiple paragraphs to test text extraction.

The document should be processed and summarized automatically.

This is the final paragraph of the test document.
"""
    test_file = Path("test_upload.txt")
    test_file.write_text(test_content)
    
    try:
        print(f"Test file created: {test_file} ({test_file.stat().st_size} bytes)")
        print(f"Uploading to context: {context_id}")
        
        with open(test_file, 'rb') as f:
            files = {
                'file': ('test_upload.txt', f, 'text/plain')
            }
            data = {
                'auto_summarize': 'true',
                'name': 'Test Upload Document'
            }
            
            print(f"\nUploading file...")
            response = requests.post(
                f"{BASE_URL}/contexts/{context_id}/documents",
                files=files,
                data=data,
                timeout=30
            )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload successful!")
            print(f"   Document ID: {data.get('document_id')}")
            print(f"   Filename: {data.get('filename')}")
            print(f"   File Size: {data.get('file_size')} bytes")
            print(f"   SHA256: {data.get('sha256', 'N/A')[:16]}...")
            print(f"   Summary: {data.get('summary', 'None')}")
            
            # Cleanup
            test_file.unlink()
            return data.get('document_id')
        else:
            print(f"❌ Upload failed!")
            print(f"\nFull Response:")
            print(response.text)
            
            # Try to parse as JSON for better formatting
            try:
                error_data = response.json()
                print(f"\nError Details (JSON):")
                print(json.dumps(error_data, indent=2))
            except:
                pass
            
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out (30s)")
        return None
    except Exception as e:
        print(f"❌ Exception occurred:")
        traceback.print_exc()
        return None
    finally:
        if test_file.exists():
            test_file.unlink()

def test_upload_without_summary(context_id: str):
    """Test uploading without auto-summarization."""
    print_section("Step 3: Upload Document (auto_summarize=False)")
    
    test_file = Path("test_upload_no_sum.txt")
    test_file.write_text("This is a simple test document without summarization.")
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_upload_no_sum.txt', f, 'text/plain')}
            data = {'auto_summarize': 'false'}
            
            response = requests.post(
                f"{BASE_URL}/contexts/{context_id}/documents",
                files=files,
                data=data,
                timeout=30
            )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Upload successful (no summary)")
            print(f"   Document ID: {data.get('document_id')}")
            print(f"   Summary: {data.get('summary', 'None')}")
            return data.get('document_id')
        else:
            print(f"❌ Upload failed!")
            print(f"Response: {response.text[:500]}")
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        traceback.print_exc()
        return None
    finally:
        if test_file.exists():
            test_file.unlink()

def test_summarize_document(document_id: str):
    """Test manual summarization."""
    print_section("Step 4: Manual Document Summarization")
    
    try:
        response = requests.post(
            f"{BASE_URL}/contexts/documents/{document_id}/summarize",
            json={"style": "concise"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Summarization successful!")
            print(f"   Summary: {data.get('summary', 'N/A')}")
            return True
        else:
            print(f"❌ Summarization failed!")
            print(f"Response: {response.text[:500]}")
            try:
                error_data = response.json()
                print(f"Error: {json.dumps(error_data, indent=2)}")
            except:
                pass
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        traceback.print_exc()
        return False

def test_get_documents(context_id: str):
    """Test getting documents list."""
    print_section("Step 5: Get Documents List")
    
    try:
        response = requests.get(f"{BASE_URL}/contexts/{context_id}/documents")
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            docs = data.get('documents', [])
            print(f"✅ Found {len(docs)} documents")
            for doc in docs:
                print(f"   - {doc.get('name')} ({doc.get('file_size', 0)} bytes)")
                if doc.get('summary'):
                    print(f"     Summary: {doc.get('summary', '')[:100]}...")
            return True
        else:
            print(f"❌ Failed to get documents")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        traceback.print_exc()
        return False

def check_health():
    """Check if backend is healthy."""
    print_section("Health Check")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend is healthy")
            print(f"   Status: {data.get('status')}")
            print(f"   Database: {data.get('database', 'unknown')}")
            return True
        else:
            print(f"⚠️  Backend health check returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        print(f"   Make sure the backend is running on http://localhost:8000")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  Document Upload & Summarization Test Suite")
    print("=" * 70)
    
    # Health check
    if not check_health():
        print("\n❌ Backend not available. Exiting.")
        sys.exit(1)
    
    # Create context
    context_id = test_create_context()
    if not context_id:
        print("\n❌ Failed to create context. Exiting.")
        sys.exit(1)
    
    # Test upload with summarization (the problematic case)
    doc_id = test_upload_text_file(context_id)
    
    # Test upload without summarization
    if doc_id:
        test_summarize_document(doc_id)
    else:
        print("\n⚠️  Skipping summarization test due to upload failure")
    
    # Test upload without summary
    test_upload_without_summary(context_id)
    
    # Get documents
    test_get_documents(context_id)
    
    print_section("Test Suite Complete")
    print("\n" + "=" * 70)
    print("  Summary")
    print("=" * 70)
    print("\nCheck the output above for any errors.")
    print("If upload failed, check:")
    print("  1. Backend logs: docker logs nex-backend-dev --tail 100")
    print("  2. OpenAI API key is set (if summarization is enabled)")
    print("  3. Database is accessible")
    print("  4. Storage directory exists and is writable")
    print("\n")

if __name__ == "__main__":
    main()

