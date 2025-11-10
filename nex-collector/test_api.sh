#!/bin/bash
# Test script for NEX Context Aggregator API

API_URL="http://localhost:8080"
TOKEN="dev-secret"

echo "🧪 Testing NEX Context Aggregator API"
echo ""

echo "1️⃣ Health Check..."
curl -s "$API_URL/healthz"
echo ""
echo ""

echo "2️⃣ Create a Context Document..."
curl -X POST "$API_URL/v1/contexts" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"ctx-test-001","title":"Test Finance Context","version":"1.0.0","body_text":"This is a test context for financial analysis. When analyzing data, verify sources and check for anomalies.","metadata_json":{}}'
echo ""
echo ""

echo "3️⃣ Create a Variant..."
curl -X POST "$API_URL/v1/contexts/ctx-test-001/variants" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id":"var-test-001","context_id":"ctx-test-001","domain":"finance","persona":"CFO","task":"analyze","style":"formal","body_text":"This is a test context for financial analysis. When analyzing data, verify sources and check for anomalies.","constraints_json":{}}'
echo ""
echo ""

echo "4️⃣ Run Underwriting..."
curl -X POST "$API_URL/v1/underwrite/run?variant_id=var-test-001&rubric_id=default" \
  -H "Authorization: Bearer $TOKEN"
echo ""
echo ""

echo "5️⃣ Get Context..."
curl -s "$API_URL/v1/contexts/ctx-test-001" \
  -H "Authorization: Bearer $TOKEN"
echo ""
echo ""

echo "6️⃣ Get Variant..."
curl -s "$API_URL/v1/variants/var-test-001" \
  -H "Authorization: Bearer $TOKEN"
echo ""
echo ""

echo "✅ Test complete!"
echo ""
echo "View API docs at: $API_URL/docs"

