#!/bin/bash
# Test script for document summarization
# Run this to test the summarization functionality

set -e

BASE_URL="http://localhost:8000"

echo "=========================================="
echo "Document Summarization Test Suite"
echo "=========================================="

echo ""
echo "1. Checking configuration..."
curl -s "$BASE_URL/health/config" | python3 -m json.tool || echo "⚠️  Config endpoint not available"

echo ""
echo "2. Creating test context..."
CONTEXT_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/contexts" \
  -H "Content-Type: application/json" \
  -d '{"name": "Summarization Test", "org_id": "demo"}')

CONTEXT_ID=$(echo "$CONTEXT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('context_id', ''))" 2>/dev/null || echo "")

if [ -z "$CONTEXT_ID" ]; then
  echo "❌ Failed to create context"
  exit 1
fi

echo "✅ Context created: $CONTEXT_ID"

echo ""
echo "3. Uploading test document..."
# Create test file
cat > /tmp/test_doc.txt << 'EOF'
This is a comprehensive test document for summarization.

It contains multiple paragraphs discussing various topics including artificial intelligence,
machine learning, and software development practices. The document provides enough content
for meaningful AI-powered summarization.

Artificial intelligence has transformed many industries, enabling automation of complex
tasks that were previously only possible through human intervention. Machine learning
algorithms can analyze vast amounts of data to identify patterns and make predictions.

Software development has evolved significantly with modern practices like agile
methodologies, continuous integration, and DevOps. These approaches have improved
collaboration, reduced time to market, and enhanced software quality.
EOF

UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/contexts/$CONTEXT_ID/documents" \
  -F "file=@/tmp/test_doc.txt" \
  -F "auto_summarize=false")

DOC_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('document_id', ''))" 2>/dev/null || echo "")

if [ -z "$DOC_ID" ]; then
  echo "❌ Failed to upload document"
  echo "Response: $UPLOAD_RESPONSE"
  exit 1
fi

echo "✅ Document uploaded: $DOC_ID"

echo ""
echo "4. Testing summarization..."
SUM_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/contexts/documents/$DOC_ID/summarize?style=concise")

echo "$SUM_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$SUM_RESPONSE"

# Cleanup
rm -f /tmp/test_doc.txt

echo ""
echo "=========================================="
echo "Test complete!"
echo "=========================================="

