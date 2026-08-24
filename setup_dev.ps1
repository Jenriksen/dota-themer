# Dota Themer - Windows Development Setup Script
# PowerShell script to set up development environment

param(
    [switch]$Help
)

if ($Help) {
    Write-Host "Dota Themer - Development Setup Script"
    Write-Host "=========================================="
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\setup_dev.ps1          - Set up development environment"
    Write-Host "  .\setup_dev.ps1 -Help     - Show this help message"
    Write-Host ""
    Write-Host "This script will:"
    Write-Host "  1. Check Python installation"
    Write-Host "  2. Create a virtual environment"
    Write-Host "  3. Install dependencies"
    Write-Host "  4. Run tests to verify setup"
    Write-Host ""
    exit 0
}

Write-Host "Dota Themer - Development Setup"
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "[1/4] Checking Python installation..." -ForegroundColor Yellow
try {
    $python = Get-Command python | Select-Object -ExpandProperty Source
    $pythonVersion = python --version 2>&1
    Write-Host "  Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Python not found!" -ForegroundColor Red
    Write-Host "  Please install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "[2/4] Creating virtual environment..." -ForegroundColor Yellow
try {
    if (Test-Path "venv") {
        Write-Host "  Virtual environment already exists" -ForegroundColor Yellow
    } else {
        python -m venv venv
        Write-Host "  Created: venv/" -ForegroundColor Green
    }
    # Activate the virtual environment for this session
    .\venv\Scripts\Activate.ps1
    Write-Host "  Activated virtual environment" -ForegroundColor Green
} catch {
    Write-Host "  ERROR: Failed to create virtual environment: $_" -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host ""
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Yellow
try {
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
        Write-Host "  Installed dependencies from requirements.txt" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: requirements.txt not found" -ForegroundColor Yellow
    }
} catch {
    Write-Host "  ERROR: Failed to install dependencies: $_" -ForegroundColor Red
    exit 1
}

# Run tests
Write-Host ""
Write-Host "[4/4] Running tests to verify setup..." -ForegroundColor Yellow
try {
    $testResult = python -m unittest discover 2>&1
    $exitCode = $LASTEXITCODE
    
    if ($exitCode -eq 0) {
        Write-Host "  All tests passed!" -ForegroundColor Green
        Write-Host "$testResult" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Some tests failed (exit code: $exitCode)" -ForegroundColor Yellow
        Write-Host "$testResult"
    }
} catch {
    Write-Host "  ERROR: Failed to run tests: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Setup complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "To use the development environment:"
Write-Host "  1. Activate the virtual environment:" -ForegroundColor Yellow
Write-Host "     .\venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "  2. Run the application:" -ForegroundColor Yellow
Write-Host "     python core.py 2"
Write-Host ""
Write-Host "  3. Run tests:" -ForegroundColor Yellow
Write-Host "     python -m unittest discover"
Write-Host ""
Write-Host "  4. Run Discord bot (set DISCORD_TOKEN first):" -ForegroundColor Yellow
Write-Host "     $env:DISCORD_TOKEN='your-token'"
Write-Host "     python bot.py"
Write-Host ""
