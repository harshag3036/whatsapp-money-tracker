# Fixing Google OAuth "Error 403: access_denied" Issue

The error you're seeing occurs because your Google Cloud project is in "Testing" mode and needs additional configuration. Here's how to fix it:

## Option 1: Add Your Email as a Test User

1. **Go to Google Cloud Console**:
   - Visit [https://console.cloud.google.com/](https://console.cloud.google.com/)
   - Select your project

2. **Configure OAuth Consent Screen**:
   - Navigate to "APIs & Services" > "OAuth consent screen"
   - Make sure "External" is selected (not "Internal")
   - Scroll down to the "Test users" section
   - Click "Add Users"
   - Add your email address (`harshag3036@gmail.com`)
   - Save the changes

3. **Try Authentication Again**:
   - Run your application again
   - The authentication should now work

## Option 2: Use Service Account Authentication (Recommended)

Instead of using OAuth, you can use a service account which doesn't require user interaction:

1. **Create a Service Account**:
   - In Google Cloud Console, go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Enter a name (e.g., "WhatsApp Money Tracker")
   - Click "Create and Continue"
   - Add the "Editor" role
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

4. **Use the Service Account Key**:
   - Rename the downloaded key file to `service-account.json`
   - Place it in the root directory of your project
   - The code is already set up to use this file if it exists

## Option 3: Fix OAuth Configuration

If you prefer to use OAuth, you may need to fix your OAuth configuration:

1. **Check Authorized Redirect URIs**:
   - Go to "APIs & Services" > "Credentials"
   - Click on your OAuth client ID
   - Under "Authorized redirect URIs", make sure `http://localhost:62428/` is added
   - Add any other redirect URIs you might be using
   - Save the changes

2. **Verify API Scopes**:
   - Go to "APIs & Services" > "OAuth consent screen"
   - Make sure the Google Sheets API scope is added
   - Save the changes

3. **Recreate Credentials File**:
   - You might need to download a new credentials file
   - Go to "APIs & Services" > "Credentials"
   - Click on your OAuth client ID
   - Click "Download JSON"
   - Rename the downloaded file to `credentials.json`
   - Replace your existing `credentials.json` file

## Additional Troubleshooting

If you're still having issues:

1. **Delete Existing Token**:
   - If a `token.json` file exists, delete it
   - This will force a new authentication flow

2. **Check API Enablement**:
   - Make sure the Google Sheets API is enabled
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Make sure it shows as "Enabled"

3. **Verify Project Status**:
   - If your project is new, it might take a few minutes for settings to propagate
   - Try waiting 5-10 minutes and then retry

4. **Check Console Logs**:
   - Look for any additional error messages in your console
   - These might provide more specific information about the issue

## Recommendation

For your WhatsApp Money Tracker bot, especially if you plan to deploy it to AWS Lightsail, I strongly recommend using the Service Account approach (Option 2). It's more reliable for server deployments and doesn't require user interaction.
