"""
Session management module for the WhatsApp Money Tracker Bot.
This module provides functions for managing user sessions and state transitions.
"""

import time
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('session_manager')

# Define conversation states
STATES = {
    'INITIAL': 'initial',
    'AWAITING_CONTACT': 'awaiting_contact',
    'AWAITING_AMOUNT': 'awaiting_amount',
    'AWAITING_CONFIRMATION': 'awaiting_confirmation',
    'COMPLETED': 'completed'
}

# In-memory session storage
# In a production app, use a database with proper persistence
sessions = {}

# Session timeout in seconds (30 minutes)
SESSION_TIMEOUT = 30 * 60

def get_or_create_session(phone_number):
    """
    Get an existing session or create a new one if it doesn't exist.
    
    Args:
        phone_number (str): The user's phone number
        
    Returns:
        dict: The user's session
    """
    # Normalize the phone number to ensure consistent keys
    normalized_phone = phone_number.strip()
    
    logger.info(f"Session request for {normalized_phone}")
    
    # Check if session exists and is not expired
    if normalized_phone in sessions:
        session = sessions[normalized_phone]
        
        # Check if session has expired
        if time.time() - session.get('last_activity', 0) > SESSION_TIMEOUT:
            logger.info(f"Session expired for {normalized_phone}, creating new session")
            session = create_new_session()
        else:
            logger.info(f"Using existing session for {normalized_phone}, state: {session['state']}")
    else:
        logger.info(f"Creating new session for {normalized_phone}")
        session = create_new_session()
    
    # Update last activity time
    session['last_activity'] = time.time()
    
    # Save the session
    sessions[normalized_phone] = session
    
    return session

def create_new_session():
    """
    Create a new session with default values.
    
    Returns:
        dict: A new session object
    """
    return {
        'state': STATES['INITIAL'],
        'selected_contact': None,
        'amount': None,
        'last_message': None,
        'last_activity': time.time(),
        'transaction_history': []
    }

def reset_session(phone_number):
    """
    Reset a user's session to the initial state.
    
    Args:
        phone_number (str): The user's phone number
        
    Returns:
        dict: The reset session
    """
    normalized_phone = phone_number.strip()
    
    if normalized_phone in sessions:
        logger.info(f"Resetting session for {normalized_phone}")
        
        # Preserve some fields from the existing session
        last_message = sessions[normalized_phone].get('last_message')
        transaction_history = sessions[normalized_phone].get('transaction_history', [])
        
        # Create a new session but keep some data
        sessions[normalized_phone] = {
            'state': STATES['INITIAL'],
            'selected_contact': None,
            'amount': None,
            'last_message': last_message,
            'last_activity': time.time(),
            'transaction_history': transaction_history
        }
    else:
        logger.info(f"No session to reset for {normalized_phone}, creating new one")
        sessions[normalized_phone] = create_new_session()
    
    return sessions[normalized_phone]

def update_session_state(phone_number, new_state, **kwargs):
    """
    Update a session's state and optionally other attributes.
    
    Args:
        phone_number (str): The user's phone number
        new_state (str): The new state to set
        **kwargs: Additional session attributes to update
        
    Returns:
        dict: The updated session
    """
    normalized_phone = phone_number.strip()
    
    if normalized_phone not in sessions:
        logger.warning(f"Attempted to update non-existent session for {normalized_phone}")
        sessions[normalized_phone] = create_new_session()
    
    session = sessions[normalized_phone]
    
    # Log the state transition
    logger.info(f"State transition for {normalized_phone}: {session['state']} -> {new_state}")
    
    # Update the state
    session['state'] = new_state
    
    # Update last activity time
    session['last_activity'] = time.time()
    
    # Update any additional attributes
    for key, value in kwargs.items():
        session[key] = value
        logger.info(f"Updated session attribute '{key}' for {normalized_phone}")
    
    # Save the session
    sessions[normalized_phone] = session
    
    return session

def is_duplicate_message(phone_number, message_sid):
    """
    Check if a message is a duplicate based on its SID.
    
    Args:
        phone_number (str): The user's phone number
        message_sid (str): The message SID from Twilio
        
    Returns:
        bool: True if the message is a duplicate, False otherwise
    """
    normalized_phone = phone_number.strip()
    
    if normalized_phone not in sessions:
        return False
    
    session = sessions[normalized_phone]
    
    if session.get('last_message') == message_sid:
        logger.warning(f"Duplicate message detected: {message_sid}")
        return True
    
    # Update the last message SID
    session['last_message'] = message_sid
    sessions[normalized_phone] = session
    
    return False

def add_transaction_to_history(phone_number, contact_id, contact_name, amount):
    """
    Add a transaction to the user's transaction history.
    
    Args:
        phone_number (str): The user's phone number
        contact_id (int): The contact ID
        contact_name (str): The contact name
        amount (float): The transaction amount
        
    Returns:
        dict: The updated session
    """
    normalized_phone = phone_number.strip()
    
    if normalized_phone not in sessions:
        logger.warning(f"Attempted to add transaction to non-existent session for {normalized_phone}")
        sessions[normalized_phone] = create_new_session()
    
    session = sessions[normalized_phone]
    
    # Create a transaction record
    transaction = {
        'contact_id': contact_id,
        'contact_name': contact_name,
        'amount': amount,
        'timestamp': time.time()
    }
    
    # Add to history
    if 'transaction_history' not in session:
        session['transaction_history'] = []
    
    session['transaction_history'].append(transaction)
    logger.info(f"Added transaction to history for {normalized_phone}: {contact_name}, ₹{amount}")
    
    # Save the session
    sessions[normalized_phone] = session
    
    return session

def get_transaction_history(phone_number):
    """
    Get the transaction history for a user.
    
    Args:
        phone_number (str): The user's phone number
        
    Returns:
        list: The user's transaction history
    """
    normalized_phone = phone_number.strip()
    
    if normalized_phone not in sessions:
        return []
    
    return sessions[normalized_phone].get('transaction_history', [])

def cleanup_expired_sessions():
    """
    Remove expired sessions to free up memory.
    
    Returns:
        int: The number of sessions removed
    """
    current_time = time.time()
    expired_keys = []
    
    for phone, session in sessions.items():
        if current_time - session.get('last_activity', 0) > SESSION_TIMEOUT:
            expired_keys.append(phone)
    
    # Remove expired sessions
    for phone in expired_keys:
        del sessions[phone]
    
    logger.info(f"Cleaned up {len(expired_keys)} expired sessions")
    return len(expired_keys)
