# Nuitbot

A Twitch chatbot built with Python.

## Prerequisites

- Python 3.0+ installed on your machine

## Setup

### 1. Setup Python Environment

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create a `.env` file in the project root directory with the following content:

```
# Your USER access token. Not APP access token.
# See instructions below for obtaining your user access token
TWITCH_OAUTH=

# Whatever nickname you want this chatbot to be
TWITCH_NICK=

# The Twitch channel you want this chatbot to join (MUST BE IN LOWERCASE)
TWITCH_CHANNEL=
```

### 3. Start the Bot

When you have everything configured, simply run:

```
# In Linux/MacOS
python3 src/main.py

# In Windows
python src/main.py
```

## Creating a Twitch User Access Token

### Prerequisites:
- A Twitch account

### 1. Register an Application

1. Go to https://dev.twitch.tv/console
2. Click on "Register Your Application"
3. Fill in the required information:
   - Name: Choose a name for your application
   - OAuth Redirect URLs: Set to `http://localhost`
   - Category: Select "Chat Bot"
   - Client Type: Set to "Confidential"
4. Click "Create"
5. Click "Manage" for the application you just registered
6. Copy your Client ID and generate a new Client Secret by clicking "New Secret"

### 2. Retrieve a User Access Token

We'll be following the "Authorization code grant flow" as described in the [Twitch documentation](https://dev.twitch.tv/docs/authentication/getting-tokens-oauth/#authorization-code-grant-flow).

#### Step 1: Authorize the Application

Open a web browser and navigate to the following URL (replace `[YOUR CLIENT ID HERE]` with your actual Client ID):

```
https://id.twitch.tv/oauth2/authorize?response_type=code&client_id=[YOUR CLIENT ID HERE]&redirect_uri=http://localhost&scope=chat%3Aread%20chat%3Aedit
```

After authorizing, you'll be redirected to a URL like:

```
http://localhost/?code=[YOUR AUTHORIZATION CODE]&...
```

Copy the authorization code value.

#### Step 2: Exchange the Authorization Code for an Access Token

Send an HTTP POST request to the following endpoint (replace the placeholders with your actual values):

```
https://id.twitch.tv/oauth2/token?client_id=[YOUR CLIENT ID HERE]&client_secret=[YOUR CLIENT SECRET HERE]&code=[YOUR AUTHORIZATION CODE HERE]&grant_type=authorization_code&redirect_uri=http://localhost
```

You can use cURL, Postman, or any HTTP client to make this request.

On success, you'll receive a response like:

```json
{
  "access_token": "[YOUR ACCESS TOKEN]",
  "expires_in": 14400,
  "refresh_token": "[YOUR REFRESH TOKEN]",
  "scope": ["chat:read", "chat:edit"],
  "token_type": "bearer"
}
```

The `access_token` value is what you need to set as `TWITCH_OAUTH` in your `.env` file.
