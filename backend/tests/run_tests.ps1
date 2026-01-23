# PowerShell test runner script for Files feature

Write-Host "===================="
Write-Host "Files Feature Tests"
Write-Host "===================="
Write-Host ""

# Check if pytest is installed
try {
    pytest --version | Out-Null
} catch {
    Write-Host "pytest not found. Installing..." -ForegroundColor Yellow
    pip install pytest pytest-cov pytest-mock
}

# Change to backend directory
$BackendDir = Split-Path -Parent $PSScriptRoot
Set-Location $BackendDir

Write-Host "Running all tests..." -ForegroundColor Blue
pytest tests/ -v

Write-Host ""
Write-Host "Running tests with coverage..." -ForegroundColor Blue
pytest --cov=domains.files --cov-report=term --cov-report=html tests/

Write-Host ""
Write-Host "✓ Tests complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Coverage report generated in: backend\htmlcov\index.html"
Write-Host ""
Write-Host "To run specific test categories:"
Write-Host "  Unit tests only:       pytest -m 'not integration' tests/"
Write-Host "  Integration tests:     pytest -m integration tests/"
Write-Host "  Specific file:         pytest tests/test_files_models.py"
Write-Host "  With verbose output:   pytest -vv tests/"
