#!/bin/bash
# Build Script - Nexus C++ Engine

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
CPP_DIR="$PROJECT_ROOT/backend/cpp"
BUILD_DIR="$CPP_DIR/build"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Nexus C++ Engine Build Script${NC}"
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

# Check if C++ directory exists
if [ ! -d "$CPP_DIR" ]; then
    print_error "C++ directory not found at: $CPP_DIR"
    exit 1
fi

print_info "Project Root: $PROJECT_ROOT"
print_info "C++ Directory: $CPP_DIR"
print_info "Build Directory: $BUILD_DIR"
echo ""

# Parse arguments
BUILD_TYPE="Release"
CLEAN_BUILD=false
RUN_TESTS=false
INSTALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --debug)
            BUILD_TYPE="Debug"
            shift
            ;;
        --release)
            BUILD_TYPE="Release"
            shift
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --test)
            RUN_TESTS=true
            shift
            ;;
        --install)
            INSTALL=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --debug      Build in Debug mode (default: Release)"
            echo "  --release    Build in Release mode"
            echo "  --clean      Clean build directory before building"
            echo "  --test       Run tests after building"
            echo "  --install    Install libraries to system"
            echo "  --help       Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_info "Build Type: $BUILD_TYPE"

# Check dependencies
print_info "Checking dependencies..."

if ! command -v cmake &> /dev/null; then
    print_error "cmake not found. Please install CMake 3.20+"
    exit 1
fi

if ! command -v g++ &> /dev/null && ! command -v clang++ &> /dev/null; then
    print_error "C++ compiler not found. Please install g++ or clang++"
    exit 1
fi

CMAKE_VERSION=$(cmake --version | head -n1 | cut -d' ' -f3)
print_success "CMake version: $CMAKE_VERSION"

if command -v g++ &> /dev/null; then
    GCC_VERSION=$(g++ --version | head -n1)
    print_success "Compiler: $GCC_VERSION"
elif command -v clang++ &> /dev/null; then
    CLANG_VERSION=$(clang++ --version | head -n1)
    print_success "Compiler: $CLANG_VERSION"
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
    -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
    -DCMAKE_CXX_STANDARD=20 \
    -DCMAKE_CXX_FLAGS_RELEASE="-O3 -march=native -mtune=native -flto -DNDEBUG" \
    -DCMAKE_CXX_FLAGS_DEBUG="-g -O0 -Wall -Wextra -pedantic" \
    -DBUILD_TESTING=ON \
    -DBUILD_BENCHMARKS=ON \
    "$CPP_DIR"

if [ $? -eq 0 ]; then
    print_success "CMake configuration completed"
else
    print_error "CMake configuration failed"
    exit 1
fi

echo ""

# Build
print_info "Building C++ engine..."
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

# Run tests if requested
if [ "$RUN_TESTS" = true ]; then
    print_info "Running tests..."
    ctest --output-on-failure

    if [ $? -eq 0 ]; then
        print_success "All tests passed"
    else
        print_error "Some tests failed"
        exit 1
    fi
    echo ""
fi

# Install if requested
if [ "$INSTALL" = true ]; then
    print_info "Installing libraries..."
    sudo make install

    if [ $? -eq 0 ]; then
        print_success "Installation completed"
        sudo ldconfig 2>/dev/null || true
    else
        print_error "Installation failed"
        exit 1
    fi
    echo ""
fi

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Summary${NC}"
echo -e "${GREEN}========================================${NC}"
print_success "Build Type: $BUILD_TYPE"
print_success "Build Directory: $BUILD_DIR"
if [ "$RUN_TESTS" = true ]; then
    print_success "Tests: PASSED"
fi
if [ "$INSTALL" = true ]; then
    print_success "Installation: COMPLETED"
fi
echo ""
print_info "To run benchmarks: cd $BUILD_DIR && ./benchmark"
print_info "To run tests: cd $BUILD_DIR && ctest"
echo ""
echo -e "${GREEN}✓ C++ Engine build completed successfully!${NC}"