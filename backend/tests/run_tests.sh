#!/bin/bash
# Test runner script for Files feature

set -e

echo "===================="
echo "Files Feature Tests"
echo "===================="
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "pytest not found. Installing..."
    pip install pytest pytest-cov pytest-mock
fi

# Change to backend directory
cd "$(dirname "$0")/.."

echo -e "${BLUE}Running all tests...${NC}"
pytest tests/ -v

echo ""
echo -e "${BLUE}Running tests with coverage...${NC}"
pytest --cov=domains.files --cov-report=term --cov-report=html tests/

echo ""
echo -e "${GREEN}✓ Tests complete!${NC}"
echo ""
echo "Coverage report generated in: backend/htmlcov/index.html"
echo ""
echo "To run specific test categories:"
echo "  Unit tests only:       pytest -m 'not integration' tests/"
echo "  Integration tests:     pytest -m integration tests/"
echo "  Specific file:         pytest tests/test_files_models.py"
echo "  With verbose output:   pytest -vv tests/"
