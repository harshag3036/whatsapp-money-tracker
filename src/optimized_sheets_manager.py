"""
Optimized Google Sheets manager module for the WhatsApp Money Tracker Bot.
This module handles all Google Sheets operations with reduced memory usage.
"""

import os
import ssl
from datetime import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('sheets_manager')

# Constants
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '1O4HXZ3qKlRuVodnpNDmuvzif3B5Hbo8xfZKpin5wLfM'

# Disable SSL verification (temporary fix for SSL certificate issues)
ssl._create_default_https_context = ssl._create_unverified_context

def get_service():
    """
    Get Google Sheets API service with simplified error handling.
    
    Returns:
        Google Sheets API service or None if error
    """
    try:
        # Use direct path to service account file
        service_account_path = 'service_account.json'
        
        if not os.path.exists(service_account_path):
            logger.error(f"Service account file not found at {service_account_path}")
            return None
        
        creds = service_account.Credentials.from_service_account_file(
            service_account_path, scopes=SCOPES)
        
        service = build('sheets', 'v4', credentials=creds)
        return service
    except Exception as e:
        logger.error(f"Error getting Google Sheets service: {e}")
        return None

def add_transaction(contact_id, contact_name, amount, transaction_type='lend', notes=''):
    """
    Add a new transaction to the Google Sheet with optimized memory usage.
    
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
        # Get the service
        service = get_service()
        if not service:
            logger.error("Failed to get Google Sheets service")
            return False
        
        # Current date and time
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        time_str = now.strftime('%H:%M:%S')
        
        # Sheet name for today
        sheet_name = f"Transactions_{date_str}"
        
        # Check if the sheet exists
        try:
            # Try to get the sheet - if it doesn't exist, we'll get an error
            service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{sheet_name}!A1"
            ).execute()
            
            logger.info(f"Sheet {sheet_name} exists")
        except Exception:
            # Sheet doesn't exist, create it
            logger.info(f"Creating new sheet {sheet_name}")
            
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
        
        # Append the transaction directly without getting the last row
        # This uses less memory and is more efficient
        new_row = [
            [date_str, time_str, contact_id, contact_name, float(amount), transaction_type, notes]
        ]
        
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{sheet_name}!A:G",
            valueInputOption='RAW',
            insertDataOption='INSERT_ROWS',
            body={'values': new_row}
        ).execute()
        
        logger.info(f"Transaction added successfully: {contact_name}, {amount}")
        return True
    
    except Exception as e:
        logger.error(f"Error adding transaction: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def get_balance_for_contact(contact_id):
    """
    Calculate the current balance for a specific contact.
    Simplified version that uses less memory.
    
    Args:
        contact_id (int): ID of the contact
        
    Returns:
        float: Current balance
    """
    try:
        # Get the service
        service = get_service()
        if not service:
            return 0.0
        
        # Get all sheets
        spreadsheet = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        
        total_lent = 0.0
        total_borrowed = 0.0
        
        # Process only the most recent 5 transaction sheets to save memory
        transaction_sheets = []
        for sheet in spreadsheet.get('sheets', []):
            sheet_name = sheet.get('properties', {}).get('title')
            if sheet_name.startswith('Transactions_'):
                transaction_sheets.append(sheet_name)
        
        # Sort by date (newest first) and take only the most recent 5
        transaction_sheets.sort(reverse=True)
        recent_sheets = transaction_sheets[:5]
        
        for sheet_name in recent_sheets:
            # Get values for this contact only using a filter
            range_name = f"{sheet_name}!A:G"
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if len(values) <= 1:
                continue
            
            # Process transactions (skip header)
            for row in values[1:]:
                if len(row) < 6:
                    continue
                
                # Check if this is for our contact
                if str(row[2]) == str(contact_id):
                    try:
                        amount = float(row[4])
                        if row[5] == 'lend':
                            total_lent += amount
                        elif row[5] == 'borrow':
                            total_borrowed += amount
                    except (ValueError, IndexError):
                        continue
        
        return total_lent - total_borrowed
    
    except Exception as e:
        logger.error(f"Error calculating balance: {e}")
        return 0.0

def generate_daily_report(date=None):
    """
    Generate a summary of transactions for a specific date.
    Simplified version that uses less memory.
    
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
        if not service:
            return {'total_lent': 0, 'total_borrowed': 0, 'net_amount': 0, 'transactions': []}
        
        # Check if the sheet exists by trying to get its values
        try:
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=f"{sheet_name}!A:G"
            ).execute()
        except Exception:
            # Sheet doesn't exist
            return {'total_lent': 0, 'total_borrowed': 0, 'net_amount': 0, 'transactions': []}
        
        values = result.get('values', [])
        if len(values) <= 1:
            return {'total_lent': 0, 'total_borrowed': 0, 'net_amount': 0, 'transactions': []}
        
        # Process transactions
        transactions = []
        total_lent = 0
        total_borrowed = 0
        
        # Skip the header row
        for row in values[1:]:
            if len(row) < 6:
                continue
            
            try:
                amount = float(row[4])
                transaction = {
                    'date': row[0],
                    'time': row[1],
                    'contact_id': row[2],
                    'contact_name': row[3],
                    'amount': amount,
                    'type': row[5],
                    'notes': row[6] if len(row) > 6 else ''
                }
                
                transactions.append(transaction)
                
                if row[5] == 'lend':
                    total_lent += amount
                elif row[5] == 'borrow':
                    total_borrowed += amount
            except (ValueError, IndexError):
                continue
        
        return {
            'total_lent': total_lent,
            'total_borrowed': total_borrowed,
            'net_amount': total_lent - total_borrowed,
            'transactions': transactions
        }
    
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return {'total_lent': 0, 'total_borrowed': 0, 'net_amount': 0, 'transactions': []}
