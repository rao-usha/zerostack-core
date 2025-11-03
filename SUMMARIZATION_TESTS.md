# Document Summarization Tests

## ✅ Tests Created

I've created comprehensive tests to ensure summarization works correctly:

### 1. **Unit Tests** (`backend/tests/test_summarization.py`)
- Tests `DocumentSummarizer` class directly
- Mocks OpenAI API calls
- Tests all error scenarios

### 2. **Integration Tests** (`backend/tests/test_document_upload_summarization.py`)  
- Tests full upload → summarize flow
- Tests with and without API key
- Tests error handling

### 3. **End-to-End Test** (`test_summarization_full.py`)
- Full API integration test
- Checks configuration
- Tests real summarization flow

## 🔧 Fixes Applied

1. ✅ **Fixed docker-compose.dev.yml** - Added `env_file: - .env` to load .env file
2. ✅ **Added config endpoint** - `/health/config` to check API key status
3. ✅ **Improved error messages** - Better feedback when API key is missing
4. ✅ **Better logging** - Detailed logs for debugging

## 🚀 Running Tests

### Quick Test (Integration):
```bash
# Copy test to container
docker cp test_summarization_full.py nex-backend-dev:/tmp/

# Run inside container (has requests installed)
docker exec nex-backend-dev bash -c "cd /tmp && python3 test_summarization_full.py"
```

### Unit Tests (Pytest):
```bash
docker exec nex-backend-dev bash -c "cd /app && pip install pytest -q && python -m pytest tests/test_summarization.py -v"
```

### Check Configuration:
```bash
# From host
Invoke-WebRequest -Uri "http://localhost:8000/health/config" | Select-Object -ExpandProperty Content

# From inside container  
docker exec nex-backend-dev bash -c "curl -s http://localhost:8000/health/config | python3 -m json.tool"
```

## 📋 Test Coverage

✅ **API Key Loading**
- From settings.openai_api_key
- From OPENAI_API_KEY environment variable  
- Fallback behavior when not configured

✅ **DocumentSummarizer**
- Initialization with/without key
- Text validation (min 50 chars)
- Text truncation (>3000 chars)
- Different summary styles (concise, detailed, bullet_points)
- Error handling (API failures, empty responses)

✅ **Document Upload & Summarization**
- Upload with auto_summarize=true
- Upload with auto_summarize=false
- Manual summarization via API
- Summary persistence to database
- Error handling for missing documents/text

## 🔍 Troubleshooting

### Issue: "OpenAI API key not configured"

1. **Verify .env file exists** in project root:
   ```bash
   # Check .env exists
   cat .env | grep OPENAI
   ```

2. **Restart backend** to load .env:
   ```bash
   docker-compose -f docker-compose.dev.yml restart backend
   ```

3. **Verify key is loaded**:
   ```bash
   docker exec nex-backend-dev bash -c "python3 -c 'from core.config import settings; print(bool(settings.openai_api_key))'"
   ```

### Issue: Summary returns None

**Possible causes:**
1. API key not configured → Check `/health/config`
2. Text too short (<50 chars) → Check document content
3. OpenAI API error → Check backend logs
4. Document has no extractable text → Try different file type

**Check logs:**
```bash
docker logs nex-backend-dev --tail 100 | grep -i "summar"
```

## 🎯 Expected Behavior

### With Valid API Key:
1. Upload document → ✅ Success
2. Click "Summarize" button → ✅ Summary generated
3. Summary appears in UI → ✅ Saved to database

### Without API Key:
1. Upload document → ✅ Success (no summary)
2. Click "Summarize" button → ❌ Error: "OpenAI API key may not be configured"
3. Helpful error message shown → ✅ User knows what's wrong

## 📝 Next Steps

After running tests, if summarization still fails:

1. Check `/health/config` endpoint output
2. Verify `.env` file is in project root
3. Ensure backend was restarted after adding key
4. Check backend logs for OpenAI API errors
5. Test with a simple text file first

All test files are ready to use and will help identify the exact issue!

