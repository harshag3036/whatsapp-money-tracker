# WhatsApp Money Tracker Bot - Deployment Guide

This guide will walk you through setting up and deploying the WhatsApp Money Tracker Bot using Twilio.

## Prerequisites

- Python 3.8 or higher
- A Twilio account
- A smartphone with WhatsApp installed
- For production: A server with a public IP address or a cloud hosting account

## Step 1: Set Up Twilio

1. **Create a Twilio Account**:
   - Go to [Twilio's website](https://www.twilio.com/) and sign up for an account
   - Complete the verification process

2. **Set Up WhatsApp Sandbox**:
   - In the Twilio Console, navigate to "Messaging" > "Try it Out" > "Send a WhatsApp Message"
   - Follow the instructions to join your sandbox by sending the provided code to the Twilio number
   - Note: The sandbox is free but has limitations. For production, you'll need to request access to the WhatsApp Business API

3. **Get Your Twilio Credentials**:
   - In the Twilio Console, find your Account SID and Auth Token
   - You'll need these for the `.env` file

## Step 2: Set Up the Project

1. **Clone the Repository**:
   ```bash
   git clone <repository-url>
   cd whatsapp-money-tracker
   ```

2. **Create a Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables**:
   - Copy the `.env.example` file to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit the `.env` file with your Twilio credentials:
     ```
     TWILIO_ACCOUNT_SID=your_account_sid_here
     TWILIO_AUTH_TOKEN=your_auth_token_here
     TWILIO_PHONE_NUMBER=whatsapp:+14155238886  # Or your Twilio WhatsApp number
     ADMIN_PHONE_NUMBER=whatsapp:+919XXXXXXXXX  # Your WhatsApp number
     ```

## Step 3: Local Development Setup

For testing and development, you can run the bot locally and use a tunneling service to expose it to the internet.

1. **Run the Flask Application**:
   ```bash
   python src/app.py
   ```
   This will start the server on port 5000 by default.

2. **Set Up Ngrok for Tunneling**:
   - [Download and install Ngrok](https://ngrok.com/download)
   - Start an Ngrok tunnel to your local server:
     ```bash
     ngrok http 5000
     ```
   - Ngrok will provide a public URL (e.g., `https://a1b2c3d4.ngrok.io`)

3. **Configure Twilio Webhook**:
   - In the Twilio Console, go to "Messaging" > "Settings" > "WhatsApp Sandbox Settings"
   - Set the "When a message comes in" webhook URL to your Ngrok URL + `/webhook`:
     ```
     https://a1b2c3d4.ngrok.io/webhook
     ```
   - Make sure the HTTP method is set to POST

## Step 4: Production Deployment

For a production environment, you'll need to deploy the bot to a server with a public IP address.

### Option 1: Deploy to a VPS (e.g., DigitalOcean, AWS EC2)

1. **Set Up a Server**:
   - Create a VPS instance (Ubuntu recommended)
   - Install Python, pip, and other dependencies
   - Set up a firewall to allow HTTP/HTTPS traffic

2. **Deploy the Code**:
   - Clone the repository to your server
   - Set up a virtual environment and install dependencies
   - Configure the `.env` file with your credentials

3. **Set Up a Production Web Server**:
   - Install and configure Gunicorn:
     ```bash
     pip install gunicorn
     gunicorn -w 4 -b 0.0.0.0:5000 src.app:app
     ```
   - Set up Nginx as a reverse proxy (recommended)

4. **Configure Twilio Webhook**:
   - Set the webhook URL to your server's public IP or domain + `/webhook`:
     ```
     https://your-domain.com/webhook
     ```

### Option 2: Deploy to a PaaS (e.g., Heroku, Render)

1. **Create an Account and Set Up**:
   - Sign up for a PaaS provider
   - Follow their documentation to connect your repository

2. **Configure Environment Variables**:
   - Add your Twilio credentials as environment variables in the platform's dashboard

3. **Deploy the Application**:
   - Follow the platform-specific deployment instructions
   - The platform will provide you with a public URL

4. **Configure Twilio Webhook**:
   - Set the webhook URL to your PaaS URL + `/webhook`:
     ```
     https://your-app.herokuapp.com/webhook
     ```

## Step 5: Testing the Bot

1. **Send a Message to Your Twilio WhatsApp Number**:
   - Start with "join" followed by the sandbox code (for sandbox setup)
   - Then send "start" to begin the transaction flow

2. **Follow the Conversation Flow**:
   - Select a contact from the list
   - Specify if you're lending or borrowing
   - Enter the amount
   - Confirm the transaction

3. **Check the Excel File**:
   - The transactions will be saved in `data/transactions.xlsx`
   - Daily reports will be generated in the same directory

## Troubleshooting

1. **Webhook Issues**:
   - Ensure your webhook URL is correctly set in Twilio
   - Check that your server is publicly accessible
   - Verify that the `/webhook` endpoint is responding to POST requests

2. **Message Delivery Problems**:
   - Confirm your WhatsApp number is correctly connected to the Twilio sandbox
   - Check Twilio logs for any error messages

3. **Excel File Issues**:
   - Ensure the `data` directory exists and is writable
   - Check for any error messages in the server logs

## Next Steps

1. **Customize the Contact List**:
   - Edit `src/contacts.py` to add your own contacts

2. **Enhance Security**:
   - Add authentication to the webhook endpoint
   - Implement request validation using Twilio's request validation

3. **Add Database Storage**:
   - Replace the in-memory session storage with a database
   - Consider using SQLite, PostgreSQL, or MongoDB

4. **Implement File Sharing**:
   - Set up functionality to send Excel reports directly via WhatsApp

## Production Considerations

1. **WhatsApp Business API**:
   - For a production environment, apply for the WhatsApp Business API
   - This provides higher message limits and additional features

2. **Monitoring and Logging**:
   - Set up proper logging and monitoring for your application
   - Consider using services like Sentry or Datadog

3. **Backup Strategy**:
   - Implement regular backups of your transaction data
   - Consider cloud storage solutions for Excel files

4. **Scaling**:
   - If needed, consider containerization with Docker
   - For high-volume applications, implement a load balancer
