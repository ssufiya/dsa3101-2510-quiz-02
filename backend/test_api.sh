#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=========================================="
echo "QuizBank API Test Script"
echo "=========================================="
echo ""

# Test 1: Check if containers are running
echo -e "${YELLOW}Test 1: Checking Docker containers...${NC}"
if docker-compose ps | grep -q "Up"; then
    echo -e "${GREEN}✓ Containers are running${NC}"
else
    echo -e "${RED}✗ Containers are not running. Run: docker-compose up -d${NC}"
    exit 1
fi
echo ""

# Test 2: Check API root endpoint
echo -e "${YELLOW}Test 2: Testing API root endpoint...${NC}"
RESPONSE=$(curl -s http://localhost:5003/)
if echo "$RESPONSE" | grep -q "Quiz Bank API"; then
    echo -e "${GREEN}✓ API is accessible${NC}"
    echo "Response: $RESPONSE"
else
    echo -e "${RED}✗ API is not responding${NC}"
    echo "Response: $RESPONSE"
fi
echo ""

# Test 3: Check Swagger docs
echo -e "${YELLOW}Test 3: Checking Swagger UI...${NC}"
SWAGGER=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5003/docs)
if [ "$SWAGGER" = "200" ]; then
    echo -e "${GREEN}✓ Swagger UI is accessible at http://localhost:5003/docs${NC}"
else
    echo -e "${RED}✗ Swagger UI is not accessible (HTTP $SWAGGER)${NC}"
fi
echo ""

# Test 4: Test GET /api/questions
echo -e "${YELLOW}Test 4: Testing GET /api/questions...${NC}"
QUESTIONS=$(curl -s http://localhost:5003/api/questions)
if echo "$QUESTIONS" | grep -q "success"; then
    echo -e "${GREEN}✓ GET /api/questions works${NC}"
    echo "Response: $QUESTIONS" | head -c 200
    echo "..."
else
    echo -e "${RED}✗ GET /api/questions failed${NC}"
    echo "Response: $QUESTIONS"
fi
echo ""

# Test 5: Check database connection
echo -e "${YELLOW}Test 5: Testing database connection...${NC}"
DB_TEST=$(docker-compose exec -T db psql -U postgres -d quizbank -c "SELECT 1;" 2>&1)
if echo "$DB_TEST" | grep -q "1 row"; then
    echo -e "${GREEN}✓ Database connection successful${NC}"
else
    echo -e "${RED}✗ Database connection failed${NC}"
    echo "Error: $DB_TEST"
fi
echo ""

# Test 6: Check if tables exist
echo -e "${YELLOW}Test 6: Checking database tables...${NC}"
TABLES=$(docker-compose exec -T db psql -U postgres -d quizbank -c "\dt" 2>&1)
if echo "$TABLES" | grep -q "questions"; then
    echo -e "${GREEN}✓ Required tables exist${NC}"
    echo "$TABLES"
else
    echo -e "${RED}✗ Tables might be missing. Check initialization scripts.${NC}"
    echo "$TABLES"
fi
echo ""

# Summary
echo "=========================================="
echo -e "${GREEN}Testing Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Open Swagger UI: http://localhost:5003/docs"
echo "2. Test API endpoints interactively"
echo "3. Upload a test CSV file"
echo ""
echo "For logs, run: docker-compose logs -f backend"