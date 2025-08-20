# Salesforce Metadata API Setup Guide

## Overview
This guide will help you set up Metadata API access for your Salesforce developer account to retrieve detailed profile and permission set metadata.

## Step 1: Create a Connected App

### 1.1 Navigate to Setup
1. Log into your Salesforce developer account
2. Go to **Setup** (gear icon in top right)
3. In the Quick Find box, type "Connected Apps"
4. Click **Connected Apps**

### 1.2 Create New Connected App
1. Click **New**
2. Fill in the basic information:
   - **Connected App Name**: `Metadata API Access`
   - **API Name**: `Metadata_API_Access` (auto-generated)
   - **Contact Email**: Your email address
   - **Logo Image**: Optional
   - **Icon**: Optional
   - **Info URL**: Optional
   - **Privacy Policy URL**: Optional
   - **Terms of Service URL**: Optional

### 1.3 Enable OAuth Settings
1. Check **Enable OAuth Settings**
2. Set **Callback URL**: `https://login.salesforce.com/services/oauth2/callback`
3. Select **OAuth Scopes**:
   - ✅ **Access and manage your data (api)**
   - ✅ **Perform requests at any time (refresh_token, offline_access)**
   - ✅ **Access custom permissions (custom_permissions)**
   - ✅ **Access metadata through the Metadata API (api)**

### 1.4 Save and Get Credentials
1. Click **Save**
2. You'll be redirected to the Connected App detail page
3. **Important**: Click **Continue** to complete the setup
4. Note down these values:
   - **Consumer Key** (Client ID)
   - **Consumer Secret** (Client Secret)

## Step 2: Create a Named Credential (Optional but Recommended)

### 2.1 Navigate to Named Credentials
1. In Setup, search for "Named Credentials"
2. Click **Named Credentials**

### 2.2 Create New Named Credential
1. Click **New**
2. Fill in the details:
   - **Label**: `Salesforce_Metadata_API`
   - **Name**: `Salesforce_Metadata_API` (auto-generated)
   - **URL**: `https://login.salesforce.com/services/oauth2/token`
   - **Identity Type**: `Named Principal`
   - **Authentication Protocol**: `OAuth 2.0`
   - **Authentication Provider**: Select your org's authentication provider (usually your org name)
   - **Scope**: `api refresh_token`
   - **Generate Authorization Header**: ✅ Checked
   - **Allow Merge Fields in HTTP Body**: ✅ Checked

## Step 3: Create a User for API Access

### 3.1 Create API User
1. In Setup, search for "Users"
2. Click **Users**
3. Click **New User**
4. Fill in required fields:
   - **First Name**: `API`
   - **Last Name**: `User`
   - **Email**: `api-user@yourdomain.com` (use a real email you can access)
   - **Username**: `api-user@yourdomain.com`
   - **Profile**: `System Administrator` (for full access)
   - **Email Encoding**: `UTF-8`
   - **Language**: `English`
   - **Locale**: `English (United States)`
   - **Time Zone**: Your timezone

### 3.2 Set Password
1. Uncheck **Generate password and notify user via email**
2. Set a strong password manually
3. Note down the password

## Step 4: Get Access Token

### 4.1 Using Salesforce CLI (Recommended)
```bash
# Authenticate with your API user
sf org login web --alias METADATA_API_USER --instance-url https://login.salesforce.com

# Get the access token
sf org display --target-org METADATA_API_USER --verbose
```

### 4.2 Using Postman or cURL
```bash
curl -X POST https://login.salesforce.com/services/oauth2/token \
  -d "grant_type=password" \
  -d "client_id=YOUR_CONSUMER_KEY" \
  -d "client_secret=YOUR_CONSUMER_SECRET" \
  -d "username=api-user@yourdomain.com" \
  -d "password=YOUR_PASSWORD"
```

## Step 5: Environment Variables

Create a `.env` file in your project root:

```env
# Salesforce Metadata API Credentials
SF_CONSUMER_KEY=your_consumer_key_here
SF_CONSUMER_SECRET=your_consumer_secret_here
SF_USERNAME=api-user@yourdomain.com
SF_PASSWORD=your_password_here
SF_LOGIN_URL=https://login.salesforce.com

# Or if using access token directly
SF_ACCESS_TOKEN=your_access_token_here
SF_INSTANCE_URL=https://your-instance.salesforce.com
```

## Step 6: Test the Setup

### 6.1 Test with Salesforce CLI
```bash
# Test metadata API access
sf org list metadata --metadata-type Profile --target-org METADATA_API_USER
```

### 6.2 Test with Python
```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

# Get access token
def get_access_token():
    url = f"{os.getenv('SF_LOGIN_URL')}/services/oauth2/token"
    data = {
        'grant_type': 'password',
        'client_id': os.getenv('SF_CONSUMER_KEY'),
        'client_secret': os.getenv('SF_CONSUMER_SECRET'),
        'username': os.getenv('SF_USERNAME'),
        'password': os.getenv('SF_PASSWORD')
    }
    
    response = requests.post(url, data=data)
    return response.json()['access_token']

# Test metadata API
def test_metadata_api():
    access_token = get_access_token()
    instance_url = f"{os.getenv('SF_LOGIN_URL').replace('login', 'your-instance')}"
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # List profiles
    url = f"{instance_url}/services/data/v64.0/sobjects/Profile"
    response = requests.get(url, headers=headers)
    print("Profiles:", response.json())

if __name__ == "__main__":
    test_metadata_api()
```

## Troubleshooting

### Common Issues:
1. **"Invalid client"**: Check your Consumer Key and Secret
2. **"Invalid username/password"**: Verify API user credentials
3. **"Insufficient access"**: Ensure API user has System Administrator profile
4. **"IP_RESTRICTION"**: Check if your org has IP restrictions

### Security Best Practices:
1. Use a dedicated API user (not your main admin account)
2. Store credentials securely (use environment variables)
3. Regularly rotate passwords
4. Monitor API usage in Setup → Monitoring → Event Monitoring

## Next Steps

Once you have the credentials set up, we can enhance the pipeline to use the Metadata API for retrieving detailed profile and permission set metadata, which will give us much more comprehensive security information than the current approach.
