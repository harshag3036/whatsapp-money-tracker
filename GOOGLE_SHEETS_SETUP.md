# Setting Up Google Sheets Integration

This guide will walk you through setting up the Google Sheets integration for your WhatsApp Money Tracker Bot.

## Step 1: Install Required Dependencies

First, install the Google API libraries:

```bash
pip install -r google_sheets_requirements.txt
```

## Step 2: Set Up Google Cloud Project

1. **Create a Google Cloud Project**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Click "New Project" and create a project
   - Note your Project ID

2. **Enable Google Sheets API**:
   - In your project, go to "APIs & Services" > "Library"
   - Search for "Google Sheets API" and enable it

3. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Select "Desktop app" as the application type
   - Name your OAuth client
   - Click "Create"
   - Download the JSON file (it will be named something like `client_secret_XXXX.json`)

4. **Rename and Move the Credentials File**:
   - Rename the downloaded file to `credentials.json`
   - Move it to the root of your WhatsApp Money Tracker project

## Step 3: First Run and Authentication

When you run the application for the first time, it will:

1. Detect that you don't have a `token.json` file
2. Open a browser window asking you to log in to your Google account
3. Ask for permission to access your Google Sheets
4. Redirect you to a success page
5. Save the authentication token to `token.json` for future use

This authentication flow only happens once, unless the token expires or is deleted.

## Step 4: Verify Google Sheet Access

1. Make sure you can access the Google Sheet at:
   [https://docs.google.com/spreadsheets/d/1O4HXZ3qKlRuVodnpNDmuvzif3B5Hbo8xfZKpin5wLfM/edit](https://docs.google.com/spreadsheets/d/1O4HXZ3qKlRuVodnpNDmuvzif3B5Hbo8xfZKpin5wLfM/edit)

2. If you want to use a different Google Sheet:
   - Create a new Google Sheet
   - Share it with the email address associated with your Google Cloud project
   - Update the `SPREADSHEET_ID` in `src/sheets_manager.py` with your new Sheet ID (the long string in the URL)

## Step 5: Restart the Application

After completing the setup, restart your application:

```bash
python3 run.py
```

## Troubleshooting

### "Error: credentials.json not found"
- Make sure you've downloaded the OAuth credentials and named the file `credentials.json`
- Make sure the file is in the root directory of your project

### Authentication Issues
- If you see authentication errors, delete the `token.json` file (if it exists) and try again
- Make sure you're using the correct Google account that has access to the spreadsheet

### Permission Issues
- Make sure the Google Sheet is shared with your Google account
- If using a service account, make sure the sheet is shared with the service account email

### "Invalid Client" Error
- Make sure your OAuth consent screen is properly configured
- If you're using a test project, add your email as a test user

## For Production Deployment

For production deployment (e.g., on AWS Lightsail), you have two options:

### Option 1: Use OAuth Credentials (Requires Initial User Interaction)

1. Complete the OAuth flow locally to generate `token.json`
2. Copy both `credentials.json` and `token.json` to your server
3. Place them in the root directory of your project on the server

This approach works but has limitations:
- The token may expire and require manual refresh
- Not ideal for fully automated deployments

### Option 2: Use Service Account Authentication (Recommended)

This is the recommended approach for production as it doesn't require user interaction:

1. **Create a Service Account**:
   - In Google Cloud Console, go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Enter a name and description
   - Click "Create and Continue"
   - Add the "Editor" role (or a more specific role like "Sheets Editor")
   - Click "Done"

2. **Create and Download Key**:
   - Find your new service account in the list
   - Click on the three dots menu > "Manage keys"
   - Click "Add Key" > "Create new key"
   - Select JSON format
   - Click "Create" to download the key file

3. **Share Your Google Sheet**:
   - Open your Google Sheet
   - Click the "Share" button
   - Add the service account email (it looks like `something@project-id.iam.gserviceaccount.com`)
   - Give it "Editor" access
   - Click "Share"

4. **Deploy the Key**:
   - Rename the downloaded key file to `service-account.json`
   - Place it in the root directory of your project on the server

The code has been updated to automatically use the service account if available, falling back to OAuth only if necessary.

## Service Account vs. OAuth: Which to Choose?

| Feature | Service Account | OAuth |
|---------|----------------|-------|
| User interaction | None required | Required for initial setup |
| Token expiration | No expiration | Tokens expire and need refresh |
| Security | More secure for server deployment | Better for personal use |
| Setup complexity | Slightly more complex | Simpler initial setup |
| Best for | Production servers, automation | Development, personal use |

For your WhatsApp bot on AWS Lightsail, the service account approach is strongly recommended.
