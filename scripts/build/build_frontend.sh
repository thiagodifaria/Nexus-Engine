#!/bin/bash
# Build Script - PyQt6 Frontend

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
FRONTEND_DIR="$PROJECT_ROOT/frontend"
DIST_DIR="$PROJECT_ROOT/dist"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Nexus Frontend Build Script${NC}"
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

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    print_error "Frontend directory not found at: $FRONTEND_DIR"
    exit 1
fi

print_info "Project Root: $PROJECT_ROOT"
print_info "Frontend Directory: $FRONTEND_DIR"
print_info "Distribution Directory: $DIST_DIR"
echo ""

# Parse arguments
PYTHON_EXECUTABLE="python3"
ONE_FILE=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --python)
            PYTHON_EXECUTABLE="$2"
            shift 2
            ;;
        --onefile)
            ONE_FILE=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --python <path>      Specify Python executable (default: python3)"
            echo "  --onefile            Create single executable file (slower startup)"
            echo "  --clean              Clean dist and build directories before building"
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

if ! command -v "$PYTHON_EXECUTABLE" &> /dev/null; then
    print_error "Python not found: $PYTHON_EXECUTABLE"
    print_info "Try specifying with --python /path/to/python"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_EXECUTABLE --version 2>&1)
print_success "Python: $PYTHON_VERSION"

# Check if PyQt6 is installed
print_info "Checking for PyQt6..."
if $PYTHON_EXECUTABLE -c "import PyQt6" 2>/dev/null; then
    PYQT_VERSION=$($PYTHON_EXECUTABLE -c "from PyQt6.QtCore import QT_VERSION_STR; print(QT_VERSION_STR)")
    print_success "PyQt6 version: $PYQT_VERSION"
else
    print_error "PyQt6 not found in Python environment"
    print_info "Install with: pip install PyQt6"
    exit 1
fi

# Check if PyInstaller is installed
print_info "Checking for PyInstaller..."
if $PYTHON_EXECUTABLE -m PyInstaller --version &> /dev/null; then
    PYINSTALLER_VERSION=$($PYTHON_EXECUTABLE -m PyInstaller --version 2>&1)
    print_success "PyInstaller version: $PYINSTALLER_VERSION"
else
    print_error "PyInstaller not found in Python environment"
    print_info "Install with: pip install pyinstaller"
    exit 1
fi

echo ""

# Clean if requested
if [ "$CLEAN" = true ]; then
    print_warning "Cleaning build artifacts..."
    rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist" "$FRONTEND_DIR/build" "$FRONTEND_DIR/dist"
    find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
    print_success "Clean completed"
    echo ""
fi

# Create dist directory
mkdir -p "$DIST_DIR"

# Build frontend
cd "$FRONTEND_DIR"

print_info "Building frontend with PyInstaller..."

# PyInstaller options
PYINSTALLER_OPTS=(
    --name="NexusEngine"
    --windowed
    --icon="$FRONTEND_DIR/resources/icons/app_icon.ico"
    --add-data="$FRONTEND_DIR/resources:resources"
    --hidden-import="PyQt6"
    --hidden-import="PyQt6.QtCore"
    --hidden-import="PyQt6.QtGui"
    --hidden-import="PyQt6.QtWidgets"
    --hidden-import="pyqtgraph"
    --hidden-import="numpy"
    --hidden-import="pandas"
    --collect-all="PyQt6"
    --clean
    --noconfirm
)

if [ "$ONE_FILE" = true ]; then
    print_info "Creating single-file executable..."
    PYINSTALLER_OPTS+=("--onefile")
else
    print_info "Creating directory-based executable..."
    PYINSTALLER_OPTS+=("--onedir")
fi

# Add main.py as entry point
PYINSTALLER_OPTS+=("$FRONTEND_DIR/src/main.py")

# Run PyInstaller
$PYTHON_EXECUTABLE -m PyInstaller "${PYINSTALLER_OPTS[@]}"

if [ $? -eq 0 ]; then
    print_success "PyInstaller build completed"
else
    print_error "PyInstaller build failed"
    exit 1
fi

echo ""

# Copy to dist directory
print_info "Copying executable to distribution directory..."

if [ "$ONE_FILE" = true ]; then
    # Single file executable
    if [ "$(uname)" == "Darwin" ] || [ "$(uname)" == "Linux" ]; then
        cp "$FRONTEND_DIR/dist/NexusEngine" "$DIST_DIR/"
        chmod +x "$DIST_DIR/NexusEngine"
    else
        cp "$FRONTEND_DIR/dist/NexusEngine.exe" "$DIST_DIR/"
    fi
else
    # Directory-based executable
    cp -r "$FRONTEND_DIR/dist/NexusEngine" "$DIST_DIR/"
fi

print_success "Executable copied to: $DIST_DIR"

echo ""

# Create README for distribution
cat > "$DIST_DIR/README.txt" << EOF
Nexus Engine Trading Platform
===============================

To run the application:

Windows:
  - Double-click NexusEngine.exe (or NexusEngine/NexusEngine.exe)

Linux/Mac:
  - Run: ./NexusEngine (or ./NexusEngine/NexusEngine)

Requirements:
  - No additional dependencies required (all bundled)

Notes:
  - First startup may be slower as the application initializes
  - Backend services must be running (see backend/README.md)
  - Prometheus endpoint: http://localhost:9091

For support and documentation:
  - See: docs/guides/getting-started.md
  - GitHub: https://github.com/your-repo/nexus-engine

Built on: $(date)
Python version: $PYTHON_VERSION
PyQt6 version: $PYQT_VERSION
EOF

print_success "README created in distribution directory"

echo ""

# Test if executable exists
if [ "$ONE_FILE" = true ]; then
    EXEC_PATH="$DIST_DIR/NexusEngine"
    [ "$(uname)" != "Darwin" ] && [ "$(uname)" != "Linux" ] && EXEC_PATH="$DIST_DIR/NexusEngine.exe"
else
    EXEC_PATH="$DIST_DIR/NexusEngine/NexusEngine"
    [ "$(uname)" != "Darwin" ] && [ "$(uname)" != "Linux" ] && EXEC_PATH="$DIST_DIR/NexusEngine/NexusEngine.exe"
fi

if [ -f "$EXEC_PATH" ] || [ -d "$DIST_DIR/NexusEngine" ]; then
    print_success "Executable created successfully"

    # Get size
    if [ "$ONE_FILE" = true ]; then
        SIZE=$(du -h "$EXEC_PATH" | cut -f1)
        print_info "Executable size: $SIZE"
    else
        SIZE=$(du -sh "$DIST_DIR/NexusEngine" | cut -f1)
        print_info "Distribution size: $SIZE"
    fi
else
    print_error "Executable not found at expected location"
    exit 1
fi

echo ""

# Summary
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Build Summary${NC}"
echo -e "${GREEN}========================================${NC}"
print_success "Distribution: $DIST_DIR"
print_success "Python: $PYTHON_VERSION"
print_success "PyQt6: $PYQT_VERSION"
if [ "$ONE_FILE" = true ]; then
    print_success "Mode: Single-file executable"
else
    print_success "Mode: Directory-based executable"
fi
echo ""
print_info "To run the application:"
if [ "$ONE_FILE" = true ]; then
    print_info "  $EXEC_PATH"
else
    print_info "  cd $DIST_DIR/NexusEngine && ./NexusEngine"
fi
echo ""
print_warning "Note: Backend services must be running first"
print_info "Start backend: cd devops/docker && docker-compose up -d"
echo ""
echo -e "${GREEN}✓ Frontend build completed successfully!${NC}"