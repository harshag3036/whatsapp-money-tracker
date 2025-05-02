#!/usr/bin/env python3
"""
Test script to verify the fixed session management in the WhatsApp Money Tracker Bot.
This script simulates a conversation flow to ensure state transitions work correctly.
"""

import requests
import json
import time
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# URL of your webhook (change if needed)
WEBHOOK_URL = "http://localhost:5000/webhook"

def simulate_message(body, from_number="+1234567890"):
    """Simulate sending a WhatsApp message to the webhook."""
    # Generate a unique message SID for each message
    message_sid = f"SM{int(time.time())}"
    
    # Create the payload similar to what Twilio would send
    payload = {
        "Body": body,
        "From": from_number,
        "MessageSid": message_sid
    }
    
    # Send the request to the webhook
    response = requests.post(WEBHOOK_URL, data=payload)
    
    # Print the response
    print(f"\n--- Message: '{body}' ---")
    print(f"Response Status: {response.status_code}")
    print(f"Response Content: {response.text}")
    
    # Extract the message content from the TwiML response
    # This is a simple parser and might break with complex TwiML
    message_content = ""
    if "<Message>" in response.text and "</Message>" in response.text:
        message_content = response.text.split("<Message>")[1].split("</Message>")[0]
    
    return message_content

def test_conversation_flow():
    """Test the entire conversation flow to verify state management."""
    print("Starting conversation flow test...")
    
    # Step 1: Send 'start' to begin
    response = simulate_message("start")
    print(f"Bot response: {response}")
    time.sleep(1)  # Small delay between messages
    
    # Step 2: Select contact '2' (Rahul)
    response = simulate_message("2")
    print(f"Bot response: {response}")
    time.sleep(1)
    
    # Step 3: Enter amount
    response = simulate_message("500")
    print(f"Bot response: {response}")
    time.sleep(1)
    
    # Step 4: Confirm transaction
    response = simulate_message("yes")
    print(f"Bot response: {response}")
    time.sleep(1)
    
    # Step 5: Start a new transaction
    response = simulate_message("start")
    print(f"Bot response: {response}")
    time.sleep(1)
    
    # Step 6: Select a different contact '5' (Neha)
    response = simulate_message("5")
    print(f"Bot response: {response}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    # Make sure the Flask app is running before executing this test
    test_conversation_flow()
