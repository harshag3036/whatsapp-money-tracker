# Testing the WhatsApp Money Tracker Bot Locally

This guide explains how to test your WhatsApp Money Tracker Bot locally without needing to set up ngrok or configure Twilio webhooks.

## Prerequisites

- The Flask application is running on port 5000
- curl is installed on your system (comes pre-installed on most macOS and Linux systems)

## Testing with the Automated Script

We've provided a bash script that simulates the entire conversation flow using curl commands:

1. **Make sure your Flask app is running**:
   ```bash
   python3 run.py
   ```

2. **In a new terminal, run the test script**:
   ```bash
   ./test_with_curl.sh
   ```

3. **Check the results**:
   - The script will simulate a complete conversation flow
   - Each step will show the message sent and the bot's response
   - After completion, check the Excel file in the `data` directory to verify the transaction was recorded

## Manual Testing with curl

You can also test individual commands manually:

### 1. Get Help

```bash
curl -X POST http://localhost:5000/webhook \
  -d "From=whatsapp:+919454715963" \
  -d "Body=help"
```

### 2. Start a Transaction

```bash
curl -X POST http://localhost:5000/webhook \
  -d "From=whatsapp:+919454715963" \
  -d "Body=start"
```

### 3. Select a Contact

```bash
curl -X POST http://localhost:5000/webhook \
  -d "From=whatsapp:+919454715963" \
  -d "Body=1"
```

### 4. Specify Transaction Type

```bash
curl -X POST http://localhost:5000/webhook \
  -d "From=whatsapp:+919454715963" \
  -d "Body=lend"
```

### 5. Enter Amount

```bash
curl -X POST http://localhost:5000/webhook \
  -d "From=whatsapp:+919454715963" \
  -d "Body=500"
```

### 6. Confirm Transaction

```bash
curl -X POST http://localhost:5000/webhook \
  -d "From=whatsapp:+919454715963" \
  -d "Body=yes"
```

### 7. Generate Report

```bash
curl -X POST http://localhost:5000/webhook \
  -d "From=whatsapp:+919454715963" \
  -d "Body=report"
```

## Understanding the Test Process

When you send a curl request to the `/webhook` endpoint, you're simulating what Twilio would do when a WhatsApp message is received. The two key parameters are:

- `From`: The WhatsApp number sending the message (should match one in your contacts.py)
- `Body`: The content of the message

The Flask application processes these parameters exactly as it would with real Twilio webhooks, maintaining the conversation state and responding appropriately.

## Troubleshooting

- **Error connecting to localhost**: Make sure your Flask app is running on port 5000
- **Session state issues**: The bot maintains session state based on the phone number. If you want to reset, send "reset" as the message body
- **XML parsing errors**: If you see XML in the response, that's normal - it's the TwiML that would be sent back to Twilio

## Moving to Production

Once you've verified everything works locally, you can deploy to a production environment like AWS Lightsail and configure Twilio to send webhooks to your server. See the DEPLOYMENT.md file for detailed instructions.
