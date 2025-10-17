@echo off
REM Test Runner Script - Nexus Engine (Windows)
REM Implementei este script para executar testes no Windows
REM Decidi manter compatibilidade com run_tests.sh

setlocal enabledelayedexpansion

echo ========================================
echo Nexus Engine Test Runner (Windows)
echo ========================================
echo.

REM Get project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..\..
cd /d "%PROJECT_ROOT%"

REM Check if pytest is installed
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pytest not found. Please install: pip install pytest pytest-cov pytest-xdist
    exit /b 1
)

echo [INFO] Project Root: %PROJECT_ROOT%
echo.

REM Parse arguments
set TEST_TYPE=all
set COVERAGE=false
set PARALLEL=false
set VERBOSE=false
set MARKERS=
set SPECIFIC_FILE=
set STOP_ON_FAIL=false
set LAST_FAILED=false

:parse_args
if "%~1"=="" goto end_parse_args
if "%~1"=="--unit" (
    set TEST_TYPE=unit
    set MARKERS=unit
    shift
    goto parse_args
)
if "%~1"=="--integration" (
    set TEST_TYPE=integration
    set MARKERS=integration
    shift
    goto parse_args
)
if "%~1"=="--e2e" (
    set TEST_TYPE=e2e
    set MARKERS=e2e
    shift
    goto parse_args
)
if "%~1"=="--fast" (
    set MARKERS=fast
    shift
    goto parse_args
)
if "%~1"=="--coverage" (
    set COVERAGE=true
    shift
    goto parse_args
)
if "%~1"=="--parallel" (
    set PARALLEL=true
    shift
    goto parse_args
)
if "%~1"=="--verbose" (
    set VERBOSE=true
    shift
    goto parse_args
)
if "%~1"=="--file" (
    set SPECIFIC_FILE=%~2
    shift
    shift
    goto parse_args
)
if "%~1"=="--stop-on-fail" (
    set STOP_ON_FAIL=true
    shift
    goto parse_args
)
if "%~1"=="--last-failed" (
    set LAST_FAILED=true
    shift
    goto parse_args
)
if "%~1"=="--help" (
    echo Usage: run_tests.bat [options]
    echo.
    echo Test Types:
    echo   --unit               Run only unit tests
    echo   --integration        Run only integration tests
    echo   --e2e                Run only end-to-end tests
    echo   --fast               Run only fast tests
    echo.
    echo Options:
    echo   --coverage           Generate coverage report
    echo   --parallel           Run tests in parallel
    echo   --verbose            Enable verbose output
    echo   --file ^<path^>        Run specific test file
    echo   --stop-on-fail       Stop on first failure
    echo   --last-failed        Run only tests that failed last time
    echo   --help               Show this help message
    echo.
    echo Examples:
    echo   run_tests.bat --unit --coverage
    echo   run_tests.bat --integration --parallel
    echo   run_tests.bat --file scripts\tests\unit\test_market_data_service.py
    exit /b 0
)
echo [ERROR] Unknown option: %~1
echo Use --help for usage information
exit /b 1

:end_parse_args

REM Build pytest command
set PYTEST_CMD=python -m pytest

REM Add verbosity
if "%VERBOSE%"=="true" set PYTEST_CMD=%PYTEST_CMD% -vv

REM Add markers
if not "%MARKERS%"=="" set PYTEST_CMD=%PYTEST_CMD% -m %MARKERS%

REM Add specific file
if not "%SPECIFIC_FILE%"=="" set PYTEST_CMD=%PYTEST_CMD% %SPECIFIC_FILE%

REM Add coverage
if "%COVERAGE%"=="true" (
    set PYTEST_CMD=%PYTEST_CMD% --cov=backend/python/src --cov=frontend/src
    set PYTEST_CMD=%PYTEST_CMD% --cov-report=html:coverage_html
    set PYTEST_CMD=%PYTEST_CMD% --cov-report=term-missing
    set PYTEST_CMD=%PYTEST_CMD% --cov-report=json:coverage.json
)

REM Add parallel execution
if "%PARALLEL%"=="true" (
    python -m pytest_xdist --version >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] pytest-xdist not found. Running sequentially.
        echo [INFO] Install with: pip install pytest-xdist
    ) else (
        set PYTEST_CMD=%PYTEST_CMD% -n auto
    )
)

REM Add stop on fail
if "%STOP_ON_FAIL%"=="true" set PYTEST_CMD=%PYTEST_CMD% -x

REM Add last failed
if "%LAST_FAILED%"=="true" set PYTEST_CMD=%PYTEST_CMD% --lf

REM Print configuration
echo Test Configuration:
echo [INFO] Test Type: %TEST_TYPE%
if not "%MARKERS%"=="" echo [INFO] Markers: %MARKERS%
if "%COVERAGE%"=="true" echo [INFO] Coverage: Enabled
if "%PARALLEL%"=="true" echo [INFO] Parallel: Enabled
if "%VERBOSE%"=="true" echo [INFO] Verbose: Enabled
if not "%SPECIFIC_FILE%"=="" echo [INFO] File: %SPECIFIC_FILE%
echo.

REM Check if virtual environment is activated
if "%VIRTUAL_ENV%"=="" (
    echo [WARNING] Virtual environment not activated
    echo [INFO] Consider activating: venv\Scripts\activate
    echo.
)

REM Run tests
echo [INFO] Running tests...
echo Command: %PYTEST_CMD%
echo.

REM Execute pytest
%PYTEST_CMD%
set TEST_EXIT_CODE=%errorlevel%

echo.
echo ========================================
if %TEST_EXIT_CODE%==0 (
    echo Test Result: PASSED
) else (
    echo Test Result: FAILED
)
echo ========================================
echo.

REM Show coverage report if enabled
if "%COVERAGE%"=="true" if %TEST_EXIT_CODE%==0 (
    echo [SUCCESS] Coverage report generated
    echo [INFO] HTML Report: coverage_html\index.html
    echo [INFO] JSON Report: coverage.json
    echo.
    echo [INFO] Opening coverage report...
    start coverage_html\index.html
)

REM Print tips
echo Tips:
echo [INFO] Run only failed tests: run_tests.bat --last-failed
echo [INFO] Run with coverage: run_tests.bat --unit --coverage
echo [INFO] Run in parallel: run_tests.bat --parallel
echo.

REM Exit with test result
if %TEST_EXIT_CODE%==0 (
    echo [SUCCESS] All tests passed!
    exit /b 0
) else (
    echo [ERROR] Some tests failed
    exit /b 1
)