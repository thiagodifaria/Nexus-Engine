#!/bin/bash
# Test Runner Script - Nexus Engine
# Implementei este script para executar testes com diferentes configurações
# Decidi incluir opções para unit, integration, coverage, e performance tests

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Nexus Engine Test Runner${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    print_error "pytest not found. Please install: pip install pytest pytest-cov pytest-xdist"
    exit 1
fi

print_info "Project Root: $PROJECT_ROOT"
cd "$PROJECT_ROOT"

# Parse arguments
TEST_TYPE="all"
COVERAGE=false
PARALLEL=false
VERBOSE=false
MARKERS=""
SPECIFIC_FILE=""
STOP_ON_FAIL=false
LAST_FAILED=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            TEST_TYPE="unit"
            MARKERS="unit"
            shift
            ;;
        --integration)
            TEST_TYPE="integration"
            MARKERS="integration"
            shift
            ;;
        --e2e)
            TEST_TYPE="e2e"
            MARKERS="e2e"
            shift
            ;;
        --fast)
            MARKERS="fast"
            shift
            ;;
        --slow)
            MARKERS="slow"
            shift
            ;;
        --critical)
            MARKERS="critical"
            shift
            ;;
        --coverage)
            COVERAGE=true
            shift
            ;;
        --parallel)
            PARALLEL=true
            shift
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --file)
            SPECIFIC_FILE="$2"
            shift 2
            ;;
        --stop-on-fail)
            STOP_ON_FAIL=true
            shift
            ;;
        --last-failed)
            LAST_FAILED=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Test Types:"
            echo "  --unit               Run only unit tests"
            echo "  --integration        Run only integration tests"
            echo "  --e2e                Run only end-to-end tests"
            echo "  --fast               Run only fast tests"
            echo "  --slow               Run only slow tests"
            echo "  --critical           Run only critical tests"
            echo ""
            echo "Options:"
            echo "  --coverage           Generate coverage report"
            echo "  --parallel           Run tests in parallel (requires pytest-xdist)"
            echo "  --verbose            Enable verbose output"
            echo "  --file <path>        Run specific test file"
            echo "  --stop-on-fail       Stop on first failure"
            echo "  --last-failed        Run only tests that failed last time"
            echo "  --help               Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --unit --coverage"
            echo "  $0 --integration --parallel"
            echo "  $0 --file scripts/tests/unit/test_market_data_service.py"
            echo "  $0 --last-failed --stop-on-fail"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

# Add verbosity
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
fi

# Add markers
if [ -n "$MARKERS" ]; then
    PYTEST_CMD="$PYTEST_CMD -m $MARKERS"
fi

# Add specific file
if [ -n "$SPECIFIC_FILE" ]; then
    PYTEST_CMD="$PYTEST_CMD $SPECIFIC_FILE"
fi

# Add coverage
if [ "$COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=backend/python/src --cov=frontend/src"
    PYTEST_CMD="$PYTEST_CMD --cov-report=html:coverage_html"
    PYTEST_CMD="$PYTEST_CMD --cov-report=term-missing"
    PYTEST_CMD="$PYTEST_CMD --cov-report=json:coverage.json"
fi

# Add parallel execution
if [ "$PARALLEL" = true ]; then
    if ! command -v pytest-xdist &> /dev/null; then
        print_warning "pytest-xdist not found. Running sequentially."
        print_info "Install with: pip install pytest-xdist"
    else
        NUM_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
        PYTEST_CMD="$PYTEST_CMD -n $NUM_CORES"
    fi
fi

# Add stop on fail
if [ "$STOP_ON_FAIL" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -x"
fi

# Add last failed
if [ "$LAST_FAILED" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --lf"
fi

# Print configuration
echo -e "${CYAN}Test Configuration:${NC}"
print_info "Test Type: $TEST_TYPE"
[ -n "$MARKERS" ] && print_info "Markers: $MARKERS"
[ "$COVERAGE" = true ] && print_info "Coverage: Enabled"
[ "$PARALLEL" = true ] && print_info "Parallel: Enabled"
[ "$VERBOSE" = true ] && print_info "Verbose: Enabled"
[ -n "$SPECIFIC_FILE" ] && print_info "File: $SPECIFIC_FILE"
echo ""

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "Virtual environment not activated"
    print_info "Consider activating: source venv/bin/activate"
    echo ""
fi

# Run tests
print_info "Running tests..."
echo -e "${CYAN}Command: $PYTEST_CMD${NC}"
echo ""

START_TIME=$(date +%s)

# Execute pytest
if $PYTEST_CMD; then
    TEST_RESULT="PASSED"
    RESULT_COLOR=$GREEN
else
    TEST_RESULT="FAILED"
    RESULT_COLOR=$RED
fi

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${RESULT_COLOR}Test Result: $TEST_RESULT${NC}"
echo -e "${BLUE}========================================${NC}"
print_info "Duration: ${DURATION}s"
echo ""

# Show coverage report if enabled
if [ "$COVERAGE" = true ] && [ "$TEST_RESULT" = "PASSED" ]; then
    print_success "Coverage report generated"
    print_info "HTML Report: coverage_html/index.html"
    print_info "JSON Report: coverage.json"
    echo ""

    # Show coverage summary
    if [ -f "coverage.json" ]; then
        print_info "Opening coverage report..."

        # Try to open in browser (platform-specific)
        if command -v xdg-open &> /dev/null; then
            xdg-open coverage_html/index.html &
        elif command -v open &> /dev/null; then
            open coverage_html/index.html &
        elif command -v start &> /dev/null; then
            start coverage_html/index.html &
        fi
    fi
fi

# Print tips
echo -e "${CYAN}Tips:${NC}"
print_info "Run only failed tests: $0 --last-failed"
print_info "Run with coverage: $0 --unit --coverage"
print_info "Run in parallel: $0 --parallel"
print_info "Run specific test: pytest scripts/tests/unit/test_market_data_service.py::TestMarketDataService::test_fetch_daily_data_success"
echo ""

# Exit with test result
if [ "$TEST_RESULT" = "PASSED" ]; then
    print_success "All tests passed!"
    exit 0
else
    print_error "Some tests failed"
    exit 1
fi