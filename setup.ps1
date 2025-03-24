# Ad Service Setup Script
# This script installs all required dependencies and sets up the environment

# Check if Python is installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check Python version
$pythonVersion = python --version 2>&1
if (-not $pythonVersion -match "Python 3\.([8-9]|1[0-9])") {
    Write-Host "Python 3.8 or higher is required. Current version: $pythonVersion" -ForegroundColor Red
    exit 1
}

# Get the service root directory from environment variable
$serviceRoot = $env:AD_SERVICE_ROOT
if (-not $serviceRoot) {
    # If not set, run set_env.ps1
    Write-Host "AD_SERVICE_ROOT not set. Running set_env.ps1..." -ForegroundColor Yellow
    & "$PSScriptRoot\set_env.ps1"
    $serviceRoot = $env:AD_SERVICE_ROOT
}

Write-Host "Setting up Ad Service in: $serviceRoot" -ForegroundColor Yellow

# Install dependencies
Write-Host "Installing required dependencies..." -ForegroundColor Yellow
$requirementsPath = Join-Path $PSScriptRoot "requirements.txt"
if (Test-Path $requirementsPath) {
    & python -m pip install --upgrade pip
    & python -m pip install -r $requirementsPath
} else {
    Write-Warning "requirements.txt not found at: $requirementsPath"
}

# Check if SQLite is installed
Write-Host "Checking SQLite installation..." -ForegroundColor Yellow
if (Get-Command "sqlite3" -ErrorAction SilentlyContinue) {
    Write-Host "SQLite is already installed and available in PATH." -ForegroundColor Green
} else {
    Write-Warning "SQLite not found in PATH. Please install SQLite and add it to your PATH."
}

# Initialize metrics database
Write-Host "Initializing metrics database..." -ForegroundColor Yellow
$metricsDb = Join-Path $serviceRoot "data\metrics.db"
$schemaPath = Join-Path $env:TEMP "metrics_schema.sql"

# Create schema file
@"
CREATE TABLE IF NOT EXISTS ad_impressions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ad_id TEXT,
    company_id TEXT,
    query TEXT,
    relevance_score REAL,
    position INTEGER
);

CREATE TABLE IF NOT EXISTS ad_clicks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ad_id TEXT,
    company_id TEXT,
    query TEXT,
    relevance_score REAL,
    position INTEGER
);

CREATE TABLE IF NOT EXISTS ad_conversions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    ad_id TEXT,
    company_id TEXT,
    query TEXT,
    relevance_score REAL,
    position INTEGER,
    conversion_value REAL
);

CREATE INDEX IF NOT EXISTS idx_impressions_timestamp ON ad_impressions(timestamp);
CREATE INDEX IF NOT EXISTS idx_clicks_timestamp ON ad_clicks(timestamp);
CREATE INDEX IF NOT EXISTS idx_conversions_timestamp ON ad_conversions(timestamp);
"@ | Set-Content -Path $schemaPath -Encoding UTF8

# Initialize the database with the schema
& sqlite3 $metricsDb ".read $schemaPath"

Write-Host "Metrics database initialized successfully." -ForegroundColor Green

Write-Host "`nSetup complete! You can now start the ad service with:" -ForegroundColor Green
Write-Host "  .\start_ad_service.ps1" -ForegroundColor Cyan
Write-Host "`nFor help and additional commands, run:" -ForegroundColor Green
Write-Host "  .\start_ad_service.ps1 -action menu" -ForegroundColor Cyan