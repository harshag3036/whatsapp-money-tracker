#!/usr/bin/env python3
"""
Test script for Google Sheets API access.
This script tests if the service account can access the Google Sheet.
"""

import os
import json
import ssl
from googleapiclient.discovery import build
from google.oauth2 import service_account

# Disable SSL verification (temporary fix for SSL certificate issues)
ssl._create_default_https_context = ssl._create_unverified_context

# Constants
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1O4HXZ3qKlRuVodnpNDmuvzif3B5Hbo8xfZKpin5wLfM'

def test_service_account():
    """Test if the service account can access the Google Sheet."""
    print("Testing service account authentication...")
    
    # Get the service account file path
    service_account_path = 'service_account.json'
    
    if not os.path.exists(service_account_path):
        print(f"Error: {service_account_path} not found!")
        return False
    
    try:
        # Load the service account credentials
        print(f"Loading service account from {service_account_path}...")
        creds = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=SCOPES)
        print("Service account credentials loaded successfully.")
        
        # Print the service account email
        with open(service_account_path, 'r') as f:
            sa_info = json.load(f)
            print(f"Service account email: {sa_info.get('client_email', 'Not found')}")
        
        # Build the service
        print("Building Google Sheets API service...")
        service = build('sheets', 'v4', credentials=creds)
        print("Google Sheets API service built successfully.")
        
        # Test getting spreadsheet info
        print(f"Testing access to spreadsheet ID: {SPREADSHEET_ID}...")
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        print("Successfully accessed the spreadsheet!")
        print(f"Spreadsheet title: {spreadsheet.get('properties', {}).get('title', 'Unknown')}")
        
        # List the sheets in the spreadsheet
        print("\nSheets in this spreadsheet:")
        for sheet in spreadsheet.get('sheets', []):
            sheet_title = sheet.get('properties', {}).get('title', 'Unknown')
            sheet_id = sheet.get('properties', {}).get('sheetId', 'Unknown')
            print(f"- {sheet_title} (ID: {sheet_id})")
        
        # Try to create a test sheet
        print("\nAttempting to create a test sheet...")
        request = {
            'addSheet': {
                'properties': {
                    'title': 'Test_Sheet2',
                    'gridProperties': {
                        'rowCount': 10,
                        'columnCount': 5
                    }
                }
            }
        }
        
        try:
            response = service.spreadsheets().batchUpdate(
                spreadsheetId=SPREADSHEET_ID,
                body={'requests': [request]}
            ).execute()
            print("Test sheet created successfully!")
        except Exception as e:
            # The sheet might already exist, which is fine
            print(f"Note: Could not create test sheet: {e}")
        
        # Try to write to the spreadsheet
        print("\nAttempting to write to the spreadsheet...")
        values = [
            ['Timestamp', 'Test Value'],
            [str(import_time := __import__('datetime').datetime.now()), 'Test successful!']
        ]
        
        body = {
            'values': values
        }
        
        result = service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range='Test_Sheet!A1:B2',
            valueInputOption='RAW',
            body=body
        ).execute()
        
        print(f"Data written successfully! Updated {result.get('updatedCells')} cells.")
        return True
    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_service_account()
    print("\nTest result:", "SUCCESS" if success else "FAILED")
