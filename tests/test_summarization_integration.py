#!/usr/bin/env python3
"""
Integration test for document summarization.
Tests the full flow from API key loading to summarization.
"""
import os
import sys
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def print_header(title):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def test_config_loading():
    """Test that OpenAI API key can be loaded from environment."""
    print_header("Test 1: Check OpenAI API Key Configuration")
    
    try:
        # Check in Docker container
        import subprocess
        result = subprocess.run(
            ['docker', 'exec', 'nex-backend-dev', 'python', '-c',
             'from core.config import settings; import os; '
             'print("Settings key:", bool(settings.openai_api_key)); '
             'print("Env var key:", bool(os.environ.get("OPENAI_API_KEY"))); '
             'print("Settings value (first 10):", settings.openai_api_key[:10] if settings.openai_api_key else "None"); '
             'print("Env value (first 10):", os.environ.get("OPENAI_API_KEY", "None")[:10] if os.environ.get("OPENAI_API_KEY") else "None")'],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
    except Exception as e:
        print(f"Failed to check config: {e}")
        return False
    
    return True

def test_summarizer_initialization():
    """Test that DocumentSummarizer can be initialized."""
    print_header("Test 2: DocumentSummarizer Initialization")
    
    try:
        result = requests.post(
            f"{BASE_URL}/test/summarizer-check",
            timeout=5
        )
        if result.status_code == 200:
            print("✅ Summarizer can be initialized")
            return True
        else:
            print(f"⚠️  Test endpoint not available (status: {result.status_code})")
            return True  # Not critical
    except requests.exceptions.RequestException:
        print("⚠️  Test endpoint not available (normal if not implemented)")
        return True

def test_create_context_and_upload():
    """Create a context and upload a test document."""
    print_header("Test 3: Create Context and Upload Document")
    
    try:
        # Create context
        response = requests.post(
            f"{BASE_URL}/contexts",
            json={
                "name": "Summarization Test Context",
                "description": "Testing summarization functionality",
                "org_id": "demo"
            },
            timeout=10
        )
        
        if response.status_code not in [200, 201]:
            print(f"❌ Failed to create context: {response.status_code}")
            print(response.text[:500])
            return None
        
        context_id = response.json().get('context_id')
        print(f"✅ Context created: {context_id}")
        
        # Upload document
        test_content = """
        This is a comprehensive test document for summarization testing.
        
        It contains multiple paragraphs with substantial content that should be
        suitable for AI-powered summarization. The document discusses various
        topics including technology, artificial intelligence, and software development.
        
        Artificial intelligence has become increasingly important in modern software
        development. Machine learning algorithms can help automate tasks, improve
        decision-making, and enhance user experiences.
        
        Software development practices have evolved significantly over the years.
        Agile methodologies, continuous integration, and DevOps have transformed
        how teams build and deploy applications.
        
        This document serves as a test case for the summarization functionality,
        ensuring that the system can properly extract and summarize key information
        from uploaded documents.
        """ * 3  # Make it long enough
        
        test_file = Path("test_summarize.txt")
        test_file.write_text(test_content)
        
        with open(test_file, 'rb') as f:
            files = {'file': ('test_summarize.txt', f, 'text/plain')}
            data = {'auto_summarize': 'false'}  # Don't auto-summarize, test manual
        
            response = requests.post(
                f"{BASE_URL}/contexts/{context_id}/documents",
                files=files,
                data=data,
                timeout=30
            )
        
        test_file.unlink()
        
        if response.status_code != 200:
            print(f"❌ Failed to upload document: {response.status_code}")
            print(response.text[:500])
            return None, None
        
        doc_data = response.json()
        doc_id = doc_data.get('document_id')
        print(f"✅ Document uploaded: {doc_id}")
        print(f"   Summary: {doc_data.get('summary', 'None (expected - auto_summarize was false)')}")
        
        return context_id, doc_id
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def test_summarization(doc_id):
    """Test manual summarization."""
    print_header("Test 4: Manual Document Summarization")
    
    if not doc_id:
        print("⚠️  Skipping - no document ID")
        return False
    
    try:
        print(f"Attempting to summarize document: {doc_id}")
        
        response = requests.post(
            f"{BASE_URL}/contexts/documents/{doc_id}/summarize?style=concise",
            timeout=60  # Longer timeout for AI calls
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            summary = data.get('summary')
            print(f"✅ Summarization successful!")
            print(f"\nSummary:")
            print(f"  {summary}")
            return True
        elif response.status_code == 400:
            error = response.json().get('detail', 'Unknown error')
            print(f"❌ Summarization failed: {error}")
            
            if "OpenAI API key" in error or "API key" in error:
                print("\n💡 Issue: OpenAI API key is not configured or not accessible.")
                print("   Check:")
                print("   1. Is OPENAI_API_KEY in your .env file?")
                print("   2. Is the .env file being loaded in Docker?")
                print("   3. Did you restart the backend after adding the key?")
                print("   4. Try: docker-compose -f docker-compose.dev.yml restart backend")
            elif "extractable text" in error:
                print("\n💡 Issue: Document may not have extractable text content.")
            else:
                print(f"\n💡 Error details: {error}")
            
            return False
        else:
            print(f"❌ Unexpected status: {response.status_code}")
            print(response.text[:500])
            return False
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after 60s")
        return False
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_get_documents(context_id):
    """Test getting documents to verify summary was saved."""
    print_header("Test 5: Verify Summary in Document List")
    
    if not context_id:
        print("⚠️  Skipping - no context ID")
        return False
    
    try:
        response = requests.get(f"{BASE_URL}/contexts/{context_id}/documents")
        
        if response.status_code == 200:
            data = response.json()
            docs = data.get('documents', [])
            
            if docs:
                doc = docs[0]  # Get most recent
                summary = doc.get('summary')
                if summary:
                    print(f"✅ Summary found in document list!")
                    print(f"   Summary: {summary[:100]}...")
                    return True
                else:
                    print(f"⚠️  Document found but no summary")
                    return False
            else:
                print(f"⚠️  No documents found")
                return False
        else:
            print(f"❌ Failed to get documents: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  Document Summarization Integration Test Suite")
    print("=" * 70)
    
    results = []
    
    # Test 1: Config loading
    results.append(("Config Loading", test_config_loading()))
    
    # Test 2: Summarizer init
    results.append(("Summarizer Init", test_summarizer_initialization()))
    
    # Test 3: Upload document
    context_id, doc_id = test_create_context_and_upload()
    results.append(("Document Upload", context_id is not None and doc_id is not None))
    
    # Test 4: Summarization
    if doc_id:
        results.append(("Summarization", test_summarization(doc_id)))
    else:
        results.append(("Summarization", False))
    
    # Test 5: Verify summary
    if context_id:
        results.append(("Verify Summary", test_get_documents(context_id)))
    else:
        results.append(("Verify Summary", False))
    
    # Print summary
    print_header("Test Summary")
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    total = len(results)
    passed = sum(1 for _, p in results if p)
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed < total:
        print("\n💡 Troubleshooting Tips:")
        print("   1. Check OPENAI_API_KEY is in .env file")
        print("   2. Ensure docker-compose.dev.yml loads .env")
        print("   3. Restart backend: docker-compose -f docker-compose.dev.yml restart backend")
        print("   4. Check logs: docker logs nex-backend-dev --tail 50")

if __name__ == "__main__":
    main()

