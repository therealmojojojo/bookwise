#!/bin/bash
# Test script for BookWise Librarian API

API_URL="${API_URL:-http://localhost:8766}"

echo "🧪 Testing BookWise Librarian API"
echo "=================================="
echo ""

# Test 1: Health Check
echo "1️⃣ Testing health check..."
curl -s "$API_URL/health" | python -m json.tool
echo ""
echo ""

# Test 2: Library Stats
echo "2️⃣ Testing library stats..."
curl -s "$API_URL/api/v1/stats" | python -m json.tool
echo ""
echo ""

# Test 3: Search Library
echo "3️⃣ Testing search_library..."
curl -s -X POST "$API_URL/api/v1/search_library" \
  -H "Content-Type: application/json" \
  -d '{
    "queries": ["resilience during hardship", "economic depression"],
    "quality_threshold": 70,
    "max_results": 5
  }' | python -m json.tool
echo ""
echo ""

# Test 4: Get Book Details
echo "4️⃣ Testing get_book_details (The Grapes of Wrath, Beloved, The Old Man and the Sea)..."
curl -s -X POST "$API_URL/api/v1/get_book_details" \
  -H "Content-Type: application/json" \
  -d '{
    "book_ids": [1834, 17306, 2781]
  }' | python -m json.tool
echo ""
echo ""

echo "✅ Tests complete!"
echo ""
echo "Visit $API_URL/docs for interactive API documentation"

