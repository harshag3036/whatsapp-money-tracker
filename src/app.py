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
import logging

# Load environment variables
load_dotenv()

# Import our modules
from src.contacts import get_contact_by_id, get_all_contacts
from src.optimized_sheets_manager import add_transaction, get_balance_for_contact, generate_daily_report
from src.file_session_manager import (
    get_or_create_session, reset_session, update_session_state, 
    is_duplicate_message, add_transaction_to_history, STATES
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('app')

# Initialize Flask app
app = Flask(__name__)

# Initialize Twilio client
TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
ADMIN_PHONE_NUMBER = os.getenv('ADMIN_PHONE_NUMBER')

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Debug flag
DEBUG = True

def get_contacts_text():
    """Create a text-based list of contacts."""
    contacts = get_all_contacts()
    
    # Create a text list of contacts
    contacts_text = "Please select a contact by replying with the number:\n"
    for i, contact in enumerate(contacts, 1):
        contacts_text += f"{i}. {contact['name']}\n"
    
    return contacts_text

def get_amount_text(contact_name):
    """Create a text message for entering amount."""
    return (
        f"Transaction with {contact_name}\n\n"
        f"Please enter the amount you are giving to {contact_name}:"
    )

def get_confirmation_text(contact_name, amount):
    """Create a text message for confirmation."""
    return (
        f"Confirm Transaction\n\n"
        f"Please confirm:\n\n"
        f"You are giving {contact_name} ₹{amount:.2f}\n\n"
        f"Reply with 'yes' to confirm or 'no' to cancel."
    )

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming WhatsApp messages."""
    # Get the message details
    incoming_msg = request.values.get('Body', '').strip()
    sender_phone = request.values.get('From', '')
    message_sid = request.values.get('MessageSid', '')
    
    # Log the incoming message
    logger.info(f"Incoming message: '{incoming_msg}' from {sender_phone} (SID: {message_sid})")
    
    # Check for duplicate message (could happen due to network retries)
    if is_duplicate_message(sender_phone, message_sid):
        logger.warning(f"Duplicate message detected: {message_sid}")
        return str(MessagingResponse())
    
    # Get or create user session
    session = get_or_create_session(sender_phone)
    
    # Log the current session state
    logger.info(f"Current session state: {session['state']}")
    
    # Initialize response
    resp = MessagingResponse()
    
    # We'll set the message content at the end
    response_text = None
    
    # Check for reset command
    if incoming_msg.lower() in ['reset', 'restart', 'cancel']:
        reset_session(sender_phone)
        response_text = "Session reset. Send 'start' to begin a new transaction."
    
    # Check for help command
    elif incoming_msg.lower() in ['help', 'commands']:
        response_text = (
            "Available commands:\n"
            "- 'start': Begin a new transaction\n"
            "- 'reset': Reset the current session\n"
            "- 'report': Generate today's report\n"
            "- 'help': Show this help message"
        )
    
    # Check for report command
    elif incoming_msg.lower() == 'report':
        report = generate_daily_report()
        
        if report['transactions']:
            report_text = f"Daily Report for {report['transactions'][0]['date']}:\n\n"
            report_text += f"Total Amount: ₹{report['total_lent']:.2f}\n\n"
            
            report_text += "Transactions:\n"
            for transaction in report['transactions']:
                report_text += f"- Gave to {transaction['contact_name']}: ₹{transaction['amount']:.2f}\n"
            
            response_text = report_text
        else:
            response_text = "No transactions found for today."
    
    # Handle conversation based on current state
    elif session['state'] == STATES['INITIAL']:
        if incoming_msg.lower() == 'start':
            # Update state before sending response
            session = update_session_state(sender_phone, STATES['AWAITING_CONTACT'])
            logger.info(f"Starting new transaction flow for {sender_phone}")
            
            # Send text-based contact list
            response_text = get_contacts_text()
        else:
            response_text = "Welcome to Money Tracker! Send 'start' to begin a new transaction or 'help' for commands."
    
    elif session['state'] == STATES['AWAITING_CONTACT']:
        try:
            # Try to parse as a number (index)
            contact_index = int(incoming_msg)
            contacts = get_all_contacts()
            
            if 1 <= contact_index <= len(contacts):
                contact = contacts[contact_index - 1]
                
                # Update state and store selected contact
                session = update_session_state(
                    sender_phone, 
                    STATES['AWAITING_AMOUNT'],
                    selected_contact=contact
                )
                logger.info(f"Contact selected: {contact['name']}")
                
                # Send amount prompt
                response_text = get_amount_text(contact['name'])
            else:
                logger.warning(f"Invalid contact index: {contact_index}")
                response_text = "Please select a valid contact from the list:\n\n" + get_contacts_text()
        except ValueError:
            # If the user didn't enter a number, check if they entered a contact name
            contacts = get_all_contacts()
            matching_contacts = [c for c in contacts if c['name'].lower() == incoming_msg.lower()]
            
            if matching_contacts:
                contact = matching_contacts[0]
                
                # Update state and store selected contact
                session = update_session_state(
                    sender_phone, 
                    STATES['AWAITING_AMOUNT'],
                    selected_contact=contact
                )
                logger.info(f"Contact selected by name: {contact['name']}")
                
                # Send amount prompt
                response_text = get_amount_text(contact['name'])
            else:
                logger.warning(f"No matching contact found for: {incoming_msg}")
                response_text = "Please select a valid contact from the list:\n\n" + get_contacts_text()
    
    elif session['state'] == STATES['AWAITING_AMOUNT']:
        # Try to extract a valid amount
        amount_match = re.search(r'(\d+(\.\d+)?)', incoming_msg)
        if amount_match:
            try:
                amount = float(amount_match.group(1))
                
                # Update state and store amount
                session = update_session_state(
                    sender_phone, 
                    STATES['AWAITING_CONFIRMATION'],
                    amount=amount
                )
                logger.info(f"Amount entered: {amount}")
                
                # Send confirmation message
                response_text = get_confirmation_text(
                    session['selected_contact']['name'],
                    amount
                )
            except ValueError:
                logger.warning(f"Invalid amount format: {incoming_msg}")
                response_text = "Invalid amount. Please enter a valid number."
        else:
            logger.warning(f"No amount found in message: {incoming_msg}")
            response_text = "Please enter a valid amount (numbers only)."
    
    elif session['state'] == STATES['AWAITING_CONFIRMATION']:
        if incoming_msg.lower() in ['yes', 'y', 'confirm']:
            # Add the transaction to Google Sheets (always use 'lend' as transaction type)
            logger.info(f"Confirming transaction: {session['selected_contact']['name']}, ₹{session['amount']}")
            
            try:
                success = add_transaction(
                    session['selected_contact']['id'],
                    session['selected_contact']['name'],
                    session['amount'],
                    'lend'  # Always use 'lend' as the transaction type
                )
                
                # Also add to session history
                add_transaction_to_history(
                    sender_phone,
                    session['selected_contact']['id'],
                    session['selected_contact']['name'],
                    session['amount']
                )
                
            except Exception as e:
                logger.error(f"Error adding transaction: {e}")
                success = False
            
            if success:
                logger.info(f"Transaction successfully recorded")
                response_text = (
                    f"✅ Transaction recorded!\n\n"
                    f"You are giving {session['selected_contact']['name']} ₹{session['amount']:.2f}\n\n"
                    f"Send 'start' to record another transaction."
                )
                
                # Change state to COMPLETED instead of resetting
                # This is a critical change to fix the flow issue
                session = update_session_state(
                    sender_phone, 
                    STATES['COMPLETED'],
                    transaction_complete=True
                )
                logger.info(f"Session moved to COMPLETED state instead of reset")
            else:
                logger.error(f"Failed to record transaction")
                response_text = "❌ Error recording transaction. Please try again."
        
        elif incoming_msg.lower() in ['no', 'n', 'cancel']:
            response_text = "Transaction cancelled. Send 'start' to begin again."
            reset_session(sender_phone)
        else:
            response_text = "Please reply with 'yes' to confirm or 'no' to cancel."
    
    # Handle COMPLETED state - this is a new state to fix the flow issue
    elif session['state'] == STATES['COMPLETED']:
        if incoming_msg.lower() == 'start':
            # Start a new transaction
            session = update_session_state(sender_phone, STATES['AWAITING_CONTACT'])
            logger.info(f"Starting new transaction from COMPLETED state")
            response_text = get_contacts_text()
        else:
            # Any other message in COMPLETED state should show the help message
            response_text = "Transaction completed. Send 'start' to begin a new transaction or 'help' for commands."
    
    # Ensure we have a non-empty response
    if not response_text:
        response_text = "Welcome to Money Tracker! Send 'start' to begin a new transaction or 'help' for commands."
    
    # Log the response
    logger.info(f"Response: '{response_text}'")
    
    # Add the message to the response
    resp.message(response_text)
    
    # Log the updated session state
    logger.info(f"Updated session state: {session['state']}")
    
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
