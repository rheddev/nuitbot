# Nuitbot

A Twitch chatbot built with Python.

## Prerequisites

- Python 3.0+ installed on your machine

## Setup Development Environment

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
# Your Twitch API credentials
# See instructions below for obtaining these credentials
TWITCH_CLIENT_ID=your_client_id_here
TWITCH_CLIENT_SECRET=your_client_secret_here

# Whatever nickname you want this chatbot to be
TWITCH_NICK=

# The Twitch channel you want this chatbot to join (MUST BE IN LOWERCASE)
TWITCH_CHANNEL=
```

### 3. Authenticate with Twitch

Simply run:

```bash
./nuitbot
```

This will:
1. Start a local Flask server on port 5000
2. Open your browser to the authentication page
3. Guide you through the Twitch authentication process
4. Store your access and refresh tokens automatically

### 4. Start the Bot

After authentication, the bot will start automatically.

## Setting up Twitch API Credentials

### 1. Register an Application

1. Go to https://dev.twitch.tv/console
2. Click on "Register Your Application"
3. Fill in the required information:
   - Name: Choose a name for your application
   - OAuth Redirect URLs: Set to `http://localhost:5000/callback`
   - Category: Select "Chat Bot"
4. Click "Create"
5. Click "Manage" for the application you just registered
6. Copy your Client ID and generate a new Client Secret by clicking "New Secret"
7. Add these values to your `.env` file as TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET
