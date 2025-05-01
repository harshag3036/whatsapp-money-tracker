# WhatsApp Money Tracker Bot

A WhatsApp bot that helps users track money lending and borrowing activities through an intuitive, interactive interface. Users can select a person from a clickable list, specify if they're lending or borrowing money, enter an amount, and the data is saved to a Google Sheet organized by date.

## Features

- **Interactive Interface**: Clickable buttons for contact selection and transaction confirmation
- **Google Sheets Integration**: Data stored in Google Sheets with daily sheets
- **Flexible Deployment**: Run locally for testing or deploy to AWS Lightsail for production
- **Balance Tracking**: Track balances for each contact
- **Daily Reports**: Generate reports of daily transactions

## Project Structure

```
whatsapp-money-tracker/
├── src/
│   ├── app.py              # Main Flask application with Twilio webhook
│   ├── contacts.py         # Contact management module
│   ├── sheets_manager.py   # Google Sheets integration
│   └── __init__.py         # Package initialization
├── .env.example            # Environment variables template
├── .gitignore              # Git ignore file
├── AWS_LIGHTSAIL_DEPLOYMENT.md  # AWS deployment guide
├── DEPLOYMENT.md           # General deployment guide
├── GOOGLE_SHEETS_SETUP.md  # Google Sheets setup instructions
├── README.md               # This file
├── google_sheets_requirements.txt  # Google API dependencies
├── requirements.txt        # Python dependencies
├── run.py                  # Entry point script
├── test_interactive.py     # Interactive testing script
└── test_with_curl.sh       # Basic testing script
```

## Setup Instructions

### 1. Install Dependencies

```bash
# Install basic dependencies
pip install -r requirements.txt

# Install Google Sheets dependencies
pip install -r google_sheets_requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and edit it:

```bash
cp .env.example .env
```

Update the `.env` file with your Twilio credentials:

```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=whatsapp:+14155238886
ADMIN_PHONE_NUMBER=whatsapp:+919XXXXXXXXX
```

### 3. Set Up Google Sheets Integration

Follow the detailed instructions in `GOOGLE_SHEETS_SETUP.md` to:
- Create a Google Cloud project
- Enable the Google Sheets API
- Set up authentication (OAuth or Service Account)
- Configure access to the Google Sheet

### 4. Run the Application

```bash
python run.py
```

This will start the Flask server on port 5000.

### 5. Connect to Twilio

To connect the bot to WhatsApp via Twilio, you need to:
- Set up a public URL (using ngrok for development or a server for production)
- Configure the Twilio webhook to point to your URL + `/webhook`
- Join the Twilio WhatsApp sandbox

Detailed instructions are in the `DEPLOYMENT.md` file.

## Testing the Bot

### Local Testing with Interactive Messages

Use the provided Python script to test the bot locally:

```bash
./test_interactive.py
```

This script simulates the WhatsApp conversation flow with interactive buttons.

### Basic Testing with curl

For basic testing without interactive features:

```bash
./test_with_curl.sh
```

## Deployment Options

### Local Development

For local development and testing:
- Use ngrok to create a public URL
- Configure Twilio to use this URL
- Follow the instructions in `DEPLOYMENT.md`

### AWS Lightsail Deployment

For production deployment:
- Deploy to AWS Lightsail ($5/month)
- Set up with Nginx and Gunicorn
- Configure with SSL for security
- Detailed instructions in `AWS_LIGHTSAIL_DEPLOYMENT.md`

## Using the Bot

1. **Start a Transaction**:
   - Send "start" to the bot
   - You'll receive a list of contacts with clickable buttons

2. **Select a Contact**:
   - Click on a contact button
   - The bot will ask if you're lending or borrowing

3. **Specify Transaction Type**:
   - Click "Lending" or "Borrowing"
   - The bot will ask for the amount

4. **Enter Amount**:
   - Type the amount (e.g., "500")
   - The bot will ask for confirmation

5. **Confirm Transaction**:
   - Click "Yes" to confirm or "No" to cancel
   - The transaction will be recorded in Google Sheets

6. **Other Commands**:
   - "balance" - Check balances for all contacts
   - "report" - Generate a report of today's transactions
   - "help" - Show available commands
   - "reset" - Reset the current conversation

## Customization

- **Add/Edit Contacts**: Modify the `CONTACTS` list in `src/contacts.py`
- **Change Google Sheet**: Update the `SPREADSHEET_ID` in `src/sheets_manager.py`
- **Modify UI Text**: Edit the message strings in `src/app.py`

## Troubleshooting

If you encounter issues:
1. Check the Flask application logs
2. Verify your Twilio configuration
3. Ensure Google Sheets authentication is set up correctly
4. Refer to the troubleshooting sections in the deployment guides
