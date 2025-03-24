# Ad Service Management Script
# This script provides easy commands to start, stop, and interact with the ad service

param (
    [Parameter(Mandatory=$false)]
    [string]$action = "menu",
    
    [Parameter(Mandatory=$false)]
    [switch]$verboseOutput = $false
)

# Set verbose mode if requested
$VerbosePreference = if ($verboseOutput) { "Continue" } else { "SilentlyContinue" }

# Get the service root directory from environment variable
$serviceRoot = $env:AD_SERVICE_ROOT
if (-not $serviceRoot) {
    Write-Error "AD_SERVICE_ROOT environment variable not set. Please run set_env.ps1 first."
    exit 1
}

# Set working directory to service root
Set-Location $serviceRoot

# Function to start the chat interface
function Start-ChatInterface {
    Write-Host "Starting Chat Interface..." -ForegroundColor Yellow
    $chatScript = Join-Path $serviceRoot "gui\chat_interface.py"
    if (-not (Test-Path $chatScript)) {
        Write-Error "Chat interface script not found at: $chatScript"
        return
    }
    Start-Process -FilePath "cmd" -ArgumentList "/k", "python", "-m", "streamlit", "run", "`"$chatScript`"", "--server.port", "8501", "--server.address", "localhost"
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8501"
}

# Function to start the ad manager
function Start-AdManager {
    Write-Host "Starting Ad Manager..." -ForegroundColor Yellow
    $managerScript = Join-Path $serviceRoot "gui\ad_manager.py"
    if (-not (Test-Path $managerScript)) {
        Write-Error "Ad manager script not found at: $managerScript"
        return
    }
    Start-Process -FilePath "cmd" -ArgumentList "/k", "python", "-m", "streamlit", "run", "`"$managerScript`"", "--server.port", "8502", "--server.address", "localhost"
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8502"
}

# Function to start the metrics dashboard
function Start-MetricsDashboard {
    Write-Host "Starting Metrics Dashboard..." -ForegroundColor Yellow
    $metricsScript = Join-Path $serviceRoot "analytics\metrics_dashboard.py"
    if (-not (Test-Path $metricsScript)) {
        Write-Error "Metrics dashboard script not found at: $metricsScript"
        return
    }
    Start-Process -FilePath "cmd" -ArgumentList "/k", "python", "-m", "streamlit", "run", "`"$metricsScript`"", "--server.port", "8503", "--server.address", "localhost"
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8503"
}

# Function to stop all services
function Stop-AllServices {
    Write-Host "Stopping all services..." -ForegroundColor Yellow
    Get-Process | Where-Object { $_.ProcessName -eq "python" -and $_.CommandLine -like "*streamlit*" } | Stop-Process -Force
    Write-Host "All services stopped." -ForegroundColor Green
}

# Function to show menu
function Show-Menu {
    Write-Host "`nAd Service Control Menu" -ForegroundColor Cyan
    Write-Host "======================" -ForegroundColor Cyan
    Write-Host "1. Start All Services"
    Write-Host "2. Stop All Services"
    Write-Host "3. Start Chat Interface"
    Write-Host "4. Start Ad Manager"
    Write-Host "5. Start Metrics Dashboard"
    Write-Host "6. Exit"
    Write-Host ""
    
    $choice = Read-Host "Enter your choice (1-6)"
    
    switch ($choice) {
        "1" { 
            Start-ChatInterface
            Start-AdManager
            Start-MetricsDashboard
        }
        "2" { Stop-AllServices }
        "3" { Start-ChatInterface }
        "4" { Start-AdManager }
        "5" { Start-MetricsDashboard }
        "6" { exit }
        default { 
            Write-Host "Invalid choice. Please try again." -ForegroundColor Red
            Show-Menu
        }
    }
}

function Start-AdService {
    param (
        [Parameter(Mandatory=$false)]
        [switch]$separateWindow = $false
    )
    
    Write-Host "Starting Ad Service..." -ForegroundColor Green
    $scriptPath = Join-Path (Get-Location) "ad_service\start_service.py"
    
    # Check if file exists
    if (-not (Test-Path $scriptPath)) {
        Write-Host "Error: Cannot find start_service.py at path: $scriptPath" -ForegroundColor Red
        Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
        Write-Host "Files in ad_service directory:" -ForegroundColor Yellow
        if (Test-Path "ad_service") {
            Get-ChildItem "ad_service" | ForEach-Object { Write-Host "  $_" }
        } else {
            Write-Host "  ad_service directory not found!" -ForegroundColor Red
        }
        return
    }
    
    if ($separateWindow) {
        # Start in a new window so the output doesn't interfere with this script
        Write-Host "Starting service in a separate window..." -ForegroundColor Green
        Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd '$(Get-Location)'; python '$scriptPath'; Read-Host 'Press Enter to close this window'"
    } else {
        # Start in the current window to see all output
        Write-Host "Starting service with console output (CTRL+C to return to menu)..." -ForegroundColor Green
        Write-Host "---------- SERVICE OUTPUT BELOW ----------" -ForegroundColor Yellow
        try {
            python $scriptPath
        } catch {
            Write-Host "Error starting service: $_" -ForegroundColor Red
        }
        Write-Host "---------- SERVICE OUTPUT ABOVE ----------" -ForegroundColor Yellow
    }
    
    # Wait for service to be responsive
    Write-Host "Waiting for service to start up..." -ForegroundColor Green
    $maxAttempts = 15
    $attempt = 0
    $serviceStarted = $false
    
    while ($attempt -lt $maxAttempts -and -not $serviceStarted) {
        $attempt++
        Write-Verbose "Checking if service is running (attempt $attempt/$maxAttempts)..."
        
        try {
            $running = Test-ServiceRunning
            if ($running) {
                $serviceStarted = $true
                Write-Host "Service successfully started!" -ForegroundColor Green
                Write-Host "  - Chat Interface: http://localhost:8501" -ForegroundColor Cyan
                Write-Host "  - Metrics Dashboard: http://localhost:8000/metrics" -ForegroundColor Cyan
            } else {
                Write-Verbose "Service not yet available..."
                Start-Sleep -Seconds 1
            }
        } catch {
            Write-Verbose "Error checking service: $_"
            Start-Sleep -Seconds 1
        }
    }
    
    if (-not $serviceStarted) {
        Write-Host "Warning: Service may not have started properly." -ForegroundColor Yellow
        Write-Host "You can check status with option 9 from the menu." -ForegroundColor Yellow
    }
}

function Test-ServiceRunning {
    $chatInterfaceUrl = "http://localhost:8501"
    $metricsUrl = "http://localhost:8000/metrics"
    
    try {
        $chatResponse = Invoke-WebRequest -Uri $chatInterfaceUrl -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($chatResponse.StatusCode -eq 200) {
            Write-Verbose "Chat interface is running"
            return $true
        }
    } catch {
        Write-Verbose "Chat interface not available: $_"
    }
    
    try {
        $metricsResponse = Invoke-WebRequest -Uri $metricsUrl -UseBasicParsing -TimeoutSec 1 -ErrorAction SilentlyContinue
        if ($metricsResponse.StatusCode -eq 200) {
            Write-Verbose "Metrics endpoint is running"
            return $true
        }
    } catch {
        Write-Verbose "Metrics endpoint not available: $_"
    }
    
    return $false
}

function Stop-AdService {
    Write-Host "Stopping Ad Service..." -ForegroundColor Red
    $count = 0
    $processes = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*start_service.py*" -or $_.CommandLine -like "*streamlit*" }
    
    if ($processes -and $processes.Count -gt 0) {
        foreach ($process in $processes) {
            try {
                $process | Stop-Process -Force
                $count++
            } catch {
                Write-Host "Error stopping process $($process.Id): $_" -ForegroundColor Red
            }
        }
        
        Write-Host "Stopped $count Python processes." -ForegroundColor Green
    } else {
        Write-Host "No running Ad Service processes found." -ForegroundColor Yellow
    }
    
    # Also try to kill any Streamlit processes
    $streamlitProcesses = Get-Process -Name streamlit -ErrorAction SilentlyContinue
    if ($streamlitProcesses -and $streamlitProcesses.Count -gt 0) {
        foreach ($process in $streamlitProcesses) {
            try {
                $process | Stop-Process -Force
                $count++
            } catch {
                Write-Host "Error stopping Streamlit process $($process.Id): $_" -ForegroundColor Red
            }
        }
    }
    
    Write-Host "Service stopped!" -ForegroundColor Green
}

function Show-ServiceStatus {
    Write-Host "Checking service status..." -ForegroundColor Blue
    
    # Check Python processes
    $pythonProcesses = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*start_service.py*" -or $_.CommandLine -like "*streamlit*" }
    $streamlitProcesses = Get-Process -Name streamlit -ErrorAction SilentlyContinue
    
    Write-Host "Python processes related to the service:" -ForegroundColor Cyan
    if ($pythonProcesses -and $pythonProcesses.Count -gt 0) {
        $pythonProcesses | ForEach-Object {
            Write-Host "  - Process ID: $($_.Id), Command: $($_.CommandLine)" -ForegroundColor Green
        }
    } else {
        Write-Host "  - No Python processes found." -ForegroundColor Yellow
    }
    
    Write-Host "Streamlit processes:" -ForegroundColor Cyan
    if ($streamlitProcesses -and $streamlitProcesses.Count -gt 0) {
        $streamlitProcesses | ForEach-Object {
            Write-Host "  - Process ID: $($_.Id)" -ForegroundColor Green
        }
    } else {
        Write-Host "  - No Streamlit processes found." -ForegroundColor Yellow
    }
    
    # Check web interfaces
    Write-Host "Web interfaces:" -ForegroundColor Cyan
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8501" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        Write-Host "  - Chat Interface (http://localhost:8501): Available" -ForegroundColor Green
    } catch {
        Write-Host "  - Chat Interface (http://localhost:8501): Not available" -ForegroundColor Red
    }
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/metrics" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
        Write-Host "  - Metrics Dashboard (http://localhost:8000/metrics): Available" -ForegroundColor Green
    } catch {
        Write-Host "  - Metrics Dashboard (http://localhost:8000/metrics): Not available" -ForegroundColor Red
    }
    
    Write-Host "Press any key to continue..." -ForegroundColor DarkGray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

function Open-BrowserUrl {
    param (
        [Parameter(Mandatory=$true)]
        [string]$url,
        [Parameter(Mandatory=$false)]
        [string]$description = "Opening URL"
    )
    
    Write-Host "$description - $url" -ForegroundColor Yellow
    try {
        Start-Process $url
        Write-Host "Browser launched successfully." -ForegroundColor Green
    } catch {
        Write-Host "Error opening browser: $_" -ForegroundColor Red
        Write-Host "Try manually opening this URL in your browser: $url" -ForegroundColor Yellow
    }
}

function Execute-SqlQuery {
    param (
        [Parameter(Mandatory=$true)]
        [string]$query,
        [Parameter(Mandatory=$false)]
        [string]$description = "Executing query"
    )
    
    $queryScriptPath = Join-Path (Get-Location) "query_metrics_db.ps1"
    
    if (-not (Test-Path $queryScriptPath)) {
        Write-Host "Error: Cannot find query_metrics_db.ps1 at path: $queryScriptPath" -ForegroundColor Red
        Write-Host "Current directory: $(Get-Location)" -ForegroundColor Yellow
        Write-Host "Press any key to continue..." -ForegroundColor DarkGray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        return
    }
    
    Write-Host $description -ForegroundColor Magenta
    Write-Host "Query: $query" -ForegroundColor Blue
    & $queryScriptPath -query $query
    
    Write-Host "Press any key to continue..." -ForegroundColor DarkGray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Main script logic
switch ($action.ToLower()) {
    "start" {
        Start-ChatInterface
        Start-AdManager
        Start-MetricsDashboard
    }
    "stop" { Stop-AllServices }
    "chat" { Start-ChatInterface }
    "manager" { Start-AdManager }
    "metrics" { Start-MetricsDashboard }
    "menu" { Show-Menu }
    default {
        Write-Host "Invalid action. Available actions: start, stop, chat, manager, metrics, menu" -ForegroundColor Red
        exit 1
    }
} 