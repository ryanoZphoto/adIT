#!/usr/bin/env python
"""
Update run_all.py Script

This script modifies the ad_service/run_all.py file to remove or disable
the code that copies files to c:\adserv directory.
"""

import os
import re
import shutil
import sys

def update_run_all():
    """Update run_all.py to remove file copying to c:\adserv"""
    # Path to the run_all.py file
    run_all_path = os.path.join('ad_service', 'run_all.py')
    
    # Check if the file exists
    if not os.path.exists(run_all_path):
        print(f"Error: Could not find {run_all_path}")
        return False
    
    # Create a backup of the original file
    backup_path = run_all_path + '.bak'
    try:
        shutil.copy2(run_all_path, backup_path)
        print(f"Created backup at {backup_path}")
    except Exception as e:
        print(f"Warning: Could not create backup: {e}")
    
    # Read the file content
    try:
        with open(run_all_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {run_all_path}: {e}")
        return False
    
    # Look for the c:\adserv file copying code
    pattern = re.compile(r'(# Check if c:\\adserv.*?except Exception as e:.*?print\(f"Error copying.*?\))', re.DOTALL)
    match = pattern.search(content)
    
    if not match:
        print(f"Could not find the c:\\adserv file copying code in {run_all_path}")
        return False
    
    # Replace the code with a commented-out version
    new_content = content.replace(match.group(1), 
        "# The following code has been disabled to prevent synchronization issues with c:\\adserv:\n'''\n" + 
        match.group(1) + 
        "\n'''")
    
    # Write the modified content back to the file
    try:
        with open(run_all_path, 'w') as f:
            f.write(new_content)
        print(f"Successfully updated {run_all_path}")
        print(f"The file copying code has been commented out.")
        return True
    except Exception as e:
        print(f"Error writing to {run_all_path}: {e}")
        print(f"You can manually restore from the backup at {backup_path}")
        return False

if __name__ == "__main__":
    print("This script will modify ad_service/run_all.py to remove the c:\\adserv file copying behavior.")
    print("A backup will be created before making any changes.")
    
    # Ask for confirmation
    print("\nDo you want to proceed? (y/n)")
    response = input().strip().lower()
    
    if response == 'y':
        success = update_run_all()
        if success:
            print("\nModification complete!")
            print("You should no longer experience synchronization issues between C:\\almostworks and c:\\adserv.")
        else:
            print("\nFailed to modify the file. Please check the error messages above.")
    else:
        print("Operation cancelled. No changes were made.") 