# How to Run Summarization Tests

## Quick Start

### 1. Check Configuration (Verify API Key)
```bash
# Check if API key is loaded
docker exec nex-backend-dev bash -c "python3 -c 'from core.config import settings; import os; print(\"From settings:\", bool(settings.openai_api_key)); print(\"From env:\", bool(os.environ.get(\"OPENAI_API_KEY\")))'"

# Or use the API endpoint
curl http://localhost:8000/health/config
```

### 2. Run Unit Tests
```bash
docker exec nex-backend-dev bash -c "cd /app && python -m pytest tests/test_summarization.py -v"
```

**Expected**: All 12 tests should pass ✅

### 3. Run Full Integration Test
```bash
# Copy test file
docker cp test_summarization_full.py nex-backend-dev:/tmp/

# Run test
docker exec nex-backend-dev bash -c "cd /tmp && python3 test_summarization_full.py"
```

**This will test**:
- ✅ API key configuration
- ✅ Context creation
- ✅ Document upload
- ✅ Summarization
- ✅ Summary persistence

## Test Files Created

1. **`backend/tests/test_summarization.py`** - Unit tests (12 tests)
2. **`backend/tests/test_document_upload_summarization.py`** - Integration tests
3. **`test_summarization_full.py`** - E2E integration test script

## What the Tests Verify

✅ **API Key Loading**
- Loads from `settings.openai_api_key` 
- Loads from `OPENAI_API_KEY` environment variable
- Gracefully handles missing key

✅ **Summarization Logic**
- Text validation (min 50 chars)
- Text truncation (>3000 chars)
- Different styles (concise, detailed, bullet_points)
- Error handling

✅ **End-to-End Flow**
- Document upload
- Manual summarization
- Summary saving
- Error messages

## Troubleshooting

If tests fail:

1. **API Key Not Loading**:
   ```bash
   # Ensure .env file exists in project root
   cat .env | grep OPENAI
   
   # Restart backend
   docker-compose -f docker-compose.dev.yml restart backend
   ```

2. **Import Errors**:
   ```bash
   # Install pytest if needed
   docker exec nex-backend-dev bash -c "pip install pytest -q"
   ```

3. **Tests Fail**:
   - Check backend logs: `docker logs nex-backend-dev --tail 50`
   - Verify API key: `curl http://localhost:8000/health/config`

All tests are ready to use! 🎉

