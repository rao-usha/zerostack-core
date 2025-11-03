# Document Summarization Tests

This document describes the test suite for document summarization functionality.

## Quick Test

Run the comprehensive integration test:

```bash
# Copy test to container
docker cp test_summarization_full.py nex-backend-dev:/tmp/

# Run test
docker exec nex-backend-dev bash -c "cd /tmp && python3 test_summarization_full.py"
```

## Test Files Created

### 1. `backend/tests/test_summarization.py`
**Unit tests** for `DocumentSummarizer`:
- ✅ Initialization with API key from settings
- ✅ Initialization with API key from environment
- ✅ Initialization without API key (should disable)
- ✅ Summarization with different styles
- ✅ Text truncation for long documents
- ✅ Error handling for API failures
- ✅ Empty response handling

### 2. `backend/tests/test_document_upload_summarization.py`
**Integration tests** for document upload and summarization:
- ✅ Upload with auto-summarization
- ✅ Upload without summarization
- ✅ Manual summarization
- ✅ Document not found handling
- ✅ Documents without extractable text

### 3. `test_summarization_full.py`
**End-to-end integration test** (runnable script):
- ✅ Checks OpenAI API key configuration
- ✅ Creates test context
- ✅ Uploads test document
- ✅ Tests manual summarization
- ✅ Verifies summary is saved

## Running Unit Tests

```bash
# Run unit tests
docker exec nex-backend-dev bash -c "cd /app && python -m pytest tests/test_summarization.py -v"

# Run integration tests
docker exec nex-backend-dev bash -c "cd /app && python -m pytest tests/test_document_upload_summarization.py -v"
```

## Configuration Issues Fixed

### Issue: OpenAI API key not loading from .env

**Solution**: Updated `docker-compose.dev.yml` to:
1. Load `.env` file via `env_file`
2. Pass `OPENAI_API_KEY` explicitly via environment

**To apply**:
```bash
docker-compose -f docker-compose.dev.yml restart backend
```

**Verify**:
```bash
curl http://localhost:8000/health/config
```

## Test Coverage

✅ API key loading (settings + environment)  
✅ DocumentSummarizer initialization  
✅ Text validation (length, content)  
✅ Summarization with different styles  
✅ Error handling (no key, API errors, missing text)  
✅ Document upload with/without auto-summarization  
✅ Manual summarization endpoint  
✅ Summary persistence  

## Common Issues & Solutions

### Issue: "OpenAI API key not configured"
- **Check**: `.env` file exists with `OPENAI_API_KEY=sk-...`
- **Fix**: Restart backend after adding key
- **Verify**: `curl http://localhost:8000/health/config`

### Issue: "Could not generate summary"
- **Check**: Document has extractable text (>50 chars)
- **Check**: OpenAI API key is valid
- **Check**: Backend logs for API errors

### Issue: Summary returns None
- **Check**: OpenAI API key is configured
- **Check**: Text is long enough (>50 chars)
- **Check**: OpenAI API is accessible (no network issues)

