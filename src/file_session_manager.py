"""
File-based session management module for the WhatsApp Money Tracker Bot.
This module provides functions for managing user sessions and state transitions
using a file-based storage that works with multiple Gunicorn workers.
"""

import os
import json
import time
import logging
import threading
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('file_session_manager')

# Define conversation states
STATES = {
    'INITIAL': 'initial',
    'AWAITING_CONTACT': 'awaiting_contact',
    'AWAITING_AMOUNT': 'awaiting_amount',
    'AWAITING_CONFIRMATION': 'awaiting_confirmation',
    'COMPLETED': 'completed'  # This state is used after a transaction is completed
}

# Session timeout in seconds (30 minutes)
SESSION_TIMEOUT = 30 * 60

# File lock for thread safety
file_lock = threading.Lock()

# Create sessions directory if it doesn't exist
SESSIONS_DIR = Path('sessions')
SESSIONS_DIR.mkdir(exist_ok=True)

def _get_session_file_path(phone_number):
    """
    Get the file path for a session.
    
    Args:
        phone_number (str): The user's phone number
        
    Returns:
        Path: The path to the session file
    """
    # Normalize and sanitize the phone number for use as a filename
    normalized_phone = phone_number.strip().replace(':', '_').replace('+', '')
    return SESSIONS_DIR / f"session_{normalized_phone}.json"

def _save_session(phone_number, session):
    """
    Save a session to a file.
    
    Args:
        phone_number (str): The user's phone number
        session (dict): The session data
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        file_path = _get_session_file_path(phone_number)
        with file_lock:
            with open(file_path, 'w') as f:
                json.dump(session, f)
        return True
    except Exception as e:
        logger.error(f"Error saving session for {phone_number}: {e}")
        return False

def _load_session(phone_number):
    """
    Load a session from a file.
    
    Args:
        phone_number (str): The user's phone number
        
    Returns:
        dict or None: The session data if found, None otherwise
    """
    try:
        file_path = _get_session_file_path(phone_number)
        if not file_path.exists():
            return None
        
        with file_lock:
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading session for {phone_number}: {e}")
        return None

def get_or_create_session(phone_number):
    """
    Get an existing session or create a new one if it doesn't exist.
    
    Args:
        phone_number (str): The user's phone number
        
    Returns:
        dict: The user's session
    """
    # Normalize the phone number
    normalized_phone = phone_number.strip()
    
    logger.info(f"Session request for {normalized_phone}")
    
    # Try to load the session
    session = _load_session(normalized_phone)
    
    if session:
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
    _save_session(normalized_phone, session)
    
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
    
    logger.info(f"Resetting session for {normalized_phone}")
    
    # Try to load the existing session
    session = _load_session(normalized_phone)
    
    if session:
        # Preserve some fields from the existing session
        last_message = session.get('last_message')
        transaction_history = session.get('transaction_history', [])
        
        # Create a new session but keep some data
        session = {
            'state': STATES['INITIAL'],
            'selected_contact': None,
            'amount': None,
            'last_message': last_message,
            'last_activity': time.time(),
            'transaction_history': transaction_history
        }
    else:
        session = create_new_session()
    
    # Save the reset session
    _save_session(normalized_phone, session)
    
    return session

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
    
    # Load the session
    session = _load_session(normalized_phone)
    
    if not session:
        logger.warning(f"Attempted to update non-existent session for {normalized_phone}")
        session = create_new_session()
    
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
    _save_session(normalized_phone, session)
    
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
    
    # Load the session
    session = _load_session(normalized_phone)
    
    if not session:
        return False
    
    if session.get('last_message') == message_sid:
        logger.warning(f"Duplicate message detected: {message_sid}")
        return True
    
    # Update the last message SID
    session['last_message'] = message_sid
    _save_session(normalized_phone, session)
    
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
    
    # Load the session
    session = _load_session(normalized_phone)
    
    if not session:
        logger.warning(f"Attempted to add transaction to non-existent session for {normalized_phone}")
        session = create_new_session()
    
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
    _save_session(normalized_phone, session)
    
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
    
    # Load the session
    session = _load_session(normalized_phone)
    
    if not session:
        return []
    
    return session.get('transaction_history', [])

def cleanup_expired_sessions():
    """
    Remove expired sessions to free up disk space.
    
    Returns:
        int: The number of sessions removed
    """
    current_time = time.time()
    removed_count = 0
    
    try:
        for file_path in SESSIONS_DIR.glob('session_*.json'):
            try:
                with file_lock:
                    with open(file_path, 'r') as f:
                        session = json.load(f)
                
                if current_time - session.get('last_activity', 0) > SESSION_TIMEOUT:
                    with file_lock:
                        file_path.unlink()
                    removed_count += 1
            except Exception as e:
                logger.error(f"Error processing session file {file_path}: {e}")
    except Exception as e:
        logger.error(f"Error cleaning up expired sessions: {e}")
    
    logger.info(f"Cleaned up {removed_count} expired sessions")
    return removed_count
