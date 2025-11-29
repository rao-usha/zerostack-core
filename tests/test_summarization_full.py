#!/usr/bin/env python3
"""
Comprehensive test suite for document summarization.
Tests configuration, upload, and summarization flow.
"""
import requests
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"

def test_config():
    """Test 1: Check OpenAI API key configuration."""
    print("\n" + "=" * 70)
    print("Test 1: OpenAI API Key Configuration")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/health/config", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Config endpoint accessible")
            print(f"   API Key configured: {data.get('openai_api_key_configured')}")
            print(f"   From settings: {data.get('from_settings')}")
            print(f"   From environment: {data.get('from_env')}")
            print(f"   Key preview: {data.get('key_preview', 'N/A')}")
            
            if not data.get('openai_api_key_configured'):
                print("\n⚠️  WARNING: OpenAI API key is NOT configured!")
                print("   Please add OPENAI_API_KEY to your .env file and restart backend:")
                print("   docker-compose -f docker-compose.dev.yml restart backend")
                return False
            return True
        else:
            print(f"❌ Config endpoint returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Failed to check config: {e}")
        return False

def test_create_context():
    """Test 2: Create a test context."""
    print("\n" + "=" * 70)
    print("Test 2: Create Test Context")
    print("=" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/contexts",
            json={
                "name": "Summarization Test Context",
                "description": "Testing AI summarization",
                "org_id": "demo"
            },
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            context_id = data.get('context_id')
            print(f"✅ Context created: {context_id}")
            return context_id
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text[:300])
            return None
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

def test_upload_document(context_id):
    """Test 3: Upload a test document."""
    print("\n" + "=" * 70)
    print("Test 3: Upload Test Document")
    print("=" * 70)
    
    # Create test document
    test_content = """
This is a comprehensive test document for AI-powered summarization testing.

The document covers multiple topics and provides substantial content that is suitable
for testing the summarization functionality. It discusses artificial intelligence,
machine learning algorithms, and their applications in modern software development.

Artificial intelligence has become increasingly important in recent years, transforming
how we approach problem-solving and automation. Machine learning enables computers to
learn from data without being explicitly programmed for every scenario.

Software development practices have evolved significantly with agile methodologies,
continuous integration, and DevOps approaches. These modern practices improve
collaboration, reduce time to market, and enhance overall software quality.

This document serves as a test case to verify that the summarization system can
properly extract and condense key information from uploaded documents using
OpenAI's language models.
""" * 2
    
    test_file = Path("test_summarize_doc.txt")
    test_file.write_text(test_content)
    
    try:
        with open(test_file, 'rb') as f:
            files = {'file': ('test_summarize_doc.txt', f, 'text/plain')}
            data = {'auto_summarize': 'false'}  # Test manual summarization
            
            print(f"Uploading to context: {context_id}")
            response = requests.post(
                f"{BASE_URL}/api/v1/contexts/{context_id}/documents",
                files=files,
                data=data,
                timeout=30
            )
        
        test_file.unlink()
        
        if response.status_code == 200:
            doc_data = response.json()
            doc_id = doc_data.get('document_id')
            print(f"✅ Document uploaded: {doc_id}")
            print(f"   File size: {doc_data.get('file_size')} bytes")
            print(f"   Initial summary: {doc_data.get('summary', 'None (expected)')}")
            return doc_id
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(response.text[:500])
            return None
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_summarization(doc_id):
    """Test 4: Test document summarization."""
    print("\n" + "=" * 70)
    print("Test 4: Document Summarization")
    print("=" * 70)
    
    if not doc_id:
        print("⚠️  Skipping - no document ID")
        return False
    
    print(f"Summarizing document: {doc_id}")
    print("Waiting for API response...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/contexts/documents/{doc_id}/summarize?style=concise",
            timeout=60
        )
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary')
            print(f"\n✅ SUCCESS! Summary generated:")
            print(f"\n{'=' * 70}")
            print(summary)
            print(f"{'=' * 70}\n")
            return True
            
        elif response.status_code == 400:
            error = response.json().get('detail', 'Unknown error')
            print(f"\n❌ Summarization failed (400 Bad Request)")
            print(f"Error: {error}\n")
            
            if "OpenAI API key" in error or "API key" in error:
                print("🔧 DIAGNOSTICS:")
                print("   The error suggests the OpenAI API key is not configured.")
                print("\n   To fix:")
                print("   1. Create/edit .env file in project root:")
                print("      OPENAI_API_KEY=sk-your-key-here")
                print("   2. Restart backend:")
                print("      docker-compose -f docker-compose.dev.yml restart backend")
                print("   3. Verify key is loaded:")
                print("      curl http://localhost:8000/health/config")
            return False
            
        else:
            print(f"\n❌ Unexpected status: {response.status_code}")
            print(response.text[:500])
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timed out (60s)")
        return False
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_documents(context_id):
    """Test 5: Verify summary is saved."""
    print("\n" + "=" * 70)
    print("Test 5: Verify Summary Saved")
    print("=" * 70)
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/contexts/{context_id}/documents")
        
        if response.status_code == 200:
            data = response.json()
            docs = data.get('documents', [])
            
            if docs:
                doc = docs[0]
                summary = doc.get('summary')
                if summary:
                    print(f"✅ Summary found in document!")
                    print(f"   Document: {doc.get('name')}")
                    print(f"   Summary: {summary[:150]}...")
                    return True
                else:
                    print(f"⚠️  Document found but no summary yet")
                    return False
            else:
                print(f"⚠️  No documents found")
                return False
        else:
            print(f"❌ Failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  Document Summarization Test Suite")
    print("=" * 70)
    
    # Test 1: Config
    config_ok = test_config()
    if not config_ok:
        print("\n⚠️  Config test failed. Fix API key configuration before continuing.")
        print("   Run: docker-compose -f docker-compose.dev.yml restart backend")
        return
    
    # Test 2: Create context
    context_id = test_create_context()
    if not context_id:
        print("\n❌ Failed to create context")
        return
    
    # Test 3: Upload
    doc_id = test_upload_document(context_id)
    if not doc_id:
        print("\n❌ Failed to upload document")
        return
    
    # Test 4: Summarization
    summary_ok = test_summarization(doc_id)
    
    # Test 5: Verify
    verify_ok = test_get_documents(context_id)
    
    # Summary
    print("\n" + "=" * 70)
    print("  Test Summary")
    print("=" * 70)
    print(f"Config:       {'✅' if config_ok else '❌'}")
    print(f"Context:      {'✅' if context_id else '❌'}")
    print(f"Upload:       {'✅' if doc_id else '❌'}")
    print(f"Summarization: {'✅' if summary_ok else '❌'}")
    print(f"Verification:  {'✅' if verify_ok else '❌'}")
    
    if summary_ok:
        print("\n🎉 All tests passed! Summarization is working correctly.")
    else:
        print("\n⚠️  Summarization failed. Check error messages above.")

if __name__ == "__main__":
    main()

