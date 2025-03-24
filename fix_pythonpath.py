#!/usr/bin/env python
"""
PYTHONPATH Fix Script

This script removes c:\adserv from the Python path and PYTHONPATH environment variable
to eliminate the directory synchronization issues.
"""

import sys
import os
import subprocess

def fix_pythonpath():
    """Remove c:\adserv from Python path and environment variable"""
    print("Checking Python path...")
    
    adserv_path = "c:\\adserv"
    # Check if c:\adserv is in the current Python path
    if adserv_path in sys.path:
        print(f"Found '{adserv_path}' in Python path")
        # Remove it from the current session's sys.path
        sys.path.remove(adserv_path)
        print(f"Removed '{adserv_path}' from current Python path")
    else:
        print(f"'{adserv_path}' not found in current Python path")
    
    # Check environment variable
    pythonpath = os.environ.get('PYTHONPATH', '')
    if adserv_path in pythonpath:
        print(f"Found '{adserv_path}' in PYTHONPATH environment variable")
        # Create new PYTHONPATH value
        paths = pythonpath.split(os.pathsep)
        new_paths = [p for p in paths if p.lower() != adserv_path.lower()]
        new_pythonpath = os.pathsep.join(new_paths)
        
        # Update environment variable for this session
        os.environ['PYTHONPATH'] = new_pythonpath
        print(f"Updated PYTHONPATH environment variable for current session")
        
        # Create PowerShell commands to update user environment variable permanently
        print("\nTo permanently remove c:\\adserv from your PYTHONPATH, run this in PowerShell as Administrator:")
        print("\n[Environment]::SetEnvironmentVariable('PYTHONPATH', '" + new_pythonpath + "', 'User')")
    else:
        print(f"'{adserv_path}' not found in PYTHONPATH environment variable")
    
    # Print the current Python path for verification
    print("\nCurrent Python path:")
    for path in sys.path:
        print(f"  {path}")

if __name__ == "__main__":
    fix_pythonpath()
    
    # Offer to update the run_all.py file to remove the copy behavior
    print("\nWould you like to update run_all.py to remove the file copying behavior? (y/n)")
    response = input().strip().lower()
    
    if response == 'y':
        try:
            run_all_path = os.path.join('ad_service', 'run_all.py')
            if os.path.exists(run_all_path):
                with open(run_all_path, 'r') as f:
                    content = f.read()
                
                # Find the section that does the copying and comment it out
                import re
                pattern = r"(# Check if c:\\adserv.*?except Exception as e:.*?print\(f\"Error copying.*?\))"
                replacement = "# The following code has been disabled to prevent synchronization issues:\n'''\n\\1\n'''"
                
                new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
                
                if new_content != content:
                    with open(run_all_path, 'w') as f:
                        f.write(new_content)
                    print(f"Updated {run_all_path} to remove file copying behavior.")
                else:
                    print(f"Could not locate the copying code in {run_all_path}.")
            else:
                print(f"Could not find {run_all_path}.")
        except Exception as e:
            print(f"Error updating run_all.py: {e}")
    
    print("\nDone! Your Python environment should now use only the C:\\almostworks directory for imports.") 