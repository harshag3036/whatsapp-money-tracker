"""
Main application file for the WhatsApp Money Tracker Bot.
This Flask application handles Twilio webhooks and implements the conversation flow.
"""

import os
import re
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Import our modules
from src.contacts import get_contact_by_id, get_all_contacts
from src.sheets_manager import add_transaction, get_balance_for_contact, generate_daily_report

# Initialize Flask app
app = Flask(__name__)

# Initialize Twilio client
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
ADMIN_PHONE_NUMBER = os.getenv('ADMIN_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# User session storage (in-memory for simplicity)
# In a production app, use a database
user_sessions = {}

# Define conversation states
STATES = {
    'INITIAL': 'initial',
    'AWAITING_CONTACT': 'awaiting_contact',
    'AWAITING_AMOUNT': 'awaiting_amount',
    'AWAITING_TYPE': 'awaiting_type',
    'AWAITING_CONFIRMATION': 'awaiting_confirmation',
    'COMPLETED': 'completed'
}

def get_or_create_session(phone_number):
    """Get or create a new user session."""
    if phone_number not in user_sessions:
        user_sessions[phone_number] = {
            'state': STATES['INITIAL'],
            'selected_contact': None,
            'amount': None,
            'transaction_type': None
        }
    return user_sessions[phone_number]

def reset_session(phone_number):
    """Reset a user session to initial state."""
    if phone_number in user_sessions:
        user_sessions[phone_number] = {
            'state': STATES['INITIAL'],
            'selected_contact': None,
            'amount': None,
            'transaction_type': None
        }
    return user_sessions[phone_number]

def create_contact_list_message():
    """Create an interactive list of contacts."""
    contacts = get_all_contacts()
    
    # Create a list of contacts with buttons
    contact_buttons = []
    for contact in contacts:
        contact_buttons.append({
            "type": "reply",
            "reply": {
                "id": f"contact_{contact['id']}",
                "title": contact['name']
            }
        })
    
    # Create the interactive message
    interactive_data = {
        "type": "button",
        "header": {
            "type": "text",
            "text": "Select a Contact"
        },
        "body": {
            "text": "Please select a contact from the list below:"
        },
        "action": {
            "buttons": contact_buttons[:3]  # WhatsApp allows max 3 buttons
        }
    }
    
    return interactive_data

def create_transaction_type_message(contact_name):
    """Create an interactive message for selecting transaction type."""
    interactive_data = {
        "type": "button",
        "header": {
            "type": "text",
            "text": f"Transaction with {contact_name}"
        },
        "body": {
            "text": f"Are you lending money to {contact_name} or borrowing from them?"
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": {
                        "id": "type_lend",
                        "title": "Lending"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "type_borrow",
                        "title": "Borrowing"
                    }
                }
            ]
        }
    }
    
    return interactive_data

def create_confirmation_message(contact_name, amount, transaction_type):
    """Create an interactive message for confirmation."""
    action = "lend to" if transaction_type == 'lend' else "borrow from"
    
    interactive_data = {
        "type": "button",
        "header": {
            "type": "text",
            "text": "Confirm Transaction"
        },
        "body": {
            "text": f"Please confirm:\n\nYou will {action} {contact_name} ₹{amount:.2f}"
        },
        "action": {
            "buttons": [
                {
                    "type": "reply",
                    "reply": {
                        "id": "confirm_yes",
                        "title": "Yes"
                    }
                },
                {
                    "type": "reply",
                    "reply": {
                        "id": "confirm_no",
                        "title": "No"
                    }
                }
            ]
        }
    }
    
    return interactive_data

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages."""
    # Get the message details
    incoming_msg = request.values.get('Body', '').strip()
    sender_phone = request.values.get('From', '')
    
    # Check for interactive message responses
    interactive_type = request.values.get('InteractiveType', '')
    interactive_id = request.values.get('InteractiveButtonId', '')
    
    # Get or create user session
    session = get_or_create_session(sender_phone)
    
    # Initialize response
    resp = MessagingResponse()
    message = resp.message()
    
    # Handle interactive responses
    if interactive_type == 'button_reply':
        if interactive_id.startswith('contact_'):
            # Extract contact ID from the button ID
            contact_id = int(interactive_id.split('_')[1])
            contact = get_contact_by_id(contact_id)
            
            if contact:
                session['selected_contact'] = contact
                session['state'] = STATES['AWAITING_TYPE']
                
                # Send interactive message for transaction type
                message.content_type = 'application/json'
                message.body = json.dumps({
                    "interactive": create_transaction_type_message(contact['name'])
                })
                return str(resp)
        
        elif interactive_id.startswith('type_'):
            # Extract transaction type from the button ID
            transaction_type = interactive_id.split('_')[1]
            
            if transaction_type in ['lend', 'borrow']:
                session['transaction_type'] = transaction_type
                session['state'] = STATES['AWAITING_AMOUNT']
                
                action = "lending to" if transaction_type == 'lend' else "borrowing from"
                message.body = f"You're {action} {session['selected_contact']['name']}. Please enter the amount:"
                return str(resp)
        
        elif interactive_id.startswith('confirm_'):
            # Extract confirmation from the button ID
            confirmation = interactive_id.split('_')[1]
            
            if confirmation == 'yes':
                # Add the transaction to Google Sheets
                success = add_transaction(
                    session['selected_contact']['id'],
                    session['selected_contact']['name'],
                    session['amount'],
                    session['transaction_type']
                )
                
                if success:
                    action = "lent to" if session['transaction_type'] == 'lend' else "borrowed from"
                    message.body = (
                        f"✅ Transaction recorded!\n\n"
                        f"You have {action} {session['selected_contact']['name']} ₹{session['amount']:.2f}\n\n"
                        f"Send 'start' to record another transaction."
                    )
                    
                    # Get updated balance
                    balance = get_balance_for_contact(session['selected_contact']['id'])
                    if balance > 0:
                        resp.message(f"{session['selected_contact']['name']} owes you ₹{abs(balance):.2f} in total.")
                    elif balance < 0:
                        resp.message(f"You owe {session['selected_contact']['name']} ₹{abs(balance):.2f} in total.")
                    else:
                        resp.message(f"Your balance with {session['selected_contact']['name']} is settled.")
                    
                    # Reset session
                    reset_session(sender_phone)
                else:
                    message.body = "❌ Error recording transaction. Please try again."
            
            elif confirmation == 'no':
                message.body = "Transaction cancelled. Send 'start' to begin again."
                reset_session(sender_phone)
            
            return str(resp)
    
    # Check for reset command
    if incoming_msg.lower() in ['reset', 'restart', 'cancel']:
        reset_session(sender_phone)
        message.body = "Session reset. Send 'start' to begin a new transaction."
        return str(resp)
    
    # Check for help command
    if incoming_msg.lower() in ['help', 'commands']:
        help_text = (
            "Available commands:\n"
            "- 'start': Begin a new transaction\n"
            "- 'reset': Reset the current session\n"
            "- 'balance': Check balances for all contacts\n"
            "- 'report': Generate today's report\n"
            "- 'help': Show this help message"
        )
        message.body = help_text
        return str(resp)
    
    # Check for balance command
    if incoming_msg.lower() == 'balance':
        # Get all contacts
        contacts = get_all_contacts()
        
        # Get balance for each contact
        balance_text = "Current balances:\n\n"
        for contact in contacts:
            balance = get_balance_for_contact(contact['id'])
            if balance > 0:
                balance_text += f"{contact['name']} owes you ₹{abs(balance):.2f}\n"
            elif balance < 0:
                balance_text += f"You owe {contact['name']} ₹{abs(balance):.2f}\n"
            else:
                balance_text += f"Your balance with {contact['name']} is settled\n"
        
        message.body = balance_text
        return str(resp)
    
    # Check for report command
    if incoming_msg.lower() == 'report':
        report = generate_daily_report()
        
        if report['transactions']:
            report_text = f"Daily Report for {report['transactions'][0]['date']}:\n\n"
            report_text += f"Total Lent: ₹{report['total_lent']:.2f}\n"
            report_text += f"Total Borrowed: ₹{report['total_borrowed']:.2f}\n"
            report_text += f"Net Amount: ₹{report['net_amount']:.2f}\n\n"
            
            report_text += "Transactions:\n"
            for transaction in report['transactions']:
                action = "Lent to" if transaction['type'] == 'lend' else "Borrowed from"
                report_text += f"- {action} {transaction['contact_name']}: ₹{transaction['amount']:.2f}\n"
            
            message.body = report_text
        else:
            message.body = "No transactions found for today."
        
        return str(resp)
    
    # Handle conversation based on current state
    if session['state'] == STATES['INITIAL']:
        if incoming_msg.lower() == 'start':
            session['state'] = STATES['AWAITING_CONTACT']
            
            # Send interactive message with contact list
            message.content_type = 'application/json'
            message.body = json.dumps({
                "interactive": create_contact_list_message()
            })
        else:
            message.body = "Welcome to Money Tracker! Send 'start' to begin a new transaction or 'help' for commands."
    
    elif session['state'] == STATES['AWAITING_CONTACT']:
        try:
            contact_id = int(incoming_msg)
            contact = get_contact_by_id(contact_id)
            if contact:
                session['selected_contact'] = contact
                session['state'] = STATES['AWAITING_TYPE']
                
                # Send interactive message for transaction type
                message.content_type = 'application/json'
                message.body = json.dumps({
                    "interactive": create_transaction_type_message(contact['name'])
                })
            else:
                message.body = "Invalid contact number. Please select from the list:"
                
                # Resend interactive message with contact list
                message.content_type = 'application/json'
                message.body = json.dumps({
                    "interactive": create_contact_list_message()
                })
        except ValueError:
            # If the user didn't enter a number, check if they entered a contact name
            contacts = get_all_contacts()
            matching_contacts = [c for c in contacts if c['name'].lower() == incoming_msg.lower()]
            
            if matching_contacts:
                contact = matching_contacts[0]
                session['selected_contact'] = contact
                session['state'] = STATES['AWAITING_TYPE']
                
                # Send interactive message for transaction type
                message.content_type = 'application/json'
                message.body = json.dumps({
                    "interactive": create_transaction_type_message(contact['name'])
                })
            else:
                message.body = "Please select a valid contact from the list."
                
                # Resend interactive message with contact list
                message.content_type = 'application/json'
                message.body = json.dumps({
                    "interactive": create_contact_list_message()
                })
    
    elif session['state'] == STATES['AWAITING_TYPE']:
        if incoming_msg.lower() in ['lend', 'borrow']:
            session['transaction_type'] = incoming_msg.lower()
            session['state'] = STATES['AWAITING_AMOUNT']
            action = "lending to" if incoming_msg.lower() == 'lend' else "borrowing from"
            message.body = f"You're {action} {session['selected_contact']['name']}. Please enter the amount:"
        else:
            message.body = "Please reply with either 'lend' or 'borrow'."
            
            # Resend interactive message for transaction type
            message.content_type = 'application/json'
            message.body = json.dumps({
                "interactive": create_transaction_type_message(session['selected_contact']['name'])
            })
    
    elif session['state'] == STATES['AWAITING_AMOUNT']:
        # Try to extract a valid amount
        amount_match = re.search(r'(\d+(\.\d+)?)', incoming_msg)
        if amount_match:
            try:
                amount = float(amount_match.group(1))
                session['amount'] = amount
                session['state'] = STATES['AWAITING_CONFIRMATION']
                
                # Send interactive message for confirmation
                message.content_type = 'application/json'
                message.body = json.dumps({
                    "interactive": create_confirmation_message(
                        session['selected_contact']['name'],
                        amount,
                        session['transaction_type']
                    )
                })
            except ValueError:
                message.body = "Invalid amount. Please enter a valid number."
        else:
            message.body = "Please enter a valid amount (numbers only)."
    
    elif session['state'] == STATES['AWAITING_CONFIRMATION']:
        if incoming_msg.lower() in ['yes', 'y', 'confirm']:
            # Add the transaction to Google Sheets
            success = add_transaction(
                session['selected_contact']['id'],
                session['selected_contact']['name'],
                session['amount'],
                session['transaction_type']
            )
            
            if success:
                action = "lent to" if session['transaction_type'] == 'lend' else "borrowed from"
                message.body = (
                    f"✅ Transaction recorded!\n\n"
                    f"You have {action} {session['selected_contact']['name']} ₹{session['amount']:.2f}\n\n"
                    f"Send 'start' to record another transaction."
                )
                
                # Get updated balance
                balance = get_balance_for_contact(session['selected_contact']['id'])
                if balance > 0:
                    resp.message(f"{session['selected_contact']['name']} owes you ₹{abs(balance):.2f} in total.")
                elif balance < 0:
                    resp.message(f"You owe {session['selected_contact']['name']} ₹{abs(balance):.2f} in total.")
                else:
                    resp.message(f"Your balance with {session['selected_contact']['name']} is settled.")
                
                # Reset session
                reset_session(sender_phone)
            else:
                message.body = "❌ Error recording transaction. Please try again."
        
        elif incoming_msg.lower() in ['no', 'n', 'cancel']:
            message.body = "Transaction cancelled. Send 'start' to begin again."
            reset_session(sender_phone)
        else:
            message.body = "Please reply with 'yes' to confirm or 'no' to cancel."
            
            # Resend interactive message for confirmation
            message.content_type = 'application/json'
            message.body = json.dumps({
                "interactive": create_confirmation_message(
                    session['selected_contact']['name'],
                    session['amount'],
                    session['transaction_type']
                )
            })
    
    return str(resp)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return json.dumps({"status": "healthy"}), 200, {'ContentType': 'application/json'}

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv('PORT', 5000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)
