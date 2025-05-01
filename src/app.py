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
from src.contacts import get_contact_by_id, format_contacts_list
from src.excel_manager import add_transaction, get_balance_for_contact, generate_daily_report

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

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages."""
    # Get the message details
    incoming_msg = request.values.get('Body', '').strip()
    sender_phone = request.values.get('From', '')
    
    # Get or create user session
    session = get_or_create_session(sender_phone)
    
    # Initialize response
    resp = MessagingResponse()
    
    # Check for reset command
    if incoming_msg.lower() in ['reset', 'restart', 'cancel']:
        reset_session(sender_phone)
        resp.message("Session reset. Send 'start' to begin a new transaction.")
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
        resp.message(help_text)
        return str(resp)
    
    # Check for balance command
    if incoming_msg.lower() == 'balance':
        # This would be expanded in a real app to show all balances
        resp.message("To check a specific contact's balance, please start a transaction first.")
        return str(resp)
    
    # Check for report command
    if incoming_msg.lower() == 'report':
        report_path = generate_daily_report()
        if report_path:
            resp.message("Daily report generated. The admin will receive it shortly.")
            # In a real app, you would send the file to the admin
            # This requires additional setup not covered in this example
        else:
            resp.message("No transactions found for today.")
        return str(resp)
    
    # Handle conversation based on current state
    if session['state'] == STATES['INITIAL']:
        if incoming_msg.lower() == 'start':
            session['state'] = STATES['AWAITING_CONTACT']
            resp.message(format_contacts_list())
        else:
            resp.message("Welcome to Money Tracker! Send 'start' to begin a new transaction or 'help' for commands.")
    
    elif session['state'] == STATES['AWAITING_CONTACT']:
        try:
            contact_id = int(incoming_msg)
            contact = get_contact_by_id(contact_id)
            if contact:
                session['selected_contact'] = contact
                session['state'] = STATES['AWAITING_TYPE']
                resp.message(f"Selected: {contact['name']}\n\nAre you lending money to them or borrowing from them? Reply with 'lend' or 'borrow'.")
            else:
                resp.message("Invalid contact number. Please select from the list:")
                resp.message(format_contacts_list())
        except ValueError:
            resp.message("Please enter a valid contact number from the list.")
    
    elif session['state'] == STATES['AWAITING_TYPE']:
        if incoming_msg.lower() in ['lend', 'borrow']:
            session['transaction_type'] = incoming_msg.lower()
            session['state'] = STATES['AWAITING_AMOUNT']
            action = "lending to" if incoming_msg.lower() == 'lend' else "borrowing from"
            resp.message(f"You're {action} {session['selected_contact']['name']}. Please enter the amount:")
        else:
            resp.message("Please reply with either 'lend' or 'borrow'.")
    
    elif session['state'] == STATES['AWAITING_AMOUNT']:
        # Try to extract a valid amount
        amount_match = re.search(r'(\d+(\.\d+)?)', incoming_msg)
        if amount_match:
            try:
                amount = float(amount_match.group(1))
                session['amount'] = amount
                session['state'] = STATES['AWAITING_CONFIRMATION']
                
                action = "lend to" if session['transaction_type'] == 'lend' else "borrow from"
                resp.message(
                    f"Please confirm:\n\n"
                    f"You will {action} {session['selected_contact']['name']} ₹{amount:.2f}\n\n"
                    f"Reply 'yes' to confirm or 'no' to cancel."
                )
            except ValueError:
                resp.message("Invalid amount. Please enter a valid number.")
        else:
            resp.message("Please enter a valid amount (numbers only).")
    
    elif session['state'] == STATES['AWAITING_CONFIRMATION']:
        if incoming_msg.lower() in ['yes', 'y', 'confirm']:
            # Add the transaction to Excel
            success = add_transaction(
                session['selected_contact']['id'],
                session['selected_contact']['name'],
                session['amount'],
                session['transaction_type']
            )
            
            if success:
                action = "lent to" if session['transaction_type'] == 'lend' else "borrowed from"
                resp.message(
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
                resp.message("❌ Error recording transaction. Please try again.")
        
        elif incoming_msg.lower() in ['no', 'n', 'cancel']:
            resp.message("Transaction cancelled. Send 'start' to begin again.")
            reset_session(sender_phone)
        else:
            resp.message("Please reply with 'yes' to confirm or 'no' to cancel.")
    
    return str(resp)

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    return json.dumps({"status": "healthy"}), 200, {'ContentType': 'application/json'}

if __name__ == '__main__':
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Get port from environment variable or use default
    port = int(os.getenv('PORT', 5000))
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=port, debug=True)
