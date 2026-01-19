# ZeroStack Backend Installation Script (Windows PowerShell)
# Usage: .\scripts\install-backend.ps1 [core|ml|full]

param(
    [ValidateSet("core", "ml", "full")]
    [string]$Mode = "core"
)

$ErrorActionPreference = "Stop"

Write-Host "================================" -ForegroundColor Cyan
Write-Host "ZeroStack Backend Installation" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python not found. Please install Python 3.11+" -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Navigate to backend
Push-Location backend

try {
    # Create virtual environment if it doesn't exist
    if (-not (Test-Path "venv")) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv venv
    }

    # Activate virtual environment
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    .\venv\Scripts\Activate.ps1

    # Upgrade pip
    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    pip install --upgrade pip

    # Install based on mode
    switch ($Mode) {
        "core" {
            Write-Host ""
            Write-Host "Installing CORE dependencies (fast, no ML)..." -ForegroundColor Cyan
            Write-Host "This skips PyTorch/SDV for faster install." -ForegroundColor Gray
            Write-Host ""
            pip install -r requirements-core.txt
            Write-Host ""
            Write-Host "Core install complete!" -ForegroundColor Green
            Write-Host "To add ML support later: pip install -r requirements-ml.txt" -ForegroundColor Gray
        }
        "ml" {
            Write-Host ""
            Write-Host "Installing ML dependencies (includes PyTorch)..." -ForegroundColor Cyan
            Write-Host "This may take 5-10 minutes." -ForegroundColor Yellow
            Write-Host ""

            # Option: CPU-only PyTorch
            $cpuOnly = Read-Host "Use CPU-only PyTorch? (saves ~1.5GB) [Y/n]"
            if ($cpuOnly -ne "n" -and $cpuOnly -ne "N") {
                Write-Host "Installing CPU-only PyTorch first..." -ForegroundColor Yellow
                pip install torch --index-url https://download.pytorch.org/whl/cpu
            }

            pip install -r requirements-ml.txt
            Write-Host ""
            Write-Host "ML install complete!" -ForegroundColor Green
        }
        "full" {
            Write-Host ""
            Write-Host "Installing FULL dependencies (ML + testing)..." -ForegroundColor Cyan
            Write-Host "This may take 10+ minutes." -ForegroundColor Yellow
            Write-Host ""
            pip install -r requirements.txt
            Write-Host ""
            Write-Host "Full install complete!" -ForegroundColor Green
        }
    }

    Write-Host ""
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "Installation Summary" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    Write-Host "Mode: $Mode"
    Write-Host "Virtual env: backend\venv"
    Write-Host ""
    Write-Host "To activate: .\backend\venv\Scripts\Activate.ps1"
    Write-Host "To run server: cd backend && uvicorn main:app --reload"
    Write-Host ""
}
finally {
    Pop-Location
}
