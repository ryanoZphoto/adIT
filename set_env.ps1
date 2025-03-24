# Get the directory where this script is located
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path

# Set AD_SERVICE_ROOT to the ad_service directory
$env:AD_SERVICE_ROOT = Join-Path $scriptPath "ad_service"

Write-Host "Environment variables set:"
Write-Host "AD_SERVICE_ROOT = $env:AD_SERVICE_ROOT"

# Create required directories if they don't exist
$directories = @(
    "data\backups",
    "logs",
    "charts",
    "temp",
    "config",
    "ad_matching",
    "ad_delivery",
    "gui",
    "analytics",
    "core",
    "utils"
) | ForEach-Object { Join-Path $env:AD_SERVICE_ROOT $_ }

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "Created directory: $dir"
    }
}

Write-Host "`nDirectory structure verified and ready" 