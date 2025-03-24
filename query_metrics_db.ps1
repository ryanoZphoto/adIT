# PowerShell script to query metrics.db database
param (
    [string]$query = ".tables",
    [string]$dbPath = "ad_service\data\metrics.db"
)

# Check if SQLite is installed in the system
function Test-SqliteInstalled {
    try {
        $null = Get-Command sqlite3 -ErrorAction Stop
        return $true
    } catch {
        return $false
    }
}

# Download SQLite if not installed
function Get-SqliteInstalled {
    $tempFolder = "$env:TEMP\sqlite_temp"
    $sqliteZip = "$tempFolder\sqlite.zip"
    $sqliteFolder = "$tempFolder\sqlite-tools"
    
    # Create temp folder if it doesn't exist
    if (-not (Test-Path $tempFolder)) {
        New-Item -ItemType Directory -Path $tempFolder | Out-Null
    }
    
    # Download and extract SQLite
    Write-Host "Downloading SQLite tools..."
    Invoke-WebRequest -Uri "https://sqlite.org/2022/sqlite-tools-win32-x86-3400100.zip" -OutFile $sqliteZip
    
    # Create extraction folder
    if (-not (Test-Path $sqliteFolder)) {
        New-Item -ItemType Directory -Path $sqliteFolder | Out-Null
    }
    
    # Extract the ZIP file
    Write-Host "Extracting SQLite tools..."
    Expand-Archive -Path $sqliteZip -DestinationPath $sqliteFolder -Force
    
    # Return the path to sqlite3.exe
    return (Get-ChildItem -Path $sqliteFolder -Recurse -Filter "sqlite3.exe").FullName
}

# Main function to run SQLite query
function Run-SqliteQuery {
    param (
        [string]$sqlitePath,
        [string]$database,
        [string]$sqlQuery
    )
    
    Write-Host "Running query: $sqlQuery"
    Write-Host "On database: $database"
    Write-Host "------------------------"
    
    & $sqlitePath $database $sqlQuery
}

# Main script execution
if (Test-SqliteInstalled) {
    $sqlitePath = "sqlite3"
} else {
    Write-Host "SQLite is not installed. Downloading temporary version..."
    $sqlitePath = Get-SqliteInstalled
}

# Ensure database path exists
if (-not (Test-Path $dbPath)) {
    Write-Host "Error: Database file not found at $dbPath"
    Write-Host "Please ensure the path is correct."
    exit 1
}

# Run the query
Run-SqliteQuery -sqlitePath $sqlitePath -database $dbPath -sqlQuery $query

# Display helpful information
if ($query -eq ".tables") {
    Write-Host "`n------------------------"
    Write-Host "Helpful commands:"
    Write-Host "------------------------"
    Write-Host "1. Show all tables: .tables"
    Write-Host "2. Show table schema: .schema table_name"
    Write-Host "3. Show all data in a table: SELECT * FROM table_name;"
    Write-Host "4. Show recent ad impressions: SELECT * FROM ad_impressions ORDER BY timestamp DESC LIMIT 10;"
    Write-Host "5. Show system metrics: SELECT * FROM events WHERE event_type = 'system_metrics' LIMIT 10;"
    Write-Host "6. Export data to CSV: .mode csv `n .output data.csv `n SELECT * FROM table_name;"
    Write-Host "------------------------"
    Write-Host "To use these commands, run: ./query_metrics_db.ps1 -query ""YOUR_QUERY_HERE"""
} 