#!/usr/bin/env python
"""
System PYTHONPATH Fix Script

This script permanently removes c:\adserv from the system PYTHONPATH environment variable.
It creates and runs a PowerShell script with admin privileges to make the change.
"""

import os
import sys
import tempfile
import subprocess

def create_powershell_script():
    """Create a PowerShell script to modify PYTHONPATH environment variable"""
    
    script_content = """
# PowerShell script to remove c:\adserv from PYTHONPATH
# Gets current PYTHONPATH, removes c:\adserv, and sets the new value

$currentPath = [Environment]::GetEnvironmentVariable('PYTHONPATH', 'User')
Write-Host "Current PYTHONPATH: $currentPath"

if ($currentPath -ne $null) {
    # Split the path and remove c:\adserv
    $paths = $currentPath -split ';'
    $newPaths = $paths | Where-Object { $_ -ne 'c:\adserv' -and $_ -ne 'c:\\adserv' }
    $newPath = $newPaths -join ';'
    
    # Set the new PYTHONPATH
    [Environment]::SetEnvironmentVariable('PYTHONPATH', $newPath, 'User')
    Write-Host "Updated PYTHONPATH: $newPath"
} else {
    Write-Host "PYTHONPATH is not set or is empty."
}

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
"""
    
    # Create a temporary PowerShell script file
    temp_dir = tempfile.gettempdir()
    script_path = os.path.join(temp_dir, "remove_adserv_from_pythonpath.ps1")
    
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    return script_path

def main():
    print("Creating PowerShell script to permanently remove c:\\adserv from PYTHONPATH...")
    script_path = create_powershell_script()
    
    print(f"PowerShell script created at: {script_path}")
    print("\nTo run this script and permanently remove c:\\adserv from your PYTHONPATH:")
    print(f"1. Open a PowerShell window as Administrator")
    print(f"2. Run: powershell -ExecutionPolicy Bypass -File \"{script_path}\"")
    
    # Ask if the user wants to run the script now
    print("\nWould you like to try running the script now? (y/n)")
    print("Note: This may prompt for administrator privileges.")
    response = input().strip().lower()
    
    if response == 'y':
        try:
            # Try to run PowerShell with admin rights
            cmd = [
                'powershell', 
                '-ExecutionPolicy', 'Bypass',
                '-Command', 
                f'Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File \"{script_path}\"" -Verb RunAs'
            ]
            subprocess.run(cmd)
            print("\nPowerShell command executed. Check the PowerShell window for results.")
        except Exception as e:
            print(f"Error running PowerShell: {e}")
            print(f"Please run the script manually as described above.")
    
    print("\nAfter making these changes, you may need to restart your computer")
    print("or any IDE/terminal sessions for the changes to take effect.")

if __name__ == "__main__":
    main() 