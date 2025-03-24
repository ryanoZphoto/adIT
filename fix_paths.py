#!/usr/bin/env python
"""
Path Structure Fix Script

This script performs a comprehensive fix of the ad service application to:
1. Remove all hardcoded references to c:\adserv
2. Ensure all paths are relative to the application directory
3. Update configuration files to use proper relative paths
4. Fix the database path to be within the ad_service directory structure
"""

import os
import re
import sys
import glob
import shutil
from pathlib import Path

# Define key directories and files
APP_ROOT = os.path.abspath(os.path.dirname(__file__))
AD_SERVICE_DIR = os.path.join(APP_ROOT, 'ad_service')

# Files that need to be checked/modified
TARGET_FILES = [
    os.path.join(AD_SERVICE_DIR, 'run_all.py'),
    os.path.join(AD_SERVICE_DIR, 'analytics', 'metrics_collector.py'),
    os.path.join(AD_SERVICE_DIR, 'analytics', 'dashboard.py'),
    os.path.join(AD_SERVICE_DIR, 'gui', 'main.py'),
    os.path.join(AD_SERVICE_DIR, 'api', 'ad_service_api.py'),
]

# Additional Python files to check
def find_python_files(directory):
    """Find all Python files in a directory recursively"""
    return glob.glob(os.path.join(directory, '**', '*.py'), recursive=True)

def create_backup(file_path):
    """Create a backup of a file"""
    backup_path = file_path + '.bak'
    try:
        shutil.copy2(file_path, backup_path)
        print(f"✓ Created backup: {backup_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create backup for {file_path}: {e}")
        return False

def fix_file_paths(file_path):
    """Fix hardcoded paths in a specific file"""
    if not os.path.exists(file_path):
        print(f"✗ File not found: {file_path}")
        return False
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Create a backup before modifying
    create_backup(file_path)
    
    original_content = content
    
    # Replace hardcoded path patterns
    patterns = [
        # Full paths replacements
        (r'["\']c:\\adserv["\']', 'os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")'),
        (r'["\']c:/adserv["\']', 'os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")'),
        (r'["\']c:\\adserv\\ad_service["\']', 'os.path.dirname(os.path.abspath(__file__))'),
        (r'["\']c:/adserv/ad_service["\']', 'os.path.dirname(os.path.abspath(__file__))'),
        
        # Database paths
        (r'c:\\adserv\\ad_service\\data\\metrics\.db', 'os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "metrics.db")'),
        (r'c:/adserv/ad_service/data/metrics\.db', 'os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "metrics.db")'),
        
        # File copying section
        (r'# Check if c:\\adserv is in the Python path[\s\S]*?except Exception as e:[\s\S]*?print\(f"Error copying.*?\)', 
         '# Removed c:\\adserv file copying code - using relative paths instead\n# All paths are now relative to the application directory'),
    ]
    
    # Apply replacements
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Check if we need to add os import
    if 'os.path' in content and 'import os' not in content:
        content = 'import os\n' + content
    
    # Ensure import sys exists if we use sys.path
    if 'sys.path' in content and 'import sys' not in content:
        content = 'import sys\n' + content
    
    # Only write if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Updated file: {file_path}")
        return True
    else:
        print(f"ℹ No changes needed for: {file_path}")
        return False

def fix_data_directory():
    """Ensure data directory exists with proper structure"""
    data_dir = os.path.join(AD_SERVICE_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Ensure ads.json exists
    ads_json = os.path.join(data_dir, 'ads.json')
    if not os.path.exists(ads_json):
        print(f"ℹ Creating default ads.json in {data_dir}")
        # Just touch the file if it doesn't exist (or copy from c:\adserv if available)
        with open(ads_json, 'w') as f:
            f.write('{"ads": []}')
    
    # Check for c:\adserv metrics.db and copy if exists
    adserv_db = r'c:\adserv\ad_service\data\metrics.db'
    local_db = os.path.join(data_dir, 'metrics.db')
    
    if not os.path.exists(local_db) and os.path.exists(adserv_db):
        try:
            shutil.copy2(adserv_db, local_db)
            print(f"✓ Copied metrics database from {adserv_db} to {local_db}")
        except Exception as e:
            print(f"✗ Failed to copy metrics database: {e}")
    elif not os.path.exists(local_db):
        # Just create an empty file
        print(f"ℹ Creating empty metrics.db in {data_dir}")
        Path(local_db).touch()
    
    print(f"✓ Data directory setup complete: {data_dir}")

def remove_adserv_from_pythonpath():
    """Remove c:\adserv from Python path and check environment variables"""
    # For current session
    adserv_path = r'c:\adserv'
    if adserv_path in sys.path:
        sys.path.remove(adserv_path)
        print(f"✓ Removed '{adserv_path}' from current Python path")
    
    # Check environment variable
    pythonpath = os.environ.get('PYTHONPATH', '')
    if adserv_path in pythonpath:
        paths = pythonpath.split(os.pathsep)
        new_paths = [p for p in paths if p.lower() != adserv_path.lower()]
        new_pythonpath = os.pathsep.join(new_paths)
        
        # Update environment variable for this session
        os.environ['PYTHONPATH'] = new_pythonpath
        print(f"✓ Updated PYTHONPATH environment variable for current session")
        
        print("\nTo permanently remove c:\\adserv from your PYTHONPATH, run this in PowerShell as Administrator:")
        print(f"[Environment]::SetEnvironmentVariable('PYTHONPATH', '{new_pythonpath}', 'User')")
    
    print("✓ Python path cleanup complete")

def main():
    """Main function to fix all paths"""
    print("=" * 80)
    print("AD SERVICE PATH STRUCTURE FIX")
    print("=" * 80)
    print("This script will fix all hardcoded paths in the ad service application.")
    print("Backups will be created for all modified files.")
    print()
    
    # Fix explicit target files first
    print("Fixing paths in key files:")
    for file_path in TARGET_FILES:
        if os.path.exists(file_path):
            fix_file_paths(file_path)
        else:
            print(f"✗ File not found: {file_path}")
    
    # Find and fix all other Python files
    print("\nScanning for additional Python files...")
    python_files = find_python_files(AD_SERVICE_DIR)
    for file_path in python_files:
        if file_path not in TARGET_FILES and not file_path.endswith('.bak'):
            fix_file_paths(file_path)
    
    # Ensure data directory is properly set up
    print("\nSetting up data directory structure...")
    fix_data_directory()
    
    # Remove from Python path
    print("\nChecking Python path...")
    remove_adserv_from_pythonpath()
    
    print("\n" + "=" * 80)
    print("FIX COMPLETE")
    print("=" * 80)
    print("The ad service application has been updated to use relative paths.")
    print("Any new ads added to ad_service/data/ads.json should now work properly.")
    print("You can now run the application with: python ad_service/run_all.py")
    print("\nIf you encounter any issues, you can restore from the .bak files.")

if __name__ == "__main__":
    main() 