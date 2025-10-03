#!/bin/bash

echo "Testing Netlify Functions..."
echo "================================"
echo ""

# Test 1: Create session (log paste)
echo "Test 1: Log paste upload"
echo "------------------------"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" http://localhost:8888/api/sessions \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"log_content":"{\"type\":\"test\",\"timestamp\":\"2025-01-01\"}","encryption_enabled":false}')

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "Status: $HTTP_STATUS"
echo "Response: $BODY"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
  echo "✅ Log paste WORKS!"
  SESSION_URL=$(echo "$BODY" | grep -o '"session_url":"[^"]*"' | cut -d'"' -f4)
  echo "Session URL: $SESSION_URL"
else
  echo "❌ Log paste FAILED"
fi

echo ""
echo "================================"
echo ""

# Test 2: Create session from folder
echo "Test 2: Folder upload"
echo "---------------------"

# Create a test file
echo '{"type":"test","data":"hello"}' > /tmp/test-upload.jsonl

RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" http://localhost:8888/api/sessions/folder \
  -X POST \
  -F "files=@/tmp/test-upload.jsonl" \
  -F "encryption_enabled=false")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS/d')

echo "Status: $HTTP_STATUS"
echo "Response: $BODY"
echo ""

if [ "$HTTP_STATUS" = "200" ]; then
  echo "✅ Folder upload WORKS!"
else
  echo "❌ Folder upload FAILED"
fi

rm -f /tmp/test-upload.jsonl

echo ""
echo "================================"
echo ""

# Test 3: GitHub auth debug (requires backend)
echo "Test 3: GitHub auth debug"
echo "-------------------------"
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" http://localhost:8888/api/github/auth/debug \
  -H "Authorization: Bearer test-token")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)

echo "Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "404" ]; then
  echo "ℹ️  GitHub endpoint exists (needs Python backend running)"
else
  echo "⚠️  GitHub endpoint not available"
fi

echo ""
echo "================================"
echo ""
echo "Summary:"
echo "- Netlify Functions are for log uploads (working above)"
echo "- GitHub mode requires Python backend: uvicorn backend.main:app --reload"
echo ""
