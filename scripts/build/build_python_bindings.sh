#!/bin/bash
# Build Script - PyBind11 Bindings

set -e  # Exit on error
set -u  # Exit on undefined variable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BINDINGS_DIR="$PROJECT_ROOT/backend/python/src/nexus_bindings"
BUILD_DIR="$BINDINGS_DIR/build"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Nexus PyBind11 Bindings Build Script${NC}"
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

# Check if bindings directory exists
if [ ! -d "$BINDINGS_DIR" ]; then
    print_error "Bindings directory not found at: $BINDINGS_DIR"
    exit 1
fi

print_info "Project Root: $PROJECT_ROOT"
print_info "Bindings Directory: $BINDINGS_DIR"
print_info "Build Directory: $BUILD_DIR"
echo ""

# Parse arguments
CLEAN_BUILD=false
PYTHON_EXECUTABLE="python3"

while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --python)
            PYTHON_EXECUTABLE="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --clean              Clean build directory before building"
            echo "  --python <path>      Specify Python executable (default: python3)"
            echo "  --help               Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Check dependencies
print_info "Checking dependencies..."

if ! command -v cmake &> /dev/null; then
    print_error "cmake not found. Please install CMake 3.20+"
    exit 1
fi

if ! command -v "$PYTHON_EXECUTABLE" &> /dev/null; then
    print_error "Python not found: $PYTHON_EXECUTABLE"
    print_info "Try specifying with --python /path/to/python"
    exit 1
fi

CMAKE_VERSION=$(cmake --version | head -n1 | cut -d' ' -f3)
print_success "CMake version: $CMAKE_VERSION"

PYTHON_VERSION=$($PYTHON_EXECUTABLE --version 2>&1)
print_success "Python: $PYTHON_VERSION"

# Check if Python has pybind11
print_info "Checking for pybind11..."
if $PYTHON_EXECUTABLE -c "import pybind11" 2>/dev/null; then
    PYBIND11_VERSION=$($PYTHON_EXECUTABLE -c "import pybind11; print(pybind11.__version__)")
    print_success "pybind11 version: $PYBIND11_VERSION"
else
    print_error "pybind11 not found in Python environment"
    print_info "Install with: pip install pybind11"
    exit 1
fi

# Check if C++ engine is built
CPP_BUILD_DIR="$PROJECT_ROOT/backend/cpp/build"
if [ ! -d "$CPP_BUILD_DIR" ]; then
    print_warning "C++ engine build directory not found"
    print_info "Run: scripts/build/build_cpp_engine.sh first"
    print_info "Proceeding anyway, but build may fail..."
else
    print_success "C++ engine build directory found"
fi

echo ""

# Clean build directory if requested
if [ "$CLEAN_BUILD" = true ]; then
    print_warning "Cleaning build directory..."
    if [ -d "$BUILD_DIR" ]; then
        rm -rf "$BUILD_DIR"
        print_success "Build directory cleaned"
    else
        print_info "Build directory doesn't exist, skipping clean"
    fi
fi

# Create build directory
print_info "Creating build directory..."
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Configure with CMake
print_info "Configuring with CMake..."
cmake -G "Unix Makefiles" \
    -DCMAKE_BUILD_TYPE=Release \
    -DPYTHON_EXECUTABLE="$PYTHON_EXECUTABLE" \
    -DCMAKE_CXX_STANDARD=20 \
    -DCMAKE_CXX_FLAGS="-O3 -march=native" \
    "$BINDINGS_DIR"

if [ $? -eq 0 ]; then
    print_success "CMake configuration completed"
else
    print_error "CMake configuration failed"
    exit 1
fi

echo ""

# Build
print_info "Building PyBind11 bindings..."
NUM_CORES=$(nproc 2>/dev/null || sysctl -n hw.ncpu 2>/dev/null || echo 4)
print_info "Using $NUM_CORES parallel jobs"

make -j"$NUM_CORES"

if [ $? -eq 0 ]; then
    print_success "Build completed successfully"
else
    print_error "Build failed"
    exit 1
fi

echo ""

# Install bindings
print_info "Installing bindings to Python environment..."
make install

if [ $? -eq 0 ]; then
    print_success "Installation completed"
else
    print_error "Installation failed"
    exit 1
fi

echo ""

# Test import
print_info "Testing Python import..."
if $PYTHON_EXECUTABLE -c "import nexus_bindings" 2>/dev/null; then
    print_success "Python can import nexus_bindings"

    # Try to get version or info
    $PYTHON_EXECUTABLE -c "import nexus_bindings; print('Available modules:', dir(nexus_bindings))" 2>/dev/null || true
else
    print_warning "Failed to import nexus_bindings"
    print_info "You may need to add to PYTHONPATH or install in development mode"
fi

echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Summary${NC}"
echo -e "${GREEN}========================================${NC}"
print_success "Build Directory: $BUILD_DIR"
print_success "Python: $PYTHON_VERSION"
print_success "PyBind11: $PYBIND11_VERSION"
echo ""
print_info "To test bindings:"
print_info "  $PYTHON_EXECUTABLE -c 'import nexus_bindings; print(dir(nexus_bindings))'"
echo ""
echo -e "${GREEN}✓ PyBind11 bindings build completed successfully!${NC}"