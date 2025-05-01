#!/usr/bin/env python3
"""
Fix SSL certificate verification issues in sheets_manager.py.
This script adds SSL verification bypass to the sheets_manager.py file.
"""

import os
import re

def fix_sheets_manager():
    """Add SSL verification bypass to sheets_manager.py."""
    sheets_manager_path = os.path.join('src', 'sheets_manager.py')
    
    if not os.path.exists(sheets_manager_path):
        print(f"Error: {sheets_manager_path} not found!")
        return False
    
    # Read the file
    with open(sheets_manager_path, 'r') as f:
        content = f.read()
    
    # Check if the fix is already applied
    if "ssl._create_default_https_context = ssl._create_unverified_context" in content:
        print("SSL verification bypass already applied to sheets_manager.py")
        return True
    
    # Add the import if needed
    if "import ssl" not in content:
        content = re.sub(
            r'(import .*?\n)',
            r'\1import ssl\n',
            content,
            count=1
        )
    
    # Add the SSL verification bypass
    content = re.sub(
        r'(# Constants\n)',
        r'\1\n# Disable SSL verification (temporary fix for SSL certificate issues)\nssl._create_default_https_context = ssl._create_unverified_context\n',
        content
    )
    
    # Write the modified content back to the file
    with open(sheets_manager_path, 'w') as f:
        f.write(content)
    
    print("SSL verification bypass added to sheets_manager.py")
    print("Note: This is a temporary fix. For production, proper SSL certificates should be installed.")
    return True

if __name__ == "__main__":
    fix_sheets_manager()
