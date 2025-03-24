# Create necessary directories if they don't exist
Write-Host "Creating necessary directories..." -ForegroundColor Yellow
$directories = @(
    "config",
    "companies",
    "ad_service",
    "charts",
    "logs",
    ".streamlit"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        Write-Host "Creating directory: $dir" -ForegroundColor Yellow
        New-Item -ItemType Directory -Path $dir | Out-Null
        # Create a placeholder file to ensure directory is included
        Set-Content -Path "$dir\placeholder.txt" -Value "Placeholder file to ensure directory is included in build" -Encoding UTF8
    }
}

# Clean previous build files
Write-Host "Cleaning previous build files..." -ForegroundColor Yellow
if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
}
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
}
if (Test-Path "*.spec") {
    Remove-Item -Path "*.spec" -Force
}

# Install PyInstaller if not already installed
Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
& python -m pip install pyinstaller

# Create a simple entry script to set environment variables
$entryScript = @"
import os
import sys
import subprocess
import tempfile
import shutil
import atexit

def main():
    # Set root directory to where the executable is located
    exe_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    os.environ['AD_SERVICE_ROOT'] = exe_dir
    
    # Create working directory next to executable if it doesn't exist
    work_dir = os.path.join(exe_dir, 'ad_service_data')
    if not os.path.exists(work_dir):
        os.makedirs(work_dir)
    
    # Extract bundled files to the working directory if needed
    for dir_name in ['config', 'companies', 'ad_service', 'charts', 'logs', '.streamlit']:
        if not os.path.exists(os.path.join(work_dir, dir_name)):
            src_dir = os.path.join(exe_dir, dir_name)
            if os.path.exists(src_dir):
                shutil.copytree(src_dir, os.path.join(work_dir, dir_name))
    
    # Set current directory to working directory
    os.chdir(work_dir)
    
    # Launch the main application
    from ad_service.start_service import main as start_service_main
    start_service_main()

if __name__ == '__main__':
    main()
"@

Set-Content -Path "ad_service_launcher.py" -Value $entryScript -Encoding UTF8

# Create a temporary PyInstaller spec file directly
$specFileContent = @"
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['ad_service_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('config', 'config'),
        ('companies', 'companies'),
        ('ad_service', 'ad_service'),
        ('charts', 'charts'),
        ('logs', 'logs'),
        ('.streamlit', '.streamlit'),
        ('setup.ps1', '.'),
        ('start_ad_service.ps1', '.'),
        ('set_env.ps1', '.'),
        ('requirements.txt', '.'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'streamlit',
        'yaml',
        'openai',
        'flask',
        'flask_restful',
        'sqlalchemy',
        'pandas',
        'numpy',
        'matplotlib',
        'seaborn',
        'plotly',
        'nltk',
        'python-dotenv',
        'pydantic',
        'requests',
        'jinja2',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AdService',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
"@

Set-Content -Path "AdService.spec" -Value $specFileContent -Encoding UTF8

# Build the executable using the spec file
Write-Host "Building executable..." -ForegroundColor Yellow
Write-Host "Using custom spec file instead of command-line arguments" -ForegroundColor Cyan
& pyinstaller AdService.spec

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nBuild complete! The executable is located in the dist folder." -ForegroundColor Green
    Write-Host "You can now distribute the AdService.exe file." -ForegroundColor Green
    
    # Create dist directory if it doesn't exist (it should exist but just to be safe)
    if (-not (Test-Path "dist")) {
        New-Item -ItemType Directory -Path "dist" | Out-Null
    }
    
    # Create a README in the dist folder
    $readme = @"
Ad Service Executable
====================

This executable contains everything needed to run the Ad Service.

To start:
1. Double-click AdService.exe
2. Enter your OpenAI API key when prompted
3. The service will automatically:
   - Create a working directory (ad_service_data) next to the executable
   - Set up all required files and configurations
   - Start all necessary services
   - Open your browser to:
     * Chat Interface (http://localhost:8501)
     * Ad Manager (http://localhost:8502)
     * Metrics Dashboard (http://localhost:8503)

IMPORTANT: The first run may take longer as it sets up all necessary components.

No installation or Python knowledge required!
"@
    
    Set-Content -Path "dist\README.txt" -Value $readme -Encoding UTF8

    # Create a simple batch file to launch the executable (with correct encoding)
    $batchLauncher = @"
@echo off
echo Starting Ad Service...
start "" "%~dp0AdService.exe"
echo Opening browser in 5 seconds...
timeout /t 5 > nul
start "" http://localhost:8501
"@

    Set-Content -Path "dist\Start_AdService.bat" -Value $batchLauncher -Encoding ASCII
} else {
    Write-Error "Build failed with exit code: $LASTEXITCODE"
    exit $LASTEXITCODE
} 