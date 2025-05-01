#!/usr/bin/env python3
"""
Simple test script for Google Sheets API access using requests library.
This bypasses some of the complexity of the Google API client libraries.
"""

import os
import json
import ssl
import time
import requests
import jwt  # You may need to install this: pip install PyJWT

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

# Load service account key
with open('service_account.json', 'r') as f:
    service_account_info = json.load(f)

print(f"Service account email: {service_account_info.get('client_email')}")

# Create JWT token
def create_jwt_token(service_account_info):
    """Create a JWT token for Google API authentication."""
    token_lifetime = 3600  # 1 hour
    now = int(time.time())
    
    # Create the JWT claims
    claims = {
        'iss': service_account_info['client_email'],
        'scope': 'https://www.googleapis.com/auth/spreadsheets',
        'aud': 'https://oauth2.googleapis.com/token',
        'exp': now + token_lifetime,
        'iat': now
    }
    
    # Sign the JWT
    signed_jwt = jwt.encode(
        claims,
        service_account_info['private_key'],
        algorithm='RS256'
    )
    
    return signed_jwt

# Get access token
def get_access_token(signed_jwt):
    """Exchange JWT for access token."""
    url = 'https://oauth2.googleapis.com/token'
    data = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': signed_jwt
    }
    
    response = requests.post(url, data=data, verify=False)
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Error getting access token: {response.status_code}")
        print(response.text)
        return None

# Test access to Google Sheets
def test_sheets_access(access_token, spreadsheet_id):
    """Test access to Google Sheets API."""
    url = f'https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}'
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(url, headers=headers, verify=False)
    if response.status_code == 200:
        print("Successfully accessed the spreadsheet!")
        spreadsheet_info = response.json()
        print(f"Spreadsheet title: {spreadsheet_info.get('properties', {}).get('title', 'Unknown')}")
        
        # List sheets
        print("\nSheets in this spreadsheet:")
        for sheet in spreadsheet_info.get('sheets', []):
            sheet_title = sheet.get('properties', {}).get('title', 'Unknown')
            sheet_id = sheet.get('properties', {}).get('sheetId', 'Unknown')
            print(f"- {sheet_title} (ID: {sheet_id})")
        
        return True
    else:
        print(f"Error accessing spreadsheet: {response.status_code}")
        print(response.text)
        return False

# Main test function
def main():
    """Main test function."""
    spreadsheet_id = '1O4HXZ3qKlRuVodnpNDmuvzif3B5Hbo8xfZKpin5wLfM'
    
    print("Creating JWT token...")
    signed_jwt = create_jwt_token(service_account_info)
    
    print("Getting access token...")
    access_token = get_access_token(signed_jwt)
    
    if access_token:
        print("Access token obtained successfully.")
        print("Testing access to Google Sheets...")
        success = test_sheets_access(access_token, spreadsheet_id)
        print("\nTest result:", "SUCCESS" if success else "FAILED")
    else:
        print("Failed to get access token.")
        print("\nTest result: FAILED")

if __name__ == "__main__":
    main()
