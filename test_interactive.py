#!/usr/bin/env python3
"""
Test script for WhatsApp Money Tracker Bot with interactive messages.
This script simulates the WhatsApp conversation flow using direct requests to the Flask app.
"""

import requests
import json
import time
import sys

# Configuration
BASE_URL = "http://localhost:5000/webhook"
PHONE = "whatsapp:+919454715963"  # Should match one in your contacts.py

# ANSI colors for better readability
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
NC = '\033[0m'  # No Color

def send_message(message, interactive_type=None, interactive_id=None):
    """Send a message to the webhook and display the response."""
    print(f"{YELLOW}Sending message: {message}{NC}")
    
    # Prepare the data
    data = {
        "From": PHONE,
        "Body": message
    }
    
    # Add interactive data if provided
    if interactive_type and interactive_id:
        data["InteractiveType"] = interactive_type
        data["InteractiveButtonId"] = interactive_id
        print(f"{YELLOW}With interactive data: {interactive_type}, {interactive_id}{NC}")
    
    # Send the request
    try:
        response = requests.post(BASE_URL, data=data)
        response_text = response.text
        
        # Try to extract the message content
        try:
            # Check if it's an interactive message
            if "interactive" in response_text:
                # Parse the TwiML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response_text)
                message_element = root.find(".//Message")
                if message_element is not None:
                    body_element = message_element.find("Body")
                    if body_element is not None and body_element.text:
                        # Try to parse the JSON
                        try:
                            interactive_data = json.loads(body_element.text)
                            if "interactive" in interactive_data:
                                interactive = interactive_data["interactive"]
                                print(f"{GREEN}Bot sent an interactive message:{NC}")
                                print(f"{GREEN}Type: {interactive['type']}{NC}")
                                if "header" in interactive:
                                    print(f"{GREEN}Header: {interactive['header']['text']}{NC}")
                                print(f"{GREEN}Body: {interactive['body']['text']}{NC}")
                                
                                # Display buttons
                                if "action" in interactive and "buttons" in interactive["action"]:
                                    print(f"{GREEN}Buttons:{NC}")
                                    for i, button in enumerate(interactive["action"]["buttons"]):
                                        button_id = button["reply"]["id"]
                                        button_title = button["reply"]["title"]
                                        print(f"{GREEN}  {i+1}. {button_title} (ID: {button_id}){NC}")
                                return
                        except json.JSONDecodeError:
                            pass
            
            # If not interactive or parsing failed, show the regular message
            import re
            message_content = re.search(r'<Message>(.*?)</Message>', response_text, re.DOTALL)
            if message_content:
                content = message_content.group(1).strip()
                # Remove any XML tags
                content = re.sub(r'<[^>]+>', '', content)
                print(f"{GREEN}Bot response: {content}{NC}")
            else:
                print(f"{GREEN}Raw response: {response_text}{NC}")
        except Exception as e:
            print(f"{GREEN}Error parsing response: {e}{NC}")
            print(f"{GREEN}Raw response: {response_text}{NC}")
    except Exception as e:
        print(f"{GREEN}Error sending request: {e}{NC}")
    
    print("")
    time.sleep(1)

def simulate_conversation():
    """Simulate a conversation with the bot."""
    print(f"{BLUE}=== WhatsApp Money Tracker Bot - Interactive Testing ==={NC}")
    print(f"{YELLOW}Make sure your Flask app is running on port 5000{NC}")
    print("")
    
    # Step 1: Send 'start' to begin
    send_message("start")
    
    # Step 2: Select a contact using interactive button
    contact_id = input(f"{BLUE}Enter contact button ID (e.g., contact_1): {NC}")
    send_message("", "button_reply", contact_id)
    
    # Step 3: Select transaction type using interactive button
    transaction_type = input(f"{BLUE}Enter transaction type button ID (e.g., type_lend): {NC}")
    send_message("", "button_reply", transaction_type)
    
    # Step 4: Enter amount
    amount = input(f"{BLUE}Enter amount: {NC}")
    send_message(amount)
    
    # Step 5: Confirm transaction using interactive button
    confirmation = input(f"{BLUE}Enter confirmation button ID (e.g., confirm_yes): {NC}")
    send_message("", "button_reply", confirmation)
    
    print(f"{BLUE}Test completed!{NC}")
    print(f"{YELLOW}Check the Google Sheet to verify the transaction was recorded.{NC}")

if __name__ == "__main__":
    simulate_conversation()
