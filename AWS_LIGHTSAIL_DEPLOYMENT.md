# Deploying WhatsApp Money Tracker Bot on AWS Lightsail

This guide will walk you through deploying your WhatsApp Money Tracker Bot on AWS Lightsail and connecting it to Twilio.

## Why AWS Lightsail?

- **Affordable**: Starting at $5/month
- **Simple**: Easy to set up and manage
- **Reliable**: AWS infrastructure with good uptime
- **Scalable**: Can upgrade as needed

## Prerequisites

- AWS account
- Twilio account (you already have the Account SID and Auth Token)
- Basic familiarity with Linux commands

## Step 1: Create a Lightsail Instance

1. **Sign in to AWS**:
   - Go to [https://aws.amazon.com/lightsail/](https://aws.amazon.com/lightsail/)
   - Sign in to your AWS account or create one

2. **Create a new instance**:
   - Click "Create instance"
   - Select a Region (choose one close to your users)
   - Under "Select a platform", choose "Linux/Unix"
   - Under "Select a blueprint", choose "Ubuntu 22.04 LTS"

3. **Choose an instance plan**:
   - The $5/month plan (1 GB RAM, 1 vCPU, 40 GB SSD) is sufficient for this bot
   - You can always upgrade later if needed

4. **Name your instance**:
   - Enter a name like "whatsapp-money-tracker"

5. **Create the instance**:
   - Click "Create instance"
   - Wait for the instance to start (usually takes a minute or two)

## Step 2: Set Up Static IP and Firewall

1. **Create a static IP**:
   - Click on your instance name
   - Go to the "Networking" tab
   - Click "Create static IP"
   - Follow the prompts to attach it to your instance
   - Note down this IP address

2. **Configure firewall**:
   - Still in the "Networking" tab
   - Under "Firewall", add the following rules:
     - HTTP (port 80): Allow from anywhere
     - HTTPS (port 443): Allow from anywhere
     - Custom (port 5000): Allow from anywhere (temporary for setup)

## Step 3: Connect to Your Instance

1. **Using SSH in browser**:
   - On your instance's management page, click "Connect using SSH"
   - This opens a browser-based SSH terminal

2. **Alternative: Using SSH from your computer**:
   - Download the SSH key from the "Connect" tab
   - Use a terminal to connect:
     ```bash
     chmod 400 your-key.pem
     ssh -i your-key.pem ubuntu@your-static-ip
     ```

## Step 4: Install Dependencies

Run these commands in your SSH session:

```bash
# Update package lists
sudo apt update
sudo apt upgrade -y

# Install required packages
sudo apt install -y python3-pip python3-venv nginx certbot python3-certbot-nginx git

# Create a directory for the application
mkdir -p ~/whatsapp-money-tracker
cd ~/whatsapp-money-tracker
```

## Step 5: Deploy Your Code

You have two options:

### Option 1: Clone from Git (if you've pushed to a repository)

```bash
git clone https://your-repository-url.git .
```

### Option 2: Upload files using SCP (from your local machine)

```bash
# Run this on your local machine, not on the server
scp -i your-key.pem -r whatsapp-money-tracker/* ubuntu@your-static-ip:~/whatsapp-money-tracker/
```

## Step 6: Set Up Python Environment

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install gunicorn  # For production serving
```

## Step 7: Configure Environment Variables

```bash
# Create .env file
cat > .env << EOF
# Twilio Credentials
TWILIO_ACCOUNT_SID=AC75b3494bc4a1a16bbadd1faf8086087d
TWILIO_AUTH_TOKEN=g3vSsnxQikMn7VJ5JmAVTp3HnJ2tIYf1
TWILIO_PHONE_NUMBER=whatsapp:+14155238886
ADMIN_PHONE_NUMBER=whatsapp:+919454715963

# Flask settings
FLASK_ENV=production
PORT=5000
EOF
```

## Step 8: Set Up Gunicorn Service

```bash
# Create a systemd service file
sudo nano /etc/systemd/system/whatsapp-bot.service
```

Add the following content:

```
[Unit]
Description=WhatsApp Money Tracker Bot
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/whatsapp-money-tracker
ExecStart=/home/ubuntu/whatsapp-money-tracker/venv/bin/gunicorn -w 3 -b 127.0.0.1:5000 src.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+X, then Y, then Enter).

Then enable and start the service:

```bash
sudo systemctl enable whatsapp-bot
sudo systemctl start whatsapp-bot
sudo systemctl status whatsapp-bot  # Check if it's running
```

## Step 9: Set Up Nginx as Reverse Proxy

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/whatsapp-bot
```

Add the following content (replace `your-static-ip` with your actual IP):

```
server {
    listen 80;
    server_name your-static-ip;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Save and exit, then enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/whatsapp-bot /etc/nginx/sites-enabled/
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

## Step 10: Set Up SSL (Optional but Recommended)

```bash
# Get a free SSL certificate
sudo certbot --nginx -d your-domain.com
```

If you don't have a domain, you can use your IP address, but you'll get a warning.

## Step 11: Configure Twilio Webhook

1. **Log in to your Twilio account**:
   - Go to [https://www.twilio.com/login](https://www.twilio.com/login)
   - Use your Account SID and Auth Token

2. **Navigate to WhatsApp Sandbox**:
   - In the Twilio Console, go to "Messaging" > "Try it Out" > "Send a WhatsApp Message"

3. **Configure the Webhook URL**:
   - In the "Sandbox Settings" section, find "When a message comes in"
   - Set the URL to your server's IP or domain + `/webhook`:
     ```
     http://your-static-ip/webhook
     ```
     or if you set up SSL:
     ```
     https://your-domain.com/webhook
     ```
   - Make sure the HTTP method is set to POST
   - Click Save

## Step 12: Connect Your WhatsApp

1. **Find the Sandbox Connection Instructions**:
   - In the Twilio WhatsApp Sandbox page, you'll see instructions like:
     "Join Twilio's WhatsApp sandbox by sending a WhatsApp message to +14155238886 with code: join example-word"
   - The code will be unique to your account

2. **Send the Join Message**:
   - Open WhatsApp on your phone
   - Add the Twilio number (+14155238886) to your contacts
   - Send the join message with your unique code (e.g., "join example-word")

3. **Start Using Your Bot**:
   - Send "start" to begin
   - Follow the conversation flow

## Maintenance and Monitoring

### Checking Logs

```bash
# Check application logs
sudo journalctl -u whatsapp-bot

# Check Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Restarting Services

```bash
# Restart the bot
sudo systemctl restart whatsapp-bot

# Restart Nginx
sudo systemctl restart nginx
```

### Updating Your Bot

```bash
cd ~/whatsapp-money-tracker

# Pull latest code (if using Git)
git pull

# Or upload new files (if using SCP)
# (Run this on your local machine)
scp -i your-key.pem -r updated-files/* ubuntu@your-static-ip:~/whatsapp-money-tracker/

# Activate virtual environment
source venv/bin/activate

# Install any new dependencies
pip install -r requirements.txt

# Restart the service
sudo systemctl restart whatsapp-bot
```

## Cost Considerations

- **Lightsail Instance**: $5/month for the basic plan
- **Static IP**: Free when attached to a running instance
- **Data Transfer**: 1 TB/month included (more than enough for this bot)
- **Twilio Costs**: As outlined in the README.md file

## Troubleshooting

- **Bot not starting**: Check logs with `sudo journalctl -u whatsapp-bot`
- **Nginx errors**: Check logs with `sudo tail -f /var/log/nginx/error.log`
- **Can't connect to WhatsApp**: Verify the webhook URL in Twilio is correct
- **SSL issues**: Run `sudo certbot --nginx` again to troubleshoot
