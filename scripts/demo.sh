#!/bin/bash
#
# Workout Tracker Demo Script
# ============================
# This script demonstrates the full functionality of the Workout Tracker application.
# It starts the services, verifies health, and walks through key features.
#
# Usage: ./scripts/demo.sh
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
API_URL="http://localhost:8000"
AI_COACH_URL="http://localhost:8001"
FRONTEND_URL="http://localhost:3000"

# Helper functions
print_header() {
    echo ""
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}============================================================${NC}"
    echo ""
}

print_step() {
    echo -e "${CYAN}➜ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1

    print_step "Waiting for $name to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            print_success "$name is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    print_error "$name failed to start"
    return 1
}

# Main demo flow
print_header "Workout Tracker Demo"

echo "This demo will:"
echo "  1. Start all services via Docker Compose"
echo "  2. Verify health of all services"
echo "  3. Demonstrate the REST API"
echo "  4. Show authentication flow"
echo "  5. Demonstrate the AI Coach"
echo "  6. Open the Streamlit dashboard"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Step 1: Start services
print_header "Step 1: Starting Services"
print_step "Running docker compose up -d..."
docker compose up -d

# Step 2: Wait for services
print_header "Step 2: Verifying Services"
wait_for_service "$API_URL/health" "Workout API"
wait_for_service "$AI_COACH_URL/health" "AI Coach"

# Step 3: Demonstrate API
print_header "Step 3: REST API Demo"

print_step "Checking API health..."
curl -s "$API_URL/health" | python3 -m json.tool
echo ""

print_step "Fetching all exercises..."
EXERCISES=$(curl -s "$API_URL/exercises")
echo "$EXERCISES" | python3 -m json.tool
echo ""

# Create a sample exercise
print_step "Creating a new exercise (Demo Squat)..."
NEW_EXERCISE=$(curl -s -X POST "$API_URL/exercises" \
    -H "Content-Type: application/json" \
    -d '{"name": "Demo Squat", "sets": 4, "reps": 10, "weight": 100.0, "workout_day": "A"}')
echo "$NEW_EXERCISE" | python3 -m json.tool
EXERCISE_ID=$(echo "$NEW_EXERCISE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
print_success "Created exercise with ID: $EXERCISE_ID"
echo ""

# Step 4: Authentication demo
print_header "Step 4: Authentication Demo"

print_step "Logging in as 'user'..."
TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "user", "password": "user123"}')
ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
print_success "Obtained access token"
echo ""

print_step "Accessing protected endpoint /auth/me..."
curl -s "$API_URL/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN" | python3 -m json.tool
echo ""

print_step "Trying to access admin endpoint as regular user (should fail)..."
ADMIN_RESPONSE=$(curl -s -w "\n%{http_code}" "$API_URL/admin/users" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
HTTP_CODE=$(echo "$ADMIN_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$ADMIN_RESPONSE" | head -n-1)
if [ "$HTTP_CODE" = "403" ]; then
    print_success "Correctly denied! Role-based access control is working."
    echo "$RESPONSE_BODY" | python3 -m json.tool
else
    print_warning "Unexpected response code: $HTTP_CODE"
fi
echo ""

print_step "Logging in as 'admin'..."
ADMIN_TOKEN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username": "admin", "password": "admin123"}')
ADMIN_TOKEN=$(echo "$ADMIN_TOKEN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
print_success "Obtained admin access token"
echo ""

print_step "Accessing admin endpoint as admin..."
curl -s "$API_URL/admin/users" \
    -H "Authorization: Bearer $ADMIN_TOKEN" | python3 -m json.tool
print_success "Admin access granted!"
echo ""

# Step 5: AI Coach demo
print_header "Step 5: AI Coach Demo"

print_step "Checking AI Coach health..."
curl -s "$AI_COACH_URL/health" | python3 -m json.tool
echo ""

print_step "Asking AI Coach for workout recommendations..."
echo "(Note: This requires ANTHROPIC_API_KEY to be set)"
AI_RESPONSE=$(curl -s -X POST "$AI_COACH_URL/chat" \
    -H "Content-Type: application/json" \
    -d '{"message": "What exercises should I add for chest day?"}' 2>/dev/null || echo '{"error": "AI Coach requires API key"}')
echo "$AI_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$AI_RESPONSE"
echo ""

# Cleanup demo exercise
print_header "Step 6: Cleanup"
print_step "Deleting demo exercise..."
curl -s -X DELETE "$API_URL/exercises/$EXERCISE_ID"
print_success "Demo exercise deleted"
echo ""

# Step 7: Open interfaces
print_header "Step 7: Access Interfaces"

echo "Services are running at:"
echo ""
echo -e "  ${GREEN}Workout API:${NC}        $API_URL"
echo -e "  ${GREEN}API Documentation:${NC}  $API_URL/docs"
echo -e "  ${GREEN}AI Coach:${NC}           $AI_COACH_URL"
echo -e "  ${GREEN}React Frontend:${NC}     $FRONTEND_URL"
echo ""

# Try to open React frontend in browser
print_step "Opening React Frontend in browser..."
if command -v open &> /dev/null; then
    open "$FRONTEND_URL" 2>/dev/null || print_warning "Could not open browser automatically"
elif command -v xdg-open &> /dev/null; then
    xdg-open "$FRONTEND_URL" 2>/dev/null || print_warning "Could not open browser automatically"
else
    print_warning "Open $FRONTEND_URL in your browser to view the React Frontend"
fi

print_header "Demo Complete!"

echo "To stop all services:"
echo "  docker compose down"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
echo "To run the async refresh script:"
echo "  uv run python scripts/refresh.py"
echo ""
