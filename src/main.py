import os
import webbrowser
import threading
from flask import Flask, request, redirect, render_template
from dotenv import load_dotenv
from nuitbot import NuitBot
import asyncio
from utils import *

# Load environment variables
load_dotenv()

app: Flask = Flask(__name__, template_folder='templates')

# Get Twitch API credentials from environment variables
CLIENT_ID = os.getenv("TWITCH_CLIENT_ID")
CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET")
REDIRECT_URI = os.getenv("TWITCH_REDIRECT_URI")
SCOPES = ["chat:read", "chat:edit"]

nuitbot = NuitBot("NuitBot", "RhedDev")

# Call authorize when Flask starts
with app.app_context():
    nuitbot.authorize(CLIENT_ID, REDIRECT_URI, SCOPES)

# Create a function to run the bot in a separate thread
def run_bot_thread():
    print(yellow("Starting NuitBot in background thread"))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(nuitbot.run())
    except KeyboardInterrupt:
        print(red("Bot shutdown: KeyboardInterrupt received"))
    except Exception as e:
        print(red(f"Bot error: {e}"))
    finally:
        print(yellow("NuitBot has stopped"))
        loop.close()

# Store tokens globally (in a real app, you'd want to use a proper storage mechanism)
@app.route('/callback')
def callback():
    # Get authorization code from URL
    code = request.args.get('code')
    
    if not code:
        return "Error: No authorization code received", 400
    
    # Use the authorization code to get a token
    nuitbot.token(CLIENT_ID, CLIENT_SECRET, code, REDIRECT_URI)
    
    # Start the bot in a separate thread after getting the token
    bot_thread = threading.Thread(target=run_bot_thread, daemon=True)
    bot_thread.start()
    
    return render_template('success.html'), 200

# if __name__ == "__main__":
#     app.run(debug=True)
