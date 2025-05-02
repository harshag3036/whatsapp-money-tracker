"""
Google Sheets manager module for the WhatsApp Money Tracker Bot.
This module handles all Google Sheets operations for storing transaction data.
"""

import os
import ssl
import json
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Constants

# Disable SSL verification (temporary fix for SSL certificate issues)
ssl._create_default_https_context = ssl._create_unverified_context
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1O4HXZ3qKlRuVodnpNDmuvzif3B5Hbo8xfZKpin5wLfM'  # The ID from the provided Google Sheet URL

def get_credentials():
    """
    Get Google Sheets API credentials.
    
    Returns:
        Credentials object for Google Sheets API
    """
    # Use service account authentication (best for production)
    service_account_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'service_account.json')
    
    if not os.path.exists(service_account_path):
        raise FileNotFoundError(
            f"Service account file not found at {service_account_path}. "
            "Please follow the setup instructions in GOOGLE_SHEETS_SETUP.md"
        )
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=SCOPES)
        print(f"Using service account authentication from {service_account_path}")
        return creds
    except Exception as e:
        raise Exception(f"Error using service account: {e}")

def get_service():
    """
    Get Google Sheets API service.
    
    Returns:
        Google Sheets API service
    """
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    return service

def get_or_create_sheet_for_date(date=None):
    """
    Get or create a sheet for the specified date.
    
    Args:
        date (str, optional): Date in 'YYYY-MM-DD' format. Defaults to today.
        
    Returns:
        str: Sheet name
    """
    # Use today's date if not specified
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    sheet_name = f"Transactions_{date}"
    
    # Get the spreadsheet
    service = get_service()
    spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
    
    # Check if the sheet already exists
    sheet_exists = False
    for sheet in spreadsheet.get('sheets', []):
        if sheet.get('properties', {}).get('title') == sheet_name:
            sheet_exists = True
            break
    
    # Create the sheet if it doesn't exist
    if not sheet_exists:
        request = {
            'addSheet': {
                'properties': {
                    'title': sheet_name,
                    'gridProperties': {
                        'rowCount': 1000,
                        'columnCount': 7
                    }
                }
            }
        }
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=SPREADSHEET_ID,
            body={'requests': [request]}
        ).execute()
        
        # Add headers
        headers = [
            ['Date', 'Time', 'Contact ID', 'Contact Name', 'Amount', 'Type', 'Notes']
        ]
        
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A1:G1",
            valueInputOption='RAW',
            body={'values': headers}
        ).execute()
    
    return sheet_name

def add_transaction(contact_id, contact_name, amount, transaction_type='lend', notes=''):
    """
    Add a new transaction to the Google Sheet.
    
    Args:
        contact_id (int): ID of the contact
        contact_name (str): Name of the contact
        amount (float): Amount of money involved
        transaction_type (str): 'lend' or 'borrow'
        notes (str): Any additional notes
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Current date and time
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        # Get or create sheet for today
        sheet_name = get_or_create_sheet_for_date(date_str)
        
        # Get the service
        service = get_service()
        
        # Get the last row with data
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:A"
        ).execute()
        
        values = result.get('values', [])
        next_row = len(values) + 1
        
        # Create new row
        new_row = [
            date_str,
            time_str,
            contact_id,
            contact_name,
            float(amount),
            transaction_type,
            notes
        ]
        
        # Append the row
        service.spreadsheets().values().update(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A{next_row}:G{next_row}",
            valueInputOption='RAW',
            body={'values': [new_row]}
        ).execute()
        
        return True
    except Exception as e:
        print(f"Error adding transaction to Google Sheet: {e}")
        return False

def get_balance_for_contact(contact_id):
    """
    Calculate the current balance for a specific contact across all sheets.
    
    Args:
        contact_id (int): ID of the contact
        
    Returns:
        float: Current balance (positive means they owe you, negative means you owe them)
    """
    try:
        # Get the service
        service = get_service()
        
        # Get all sheets
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        
        total_lent = 0.0
        total_borrowed = 0.0
        
        # Loop through all transaction sheets
        for sheet in spreadsheet.get('sheets', []):
            sheet_name = sheet.get('properties', {}).get('title')
            
            # Skip non-transaction sheets
            if not sheet_name.startswith('Transactions_'):
                continue
            
            # Get all values from the sheet
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{sheet_name}!A:G"
            ).execute()
            
            values = result.get('values', [])
            
            # Skip empty sheets or sheets with only headers
            if len(values) <= 1:
                continue
            
            # Skip the header row
            for row in values[1:]:
                # Skip rows that don't have enough columns
                if len(row) < 7:
                    continue
                
                # Check if this row is for the specified contact
                if str(row[2]) == str(contact_id):
                    # Add to lent or borrowed total
                    if row[5] == 'lend':
                        total_lent += float(row[4])
                    elif row[5] == 'borrow':
                        total_borrowed += float(row[4])
        
        # Calculate balance
        return total_lent - total_borrowed
    except Exception as e:
        print(f"Error calculating balance: {e}")
        return 0.0

def generate_daily_report(date=None):
    """
    Generate a summary of transactions for a specific date.
    
    Args:
        date (str, optional): Date in 'YYYY-MM-DD' format. Defaults to today.
        
    Returns:
        dict: Summary of transactions
    """
    try:
        # Use today's date if not specified
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        sheet_name = f"Transactions_{date}"
        
        # Get the service
        service = get_service()
        
        # Check if the sheet exists
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        sheet_exists = False
        for sheet in spreadsheet.get('sheets', []):
            if sheet.get('properties', {}).get('title') == sheet_name:
                sheet_exists = True
                break
        
        if not sheet_exists:
            return {
                'total_lent': 0,
                'total_borrowed': 0,
                'net_amount': 0,
                'transactions': []
            }
        
        # Get all values from the sheet
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:G"
        ).execute()
        
        values = result.get('values', [])
        
        # Skip empty sheets or sheets with only headers
        if len(values) <= 1:
            return {
                'total_lent': 0,
                'total_borrowed': 0,
                'net_amount': 0,
                'transactions': []
            }
        
        # Process transactions
        transactions = []
        total_lent = 0
        total_borrowed = 0
        
        # Skip the header row
        for row in values[1:]:
            # Skip rows that don't have enough columns
            if len(row) < 7:
                continue
            
            transaction = {
                'date': row[0],
                'time': row[1],
                'contact_id': row[2],
                'contact_name': row[3],
                'amount': float(row[4]),
                'type': row[5],
                'notes': row[6] if len(row) > 6 else ''
            }
            
            transactions.append(transaction)
            
            # Add to totals
            if transaction['type'] == 'lend':
                total_lent += transaction['amount']
            elif transaction['type'] == 'borrow':
                total_borrowed += transaction['amount']
        
        # Calculate net amount
        net_amount = total_lent - total_borrowed
        
        return {
            'total_lent': total_lent,
            'total_borrowed': total_borrowed,
            'net_amount': net_amount,
            'transactions': transactions
        }
    except Exception as e:
        print(f"Error generating daily report: {e}")
        return {
            'total_lent': 0,
            'total_borrowed': 0,
            'net_amount': 0,
            'transactions': []
        }
