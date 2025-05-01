"""
Contact management module for the WhatsApp Money Tracker Bot.
This module handles the list of contacts that can be selected for transactions.
"""

# Sample list of contacts - in a real application, this might come from a database
CONTACTS = [
    {"id": 1, "name": "Self", "phone": "+919454715963"},  # Your number
    {"id": 2, "name": "Rahul", "phone": "+919XXXXXXXX1"},
    {"id": 3, "name": "Priya", "phone": "+919XXXXXXXX2"},
    {"id": 4, "name": "Amit", "phone": "+919XXXXXXXX3"},
    {"id": 5, "name": "Neha", "phone": "+919XXXXXXXX4"},
    {"id": 6, "name": "Vikram", "phone": "+919XXXXXXXX5"},
]

def get_all_contacts():
    """Return the list of all contacts."""
    return CONTACTS

def get_contact_by_id(contact_id):
    """
    Get a contact by their ID.
    
    Args:
        contact_id (int): The ID of the contact to retrieve.
        
    Returns:
        dict or None: The contact information if found, None otherwise.
    """
    for contact in CONTACTS:
        if contact["id"] == contact_id:
            return contact
    return None

def get_contact_by_name(name):
    """
    Get a contact by their name (case-insensitive partial match).
    
    Args:
        name (str): The name or partial name to search for.
        
    Returns:
        list: A list of matching contacts.
    """
    name = name.lower()
    return [contact for contact in CONTACTS if name in contact["name"].lower()]

def format_contacts_list():
    """
    Format the contacts list for display in WhatsApp.
    
    Returns:
        str: A formatted string listing all contacts with their IDs.
    """
    contacts_text = "Select a contact by replying with their number:\n\n"
    for contact in CONTACTS:
        contacts_text += f"{contact['id']}. {contact['name']}\n"
    return contacts_text
