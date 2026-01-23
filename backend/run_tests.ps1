# PowerShell script to run Files feature tests
# Usage: .\run_tests.ps1 [test_type]
# Test types: unit, service, api, integration, manual, all

param(
    [string]$TestType = "unit"
)

Write-Host "🧪 Running Files Feature Tests - Type: $TestType" -ForegroundColor Cyan
Write-Host "=" * 60

$BackendDir = $PSScriptRoot
Set-Location $BackendDir

switch ($TestType.ToLower()) {
    "unit" {
        Write-Host "Running unit tests (models + encryption)..." -ForegroundColor Yellow
        pytest tests/test_files_models.py tests/test_files_encryption.py -v
    }
    "service" {
        Write-Host "Running service layer tests..." -ForegroundColor Yellow
        pytest tests/test_files_service.py -v
    }
    "api" {
        Write-Host "Running API endpoint tests..." -ForegroundColor Yellow
        pytest tests/test_files_router.py -v
    }
    "integration" {
        Write-Host "Running integration tests..." -ForegroundColor Yellow
        pytest tests/test_files_integration.py -v -m integration
    }
    "gdrive" {
        Write-Host "Running Google Drive tests..." -ForegroundColor Yellow
        pytest tests/test_gdrive_connector.py -v -m gdrive
    }
    "manual" {
        Write-Host "Running manual test scenarios..." -ForegroundColor Yellow
        Write-Host "These tests use files in C:\Users\awron\Desktop\nex-test-files\" -ForegroundColor Cyan
        python tests/test_manual_scenarios.py
    }
    "manual-api" {
        Write-Host "Running manual API tests (requires running server)..." -ForegroundColor Yellow
        Write-Host "Ensure backend is running: docker-compose -f docker-compose.dev.yml up -d" -ForegroundColor Cyan
        pytest tests/test_manual_scenarios.py::test_api_scan_local_folder -v -s
        pytest tests/test_manual_scenarios.py::test_api_version_detection -v -s
    }
    "all" {
        Write-Host "Running ALL tests..." -ForegroundColor Yellow
        pytest tests/test_files_*.py -v
    }
    "coverage" {
        Write-Host "Running tests with coverage report..." -ForegroundColor Yellow
        pytest tests/test_files_*.py --cov=domains.files --cov-report=html --cov-report=term
        Write-Host ""
        Write-Host "Coverage report generated at: htmlcov\index.html" -ForegroundColor Green
    }
    default {
        Write-Host "Unknown test type: $TestType" -ForegroundColor Red
        Write-Host ""
        Write-Host "Available test types:" -ForegroundColor Yellow
        Write-Host "  unit          - Model and encryption tests"
        Write-Host "  service       - Service layer tests"
        Write-Host "  api           - API endpoint tests"
        Write-Host "  integration   - Integration workflow tests"
        Write-Host "  gdrive        - Google Drive tests"
        Write-Host "  manual        - Manual test scenarios (test files)"
        Write-Host "  manual-api    - Manual API tests (requires server)"
        Write-Host "  all           - All tests"
        Write-Host "  coverage      - All tests with coverage report"
        Write-Host ""
        Write-Host "Example: .\run_tests.ps1 unit" -ForegroundColor Cyan
        exit 1
    }
}

Write-Host ""
Write-Host "=" * 60
Write-Host "✅ Tests complete!" -ForegroundColor Green
