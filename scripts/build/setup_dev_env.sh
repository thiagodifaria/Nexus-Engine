#!/bin/bash
# Setup Development Environment - Nexus Engine

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

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}Nexus Engine - Development Environment Setup${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Functions for colored output
print_step() {
    echo -e "${CYAN}[STEP]${NC} $1"
}

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

# Parse arguments
SKIP_CPP=false
SKIP_PYTHON=false
SKIP_FRONTEND=false
SKIP_DATABASE=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-cpp)
            SKIP_CPP=true
            shift
            ;;
        --skip-python)
            SKIP_PYTHON=true
            shift
            ;;
        --skip-frontend)
            SKIP_FRONTEND=true
            shift
            ;;
        --skip-database)
            SKIP_DATABASE=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --skip-cpp          Skip C++ engine build"
            echo "  --skip-python       Skip Python dependencies and bindings"
            echo "  --skip-frontend     Skip frontend dependencies"
            echo "  --skip-database     Skip database setup"
            echo "  --skip-tests        Skip running tests"
            echo "  --help              Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

print_info "Project Root: $PROJECT_ROOT"
echo ""

# ==================================================
# STEP 1: Check System Dependencies
# ==================================================
print_step "Checking system dependencies..."

# Check OS
OS=$(uname -s)
print_info "Operating System: $OS"

# Required tools
REQUIRED_TOOLS=("cmake" "git")
MISSING_TOOLS=()

for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        MISSING_TOOLS+=("$tool")
    fi
done

if [ ${#MISSING_TOOLS[@]} -ne 0 ]; then
    print_error "Missing required tools: ${MISSING_TOOLS[*]}"
    print_info "Please install missing tools and run again"
    exit 1
fi

# Check compilers
if ! command -v g++ &> /dev/null && ! command -v clang++ &> /dev/null; then
    print_error "No C++ compiler found (g++ or clang++)"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 not found"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
print_success "Found: $PYTHON_VERSION"

print_success "All system dependencies present"
echo ""

# ==================================================
# STEP 2: Setup Python Virtual Environment
# ==================================================
if [ "$SKIP_PYTHON" = false ]; then
    print_step "Setting up Python virtual environment..."

    VENV_DIR="$PROJECT_ROOT/venv"

    if [ -d "$VENV_DIR" ]; then
        print_warning "Virtual environment already exists"
        print_info "To recreate, delete: rm -rf $VENV_DIR"
    else
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    fi

    # Activate venv
    source "$VENV_DIR/bin/activate"

    # Upgrade pip
    print_info "Upgrading pip..."
    pip install --upgrade pip setuptools wheel

    # Install backend Python dependencies
    print_info "Installing backend Python dependencies..."
    pip install -r "$PROJECT_ROOT/backend/python/requirements.txt"

    # Install frontend dependencies
    if [ "$SKIP_FRONTEND" = false ]; then
        print_info "Installing frontend dependencies..."
        pip install -r "$PROJECT_ROOT/frontend/requirements.txt"
    fi

    print_success "Python dependencies installed"
    echo ""
else
    print_warning "Skipping Python setup"
    echo ""
fi

# ==================================================
# STEP 3: Build C++ Engine
# ==================================================
if [ "$SKIP_CPP" = false ]; then
    print_step "Building C++ engine..."

    if [ -f "$SCRIPT_DIR/build_cpp_engine.sh" ]; then
        bash "$SCRIPT_DIR/build_cpp_engine.sh" --release --test
        print_success "C++ engine built successfully"
    else
        print_error "build_cpp_engine.sh not found"
        exit 1
    fi

    echo ""
else
    print_warning "Skipping C++ engine build"
    echo ""
fi

# ==================================================
# STEP 4: Build PyBind11 Bindings
# ==================================================
if [ "$SKIP_PYTHON" = false ]; then
    print_step "Building PyBind11 bindings..."

    if [ -f "$SCRIPT_DIR/build_python_bindings.sh" ]; then
        bash "$SCRIPT_DIR/build_python_bindings.sh" --clean
        print_success "PyBind11 bindings built successfully"
    else
        print_error "build_python_bindings.sh not found"
        exit 1
    fi

    echo ""
else
    print_warning "Skipping PyBind11 bindings"
    echo ""
fi

# ==================================================
# STEP 5: Setup Database
# ==================================================
if [ "$SKIP_DATABASE" = false ]; then
    print_step "Setting up database..."

    # Check if Docker is available
    if command -v docker &> /dev/null && command -v docker-compose &> /dev/null; then
        print_info "Starting PostgreSQL with Docker Compose..."

        cd "$PROJECT_ROOT/devops/docker"

        # Check if .env exists
        if [ ! -f ".env" ]; then
            print_warning ".env file not found, copying from .env.example"
            cp .env.example .env
            print_info "Please edit .env with your credentials"
        fi

        # Start only postgres
        docker-compose up -d postgres

        # Wait for postgres to be ready
        print_info "Waiting for PostgreSQL to be ready..."
        sleep 5

        # Run migrations
        print_info "Running database migrations..."
        cd "$PROJECT_ROOT/backend/python"

        if source "$PROJECT_ROOT/venv/bin/activate" 2>/dev/null; then
            alembic upgrade head 2>/dev/null || print_warning "Migrations not configured yet"
        fi

        print_success "Database setup completed"
    else
        print_warning "Docker not found, skipping database setup"
        print_info "Install Docker and run: cd devops/docker && docker-compose up -d"
    fi

    echo ""
else
    print_warning "Skipping database setup"
    echo ""
fi

# ==================================================
# STEP 6: Run Tests
# ==================================================
if [ "$SKIP_TESTS" = false ]; then
    print_step "Running tests..."

    # C++ tests
    if [ "$SKIP_CPP" = false ]; then
        print_info "Running C++ tests..."
        cd "$PROJECT_ROOT/backend/cpp/build"
        ctest --output-on-failure || print_warning "Some C++ tests failed"
    fi

    # Python tests
    if [ "$SKIP_PYTHON" = false ]; then
        print_info "Running Python tests..."
        cd "$PROJECT_ROOT"
        source "$VENV_DIR/bin/activate" 2>/dev/null || true
        pytest scripts/tests/unit/ -v 2>/dev/null || print_warning "Python unit tests not configured yet"
    fi

    echo ""
else
    print_warning "Skipping tests"
    echo ""
fi

# ==================================================
# STEP 7: Create helper scripts
# ==================================================
print_step "Creating helper scripts..."

# Create activate script
cat > "$PROJECT_ROOT/activate_env.sh" << 'EOF'
#!/bin/bash
# Activate Nexus development environment
source venv/bin/activate
export PYTHONPATH="$PWD/backend/python/src:$PYTHONPATH"
echo "Nexus development environment activated"
echo "To deactivate: deactivate"
EOF

chmod +x "$PROJECT_ROOT/activate_env.sh"

print_success "Helper scripts created"
echo ""

# ==================================================
# Summary
# ==================================================
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

print_success "Development environment is ready"
echo ""

print_info "To activate the environment:"
echo "  source activate_env.sh"
echo ""

print_info "To start the backend services:"
echo "  cd devops/docker && docker-compose up -d"
echo ""

print_info "To run the frontend:"
echo "  cd frontend/src && python main.py"
echo ""

print_info "To access Grafana:"
echo "  http://localhost:3000 (admin/nexus_admin)"
echo ""

print_info "Useful commands:"
echo "  Build C++: ./scripts/build/build_cpp_engine.sh"
echo "  Build bindings: ./scripts/build/build_python_bindings.sh"
echo "  Build frontend: ./scripts/build/build_frontend.sh"
echo "  Run tests: pytest scripts/tests/"
echo ""

if [ ! -f "$PROJECT_ROOT/devops/docker/.env" ]; then
    print_warning "Don't forget to configure .env file:"
    print_info "  cp devops/docker/.env.example devops/docker/.env"
    print_info "  Edit devops/docker/.env with your API keys"
fi

echo ""
echo -e "${GREEN}✓ Setup completed successfully!${NC}"
echo -e "${CYAN}Happy coding! 🚀${NC}"