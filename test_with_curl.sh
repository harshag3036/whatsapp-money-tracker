#!/bin/bash
# Test script for WhatsApp Money Tracker Bot
# This script simulates the WhatsApp conversation flow using curl commands

# Set the base URL
BASE_URL="http://localhost:5000/webhook"
# Set the phone number (should match one in your contacts.py)
PHONE="whatsapp:+919454715963"

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== WhatsApp Money Tracker Bot - Local Testing ===${NC}"
echo -e "${YELLOW}Make sure your Flask app is running on port 5000${NC}"
echo ""

# Function to send a message and display the response
send_message() {
    local message=$1
    echo -e "${YELLOW}Sending message: ${message}${NC}"
    
    # Send the message using curl
    response=$(curl -s -X POST $BASE_URL \
        -d "From=$PHONE" \
        -d "Body=$message")
    
    # Extract the message content from the TwiML response
    message_content=$(echo $response | grep -o '<Message>.*</Message>' | sed 's/<Message>//g' | sed 's/<\/Message>//g')
    
    echo -e "${GREEN}Bot response: ${message_content}${NC}"
    echo ""
    
    # Sleep to simulate real conversation timing
    sleep 1
}

# Test the conversation flow
echo -e "${BLUE}Starting conversation flow test...${NC}"
echo ""

# Step 1: Send 'help' to get available commands
send_message "help"

# Step 2: Start a new transaction
send_message "start"

# Step 3: Select contact (1 = Self)
send_message "1"

# Step 4: Specify transaction type (lend)
send_message "lend"

# Step 5: Enter amount
send_message "500"

# Step 6: Confirm transaction
send_message "yes"

# Step 7: Check the report command
send_message "report"

echo -e "${BLUE}Test completed!${NC}"
echo -e "${YELLOW}Check the Excel file in the data directory to verify the transaction was recorded.${NC}"
