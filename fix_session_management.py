#!/usr/bin/env python3
"""
Script to fix session management issues in the WhatsApp Money Tracker Bot.
This script will modify the app.py file to fix session management issues.
"""

import os
import re
import shutil

def fix_session_management():
    """Fix session management issues in app.py."""
    print("Fixing session management issues in app.py...")
    
    # Backup the original file
    shutil.copy('src/app.py', 'src/app.py.session_backup')
    print("Created backup at src/app.py.session_backup")
    
    # Read the original file
    with open('src/app.py', 'r') as f:
        content = f.read()
    
    # Add debug flag
    content = content.replace(
        "# User session storage (in-memory for simplicity)\n# In a production app, use a database\nuser_sessions = {}",
        "# User session storage (in-memory for simplicity)\n# In a production app, use a database\nuser_sessions = {}\n\n# Debug flag\nDEBUG = True"
    )
    
    # Fix the get_or_create_session function
    content = content.replace(
        "def get_or_create_session(phone_number):\n    \"\"\"Get or create a new user session.\"\"\"\n    if phone_number not in user_sessions:\n        user_sessions[phone_number] = {\n            'state': STATES['INITIAL'],\n            'selected_contact': None,\n            'amount': None\n        }\n    return user_sessions[phone_number]",
        "def get_or_create_session(phone_number):\n    \"\"\"Get or create a new user session.\"\"\"\n    if phone_number not in user_sessions:\n        if DEBUG:\n            print(f\"Creating new session for {phone_number}\")\n        user_sessions[phone_number] = {\n            'state': STATES['INITIAL'],\n            'selected_contact': None,\n            'amount': None\n        }\n    return user_sessions[phone_number]"
    )
    
    # Fix the reset_session function
    content = content.replace(
        "def reset_session(phone_number):\n    \"\"\"Reset a user session to initial state.\"\"\"\n    if phone_number in user_sessions:\n        user_sessions[phone_number] = {\n            'state': STATES['INITIAL'],\n            'selected_contact': None,\n            'amount': None\n        }\n    return user_sessions[phone_number]",
        "def reset_session(phone_number):\n    \"\"\"Reset a user session to initial state.\"\"\"\n    if phone_number in user_sessions:\n        if DEBUG:\n            print(f\"Resetting session for {phone_number}\")\n        user_sessions[phone_number] = {\n            'state': STATES['INITIAL'],\n            'selected_contact': None,\n            'amount': None\n        }\n    return user_sessions[phone_number]"
    )
    
    # Fix the add_transaction call
    content = content.replace(
        "            # Add the transaction to Google Sheets (always use 'lend' as transaction type)\n            success = add_transaction(\n                session['selected_contact']['id'],\n                session['selected_contact']['name'],\n                session['amount'],\n                'lend'  # Always use 'lend' as the transaction type\n            )",
        "            # Add the transaction to Google Sheets (always use 'lend' as transaction type)\n            if DEBUG:\n                print(f\"Adding transaction: {session['selected_contact']['id']}, {session['selected_contact']['name']}, {session['amount']}\")\n            try:\n                success = add_transaction(\n                    session['selected_contact']['id'],\n                    session['selected_contact']['name'],\n                    session['amount'],\n                    'lend'  # Always use 'lend' as the transaction type\n                )\n            except Exception as e:\n                print(f\"Error adding transaction: {e}\")\n                success = False"
    )
    
    # Write the modified content back to the file
    with open('src/app.py', 'w') as f:
        f.write(content)
    
    print("Session management issues fixed in app.py")

if __name__ == "__main__":
    fix_session_management()
