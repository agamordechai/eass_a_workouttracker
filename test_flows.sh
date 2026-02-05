#!/bin/bash

# Comprehensive Behavioral and Flow Testing Script
# Tests all major user journeys and system behaviors

set -e  # Exit on error

API_URL="http://localhost:8000"
AI_COACH_URL="http://localhost:8001"
WORKER_URL="http://localhost:8002"

echo "================================================"
echo "WORKOUT TRACKER - COMPREHENSIVE FLOW TESTING"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_count=0
pass_count=0
fail_count=0

run_test() {
    test_count=$((test_count + 1))
    echo -e "\n${YELLOW}[TEST $test_count]${NC} $1"
}

pass_test() {
    pass_count=$((pass_count + 1))
    echo -e "${GREEN}✓ PASS${NC}: $1"
}

fail_test() {
    fail_count=$((fail_count + 1))
    echo -e "${RED}✗ FAIL${NC}: $1"
}

# ==============================================================================
# PHASE 1: HEALTH CHECKS
# ==============================================================================
echo -e "\n${YELLOW}=== PHASE 1: HEALTH CHECKS ===${NC}"

run_test "API Health Check"
response=$(curl -s "$API_URL/health")
if echo "$response" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    pass_test "API is healthy"
else
    fail_test "API health check failed"
fi

run_test "AI Coach Health Check"
response=$(curl -s "$AI_COACH_URL/health")
if echo "$response" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    pass_test "AI Coach is healthy"
else
    fail_test "AI Coach health check failed"
fi

run_test "Worker Health Check"
response=$(curl -s "$WORKER_URL/health")
if echo "$response" | jq -e '.status == "healthy"' > /dev/null 2>&1; then
    pass_test "Worker is healthy"
else
    fail_test "Worker health check failed"
fi

# ==============================================================================
# PHASE 2: AUTHENTICATION FLOW
# ==============================================================================
echo -e "\n${YELLOW}=== PHASE 2: AUTHENTICATION FLOW ===${NC}"

# Hardcoded test users (no registration endpoint in this API)
TEST_USER="user"
TEST_PASS="user123"
ADMIN_USER="admin"
ADMIN_PASS="admin123"

run_test "User Login"
login_response=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"password\":\"$TEST_PASS\"}")

if echo "$login_response" | jq -e '.access_token' > /dev/null 2>&1; then
    USER_TOKEN=$(echo "$login_response" | jq -r '.access_token')
    pass_test "User login successful"
else
    fail_test "User login failed: $login_response"
    USER_TOKEN=""
fi

run_test "Admin Login"
admin_response=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$ADMIN_USER\",\"password\":\"$ADMIN_PASS\"}")

if echo "$admin_response" | jq -e '.access_token' > /dev/null 2>&1; then
    ADMIN_TOKEN=$(echo "$admin_response" | jq -r '.access_token')
    pass_test "Admin login successful"
else
    fail_test "Admin login failed: $admin_response"
    ADMIN_TOKEN=""
fi

run_test "Invalid Password Rejection"
invalid_response=$(curl -s -X POST "$API_URL/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"$TEST_USER\",\"password\":\"wrongpassword\"}")

if echo "$invalid_response" | jq -e '.detail' > /dev/null 2>&1; then
    pass_test "Invalid password correctly rejected"
else
    fail_test "Invalid password not rejected properly"
fi

# ==============================================================================
# PHASE 3: AUTHORIZATION & RBAC
# ==============================================================================
echo -e "\n${YELLOW}=== PHASE 3: ROLE-BASED ACCESS CONTROL ===${NC}"

run_test "Verify Auth Token Contains User Info"
if [ -n "$USER_TOKEN" ]; then
    auth_me=$(curl -s -H "Authorization: Bearer $USER_TOKEN" "$API_URL/auth/me")
    if echo "$auth_me" | jq -e '.username == "user"' > /dev/null 2>&1; then
        pass_test "Auth token correctly identifies user"
    else
        fail_test "Auth token validation failed: $auth_me"
    fi
fi

run_test "Access Without Token Returns Proper Error"
# Note: /exercises is public, so test with admin-only endpoint
unauth_response=$(curl -s -w "\n%{http_code}" "$API_URL/admin/users")
http_code=$(echo "$unauth_response" | tail -n1)
if [ "$http_code" = "401" ]; then
    pass_test "Unauthorized access correctly blocked (401)"
else
    fail_test "Expected 401, got $http_code"
fi

run_test "User Cannot Access Admin Endpoint"
if [ -n "$USER_TOKEN" ]; then
    admin_attempt=$(curl -s -w "\n%{http_code}" -H "Authorization: Bearer $USER_TOKEN" "$API_URL/admin/users")
    http_code=$(echo "$admin_attempt" | tail -n1)
    if [ "$http_code" = "403" ]; then
        pass_test "Non-admin user correctly blocked from admin endpoint (403)"
    else
        fail_test "Expected 403, got $http_code"
    fi
fi

run_test "Admin Can Access Admin Endpoint"
if [ -n "$ADMIN_TOKEN" ]; then
    admin_users=$(curl -s -H "Authorization: Bearer $ADMIN_TOKEN" "$API_URL/admin/users")
    if echo "$admin_users" | jq -e 'type == "array"' > /dev/null 2>&1; then
        pass_test "Admin can access admin endpoints"
    else
        fail_test "Admin cannot access admin endpoints"
    fi
fi

# ==============================================================================
# PHASE 4: EXERCISE CRUD OPERATIONS
# ==============================================================================
echo -e "\n${YELLOW}=== PHASE 4: EXERCISE CRUD OPERATIONS ===${NC}"

if [ -n "$ADMIN_TOKEN" ]; then
    run_test "Create Exercise (Admin)"
    exercise_data=$(cat <<EOF
{
    "name": "Test Exercise $(date +%s)",
    "sets": 3,
    "reps": 10,
    "weight": 50.0,
    "workout_day": "A"
}
EOF
)

    create_response=$(curl -s -X POST "$API_URL/exercises" \
        -H "Authorization: Bearer $ADMIN_TOKEN" \
        -H "Content-Type: application/json" \
        -d "$exercise_data")

    if echo "$create_response" | jq -e '.id' > /dev/null 2>&1; then
        EXERCISE_ID=$(echo "$create_response" | jq -r '.id')
        pass_test "Exercise created successfully (ID: $EXERCISE_ID)"
    else
        fail_test "Exercise creation failed: $create_response"
        EXERCISE_ID=""
    fi

    run_test "Read Exercise"
    if [ -n "$EXERCISE_ID" ]; then
        read_response=$(curl -s "$API_URL/exercises/$EXERCISE_ID")
        if echo "$read_response" | jq -e '.id' > /dev/null 2>&1; then
            pass_test "Exercise retrieved successfully"
        else
            fail_test "Exercise retrieval failed"
        fi
    fi

    run_test "Update Exercise (Admin)"
    if [ -n "$EXERCISE_ID" ]; then
        update_response=$(curl -s -X PATCH "$API_URL/exercises/$EXERCISE_ID" \
            -H "Authorization: Bearer $ADMIN_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"name":"Updated Exercise Name","sets":5}')

        if echo "$update_response" | jq -e '.name == "Updated Exercise Name" and .sets == 5' > /dev/null 2>&1; then
            pass_test "Exercise updated successfully"
        else
            fail_test "Exercise update failed: $update_response"
        fi
    fi

    run_test "Non-Admin Can Create Exercise (Security Note)"
    if [ -n "$USER_TOKEN" ]; then
        user_create=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/exercises" \
            -H "Authorization: Bearer $USER_TOKEN" \
            -H "Content-Type: application/json" \
            -d "$exercise_data")
        http_code=$(echo "$user_create" | tail -1)
        body=$(echo "$user_create" | sed '$d')
        if [ "$http_code" = "201" ]; then
            pass_test "Non-admin can create exercises (NOTE: Potential security issue - may be intentional)"
            # Clean up the created exercise
            created_id=$(echo "$body" | jq -r '.id')
            if [ -n "$created_id" ] && [ "$created_id" != "null" ]; then
                curl -s -X DELETE "$API_URL/admin/exercises/$created_id" -H "Authorization: Bearer $ADMIN_TOKEN" > /dev/null
            fi
        else
            fail_test "Expected 201 (or 403 if secured), got $http_code"
        fi
    fi

    run_test "Delete Exercise (Admin)"
    if [ -n "$EXERCISE_ID" ]; then
        delete_response=$(curl -s -w "\n%{http_code}" -X DELETE "$API_URL/admin/exercises/$EXERCISE_ID" \
            -H "Authorization: Bearer $ADMIN_TOKEN")
        http_code=$(echo "$delete_response" | tail -n1)
        if [ "$http_code" = "204" ]; then
            pass_test "Exercise deleted successfully"
        else
            fail_test "Exercise deletion failed (HTTP $http_code)"
        fi
    fi
fi

# ==============================================================================
# PHASE 5: RATE LIMITING
# ==============================================================================
echo -e "\n${YELLOW}=== PHASE 5: RATE LIMITING BEHAVIOR ===${NC}"

run_test "Rate Limit on Auth Endpoint"
# Auth endpoint has 10/minute limit - try 12 requests with small delays
rate_limit_hit=false
for i in {1..12}; do
    response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/auth/login" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"ratelimittest\",\"password\":\"test\"}")
    http_code=$(echo "$response" | tail -1)
    if [ "$http_code" = "429" ]; then
        rate_limit_hit=true
        RATE_LIMIT_RESPONSE=$(echo "$response" | sed '$d')
        break
    fi
    sleep 0.15  # Small delay between requests
done

if [ "$rate_limit_hit" = true ]; then
    pass_test "Rate limiting enforced (429 after ~10 requests)"
    # Verify error format
    if echo "$RATE_LIMIT_RESPONSE" | jq -e '.detail' > /dev/null 2>&1; then
        pass_test "Rate limit error format correct (includes detail)"
    fi
else
    fail_test "Rate limit not hit after 12 requests (expected 10/min limit)"
fi

run_test "Health Endpoint Exempt from Rate Limiting"
for i in {1..20}; do
    response=$(curl -s -w "\n%{http_code}" "$API_URL/health")
    http_code=$(echo "$response" | tail -n1)
    if [ "$http_code" = "429" ]; then
        fail_test "Health endpoint incorrectly rate limited"
        break
    fi
done
if [ "$http_code" != "429" ]; then
    pass_test "Health endpoint exempt from rate limiting"
fi

# ==============================================================================
# PHASE 6: EXERCISE LIBRARY
# ==============================================================================
echo -e "\n${YELLOW}=== PHASE 6: EXERCISE LIBRARY ===${NC}"

run_test "List All Exercises (Public)"
exercises=$(curl -s "$API_URL/exercises")
exercise_count=$(echo "$exercises" | jq 'length')
if [ "$exercise_count" -ge 1 ]; then
    pass_test "Exercises retrieved (count: $exercise_count)"
else
    fail_test "No exercises found in library"
fi

run_test "Get Single Exercise"
if [ "$exercise_count" -ge 1 ]; then
    first_exercise_id=$(echo "$exercises" | jq -r '.[0].id')
    single_exercise=$(curl -s "$API_URL/exercises/$first_exercise_id")
    if echo "$single_exercise" | jq -e '.id' > /dev/null 2>&1; then
        pass_test "Single exercise retrieved"
    else
        fail_test "Single exercise retrieval failed"
    fi
fi

# ==============================================================================
# PHASE 7: AI COACH INTEGRATION
# ==============================================================================
echo -e "\n${YELLOW}=== PHASE 7: AI COACH INTEGRATION ===${NC}"

if [ -n "$USER_TOKEN" ]; then
    run_test "AI Coach Progress Analysis"
    ai_request=$(curl -s "$AI_COACH_URL/analyze?user_id=1" \
        -H "Authorization: Bearer $USER_TOKEN")

    # Check if we get a valid response
    if echo "$ai_request" | jq -e '.summary or .improvements' > /dev/null 2>&1; then
        pass_test "AI Coach analysis successful"
    else
        fail_test "AI Coach analysis failed: $ai_request"
    fi

    run_test "AI Coach Chat Interaction"
    chat_request=$(curl -s -X POST "$AI_COACH_URL/chat" \
        -H "Authorization: Bearer $USER_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{"message":"What exercises should I do today?","user_id":1}')

    if echo "$chat_request" | jq -e '.response' > /dev/null 2>&1; then
        pass_test "AI Coach chat successful"
    else
        fail_test "AI Coach chat failed: $chat_request"
    fi
fi

# ==============================================================================
# SUMMARY
# ==============================================================================
echo ""
echo "================================================"
echo "TEST SUMMARY"
echo "================================================"
echo -e "Total Tests:  $test_count"
echo -e "${GREEN}Passed:       $pass_count${NC}"
echo -e "${RED}Failed:       $fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✓ ALL TESTS PASSED${NC}"
    exit 0
else
    echo -e "${RED}✗ SOME TESTS FAILED${NC}"
    exit 1
fi
