#!/bin/bash
API_URL="http://localhost:8000"

echo "=== Testing Workout Tracker API ==="

# Test 1: Root endpoint
echo -e "\n1. Testing root endpoint..."
curl -s $API_URL/ | jq

# Test 2: Get all exercises
echo -e "\n2. Getting all exercises..."
curl -s $API_URL/exercises | jq

# Test 3: Create new exercise
echo -e "\n3. Creating new exercise..."
curl -s -X POST $API_URL/exercises \
  -H "Content-Type: application/json" \
  -d '{"name":"Barbell Row","sets":4,"reps":10,"weight":80.0}' | jq

# Test 4: Get specific exercise
echo -e "\n4. Getting exercise #1..."
curl -s $API_URL/exercises/1 | jq

# Test 5: Update exercise
echo -e "\n5. Updating exercise #1..."
curl -s -X PATCH $API_URL/exercises/1 \
  -H "Content-Type: application/json" \
  -d '{"weight":100.0}' | jq

# Test 6: Delete exercise (optional - commented out to preserve data)
# echo -e "\n6. Deleting exercise..."
# curl -s -X DELETE $API_URL/exercises/7 | jq

echo -e "\n=== Tests Complete ==="
echo -e "\nNote: If 'jq' is not installed, remove '| jq' from commands"

