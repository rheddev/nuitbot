from typing import Any, Optional, Callable
import requests
import webbrowser
from urllib.parse import urlencode
from utils import *
from dataclasses import dataclass
import random
import os
import asyncio
import websockets
from websockets import State
import signal
import json
import hashlib
import base64
import uuid

# WebSocket URIs and configuration
TWITCH_WS_URI = "wss://irc-ws.chat.twitch.tv:443"

# OBS WebSocket configuration from environment variables
OBS_HOST = os.getenv("OBS_HOST", "localhost")
OBS_PORT = os.getenv("OBS_PORT", "4455")
OBS_PASSWORD = os.getenv("OBS_PASSWORD", "")

OBS_URL = f"ws://{OBS_HOST}:{OBS_PORT}"

# Set to True if you want to connect the websocket client
ENABLE_LOCAL_WS = False
ENABLE_OBS_WS = True

def is_closed(ws: Optional[websockets.ClientConnection]) -> bool:
    """Check if a websocket connection is closed.
    
    Args:
        ws: The websocket connection to check
        
    Returns:
        True if the connection is closed or None, False otherwise
    """
    return ws is None or ws.state is State.CLOSED or ws.state is State.CLOSING

def is_open(ws: Optional[websockets.ClientConnection]) -> bool:
    """Check if a websocket connection is open.
    
    Args:
        ws: The websocket connection to check
        
    Returns:
        True if the connection is open, False otherwise
    """
    return ws is not None and ws.state is State.OPEN

def src(*paths: str) -> str:
    """Get the full path to a resource file in a subdirectory."""
    return os.path.join(os.path.dirname(__file__), *paths)

def generate_auth_response(password: str, challenge: str, salt: str) -> str:
    """Generate authentication response based on OBS WebSocket protocol.
    
    Args:
        password: The OBS WebSocket password
        challenge: The challenge string from OBS WebSocket server
        salt: The salt string from OBS WebSocket server
        
    Returns:
        The authentication string to send back to OBS
    """
    # Step 1: Concatenate password and salt
    combined: str = password + salt
    
    # Step 2: Generate SHA256 hash and base64 encode (base64 secret)
    sha256_hash = hashlib.sha256(combined.encode()).digest()
    base64_secret = base64.b64encode(sha256_hash).decode()
    
    # Step 3: Concatenate base64_secret with challenge
    combined_secret_challenge = base64_secret + challenge
    
    # Step 4: Generate SHA256 hash of the result and base64 encode
    sha256_hash_final = hashlib.sha256(combined_secret_challenge.encode()).digest()
    authentication_string = base64.b64encode(sha256_hash_final).decode()
    
    return authentication_string

@dataclass
class PrivateMessage:
    """Represents a private message from Twitch IRC.
    
    Attributes:
        tags: Dictionary of IRC tags
        channel: The channel the message was sent to
        user: The user who sent the message
        message: The message content
    """
    tags: dict[str, str]
    channel: str
    user: str
    message: str

    def __init__(self, message: str):
        """Parse a raw IRC message into its components.
        
        Args:
            message: Raw IRC message string
        """
        message_without_at = message[1:] if message.startswith("@") else message

        # Separate on first instance of a space. First part is tags_str, and second part is command_str
        tags_str, command_str = message_without_at.split(" ", 1)

        # Parse tags (format: key=value;key=value;...)
        tags_list: list[str] = tags_str.split(";")
        tags_dict: dict[str, str] = dict()
        for tag in tags_list:
            if "=" in tag:
                key, value = tag.split("=", 1)
                tags_dict[key] = value

        # Parse command parts
        # Format: :<user>!<user>@<user>.tmi.twitch.tv PRIVMSG #<channel> :<message>
        user_part, channel_message_part = command_str.split(" PRIVMSG ", 1)
        user = user_part[1:].split("!")[0]  # Remove leading ":" and extract username before "!"

        channel_part, message_part = channel_message_part.split(" :", 1)
        channel = channel_part[1:]  # Remove "#" prefix from channel

        self.tags = tags_dict
        self.channel = channel
        self.user = user
        self.message = message_part.strip()
        
    def __str__(self) -> str:
        """String representation of the message."""
        display_name = self.tags.get("display-name", self.user)
        return f"[#{self.channel}] {display_name}: {self.message}"

async def write(filename, content):
    """Write content to a file asynchronously.
    
    Args:
        filename: Path to the file
        content: Content to write
        
    Returns:
        Result of the write operation
    """
    def _write(filename, content):
        with open(filename, "w") as f:
            return f.write(content)
    
    return await asyncio.to_thread(_write, filename, content)

class NuitBot:
    """Twitch chat bot with OBS integration.
    
    This bot connects to Twitch chat and OBS WebSocket to handle commands
    and trigger actions.
    """

    def __init__(self, nick: str, channel: str) -> None:
        """Initialize the bot with a nickname and channel.
        
        Args:
            nick: Bot's nickname on Twitch
            channel: Channel to join (without # prefix)
        """
        self._nick = nick
        self._channel = channel.lower()

        self._access_token = ""
        self._refresh_token = ""

        self._running = True

    def get_access_token(self) -> str:
        """Get the current access token."""
        return self._access_token

    def get_refresh_token(self) -> str:
        """Get the current refresh token."""
        return self._refresh_token

    def authorize(self, client_id: str, redirect_uri: str, scopes: list[str]) -> None:
        """Open browser for Twitch OAuth authorization.
        
        Args:
            client_id: Twitch application client ID
            redirect_uri: OAuth redirect URI
            scopes: List of permission scopes to request
        """
        # Make scopes space-separated
        scope_str: str = " ".join(scopes)

        # Get the user to authorize your app
        authorize_url = "https://id.twitch.tv/oauth2/authorize"
        params_dict = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope_str
        }

        # Encode query params
        params = urlencode(params_dict)

        # Put it all together
        url = f"{authorize_url}?{params}"

        webbrowser.open(url)

    def token(self, client_id: str, client_secret: str, code: str, redirect_uri: str) -> None:
        """Exchange authorization code for access and refresh tokens.
        
        Args:
            client_id: Twitch application client ID
            client_secret: Twitch application client secret
            code: Authorization code from redirect
            redirect_uri: OAuth redirect URI
        """
        token_url = "https://id.twitch.tv/oauth2/token"
        payload = {
            "client_id": client_id,
            "client_secret": client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": redirect_uri
        }

        response = requests.post(token_url, data=payload)
        response_json: dict[str, str] = response.json()

        self._access_token = response_json.get("access_token")
        self._refresh_token = response_json.get("refresh_token")

    async def _join(self, ws: websockets.ClientConnection) -> None:
        """Join a Twitch channel and authenticate with the server.
        
        Args:
            ws: WebSocket connection to Twitch IRC
        """
        # Request additional capabilities
        await ws.send("CAP REQ :twitch.tv/commands twitch.tv/tags")

        # Authenticate
        await ws.send(f"PASS oauth:{self._access_token}")
        await ws.send(f"NICK {self._nick}")
        await ws.send(f"JOIN #{self._channel}")

        print(green(f"Connected to Twitch channel: #{self._channel}"))

    async def _websocket_connect(self, uri: str, callback=None, max_retries=3) -> Optional[websockets.ClientConnection]:
        """Connect to a WebSocket server with error handling and retry logic.
        
        Args:
            uri: WebSocket server URI
            callback: Optional callback function to execute after connection
            max_retries: Maximum number of connection attempts
            
        Returns:
            WebSocket connection or None if all connection attempts failed
        """
        retries = 0
        while retries <= max_retries:
            try:
                socket = await websockets.connect(uri, ping_interval=20, ping_timeout=10)
                print(green(f"Connected to {uri}"))
                if callback:
                    await callback(socket)
                return socket
            except Exception as e:
                retries += 1
                if retries <= max_retries:
                    wait_time = 2 ** retries  # Exponential backoff
                    print(yellow(f"Connection to {uri} failed (attempt {retries}/{max_retries}): {e}"))
                    print(yellow(f"Retrying in {wait_time} seconds..."))
                    await asyncio.sleep(wait_time)
                else:
                    print(red(f"Connection to {uri} failed after {max_retries} attempts: {e}"))
                    if callback and callback.__code__.co_argcount > 1:
                        await callback(None, e)
                    return None

    async def _reconnect_websocket(self, socket, uri, callback=None, max_retries=3):
        """Attempt to reconnect a WebSocket that has disconnected.
        
        Args:
            socket: The disconnected socket to replace
            uri: WebSocket server URI
            callback: Optional callback function to execute after reconnection
            max_retries: Maximum number of reconnection attempts
            
        Returns:
            New WebSocket connection or None if reconnection failed
        """
        if socket and not is_closed(socket):
            try:
                await socket.close()
            except:
                pass
                
        print(yellow(f"Attempting to reconnect to {uri}..."))
        return await self._websocket_connect(uri, callback, max_retries)

    async def _obs_connect(self, websocket: websockets.ClientConnection) -> None:
        """Handle OBS WebSocket authentication flow.
        
        Args:
            websocket: WebSocket connection to OBS
        """
        # Receive the initial OpCode 0 message
        hello_message = await websocket.recv()
        hello_data = json.loads(hello_message)
        print(green("OBS: Hello message received"))

        if hello_data["op"] == 0:
            challenge = hello_data["d"]["authentication"]["challenge"]
            salt = hello_data["d"]["authentication"]["salt"]
            rpc_version = hello_data["d"]["rpcVersion"]
            
            # Generate authentication string
            auth_string = generate_auth_response(OBS_PASSWORD, challenge, salt)
            
            # Create OpCode 1 message
            auth_payload = {
                "op": 1,
                "d": {
                    "rpcVersion": rpc_version,
                    "authentication": auth_string
                }
            }
            
            # Send authentication response
            print(green("OBS: Sending authentication"))
            await websocket.send(json.dumps(auth_payload))
            
            # Receive authentication result
            auth_result = await websocket.recv()
            auth_result_data = json.loads(auth_result)
            print(green("OBS: Authentication complete"))

    async def _obs_trigger_hotkey(self, websocket: websockets.ClientConnection, request_data: dict[str, Any]) -> None:
        """Trigger an OBS hotkey via WebSocket.
        
        Args:
            websocket: WebSocket connection to OBS
            request_data: Data containing the key sequence to trigger
        """
        request_id = str(uuid.uuid4())
        hotkey_request = {
            "op": 6,
            "d": {
                "requestType": "TriggerHotkeyByKeySequence",
                "requestId": request_id,
                "requestData": request_data
            }
        }

        # Send request to trigger hotkey
        print(cyan("OBS: Triggering hotkey"))
        await websocket.send(json.dumps(hotkey_request))
        
        # Receive response
        await websocket.recv()
        print(cyan("OBS: Hotkey triggered"))

    async def _run(self) -> None:
        """Main bot operation loop with reconnection logic."""
        
        obs_ws = None
        local_ws = None
        reconnect_attempts = 0
        max_reconnect_attempts = 5

        while self._running and reconnect_attempts <= max_reconnect_attempts:
            try:
                # If you aren't using one, just comment the if statement out to prevent blocking

                # Connect to OBS WebSocket server
                if ENABLE_OBS_WS:
                    if obs_ws is None or is_closed(obs_ws):
                        obs_ws = await self._websocket_connect(OBS_URL, self._obs_connect)
                        if not obs_ws:
                            print(red("Failed to connect to OBS. Continuing without OBS integration."))
                
                # Connect to local WebSocket server (if available)
                if ENABLE_LOCAL_WS:
                    if local_ws is None or is_closed(local_ws):
                        local_ws = await self._websocket_connect("ws://localhost:8765")
                        if not local_ws:
                            print(yellow("Local WebSocket server not available. Some features will be disabled."))
            
                # Connect to Twitch IRC
                async with websockets.connect(TWITCH_WS_URI, ping_interval=20, ping_timeout=10) as ws:
                    await self._join(ws)
                    reconnect_attempts = 0  # Reset reconnect attempts on successful connection
                    
                    # Main message handling loop
                    while self._running:
                        try:
                            # Monitor OBS and local websocket connections
                            if obs_ws and is_closed(obs_ws):
                                print(yellow("OBS WebSocket connection lost. Attempting to reconnect..."))
                                obs_ws = await self._reconnect_websocket(obs_ws, OBS_URL, self._obs_connect)
                                
                            if local_ws and is_closed(local_ws):
                                print(yellow("Local WebSocket connection lost. Attempting to reconnect..."))
                                local_ws = await self._reconnect_websocket(local_ws, "ws://localhost:8765")
                                
                            # Use a timeout to allow checking the running flag
                            command = await asyncio.wait_for(ws.recv(), timeout=1.0)
                            print(blue(f"IRC: {command.strip()}"))

                            # Handle PING messages
                            if command.startswith("PING"):
                                await ws.send("PONG")
                                print(cyan("Sent PONG response"))

                            # Handle PRIVMSG messages (chat messages)
                            elif "PRIVMSG" in command:
                                private_message = PrivateMessage(command)
                                print(private_message.message)

                                # Handle bot commands (starting with !)
                                if private_message.message.startswith("!"):
                                    command = private_message.message.split()[0].lower()
                                    
                                    # 1% chance to respond with "no" to any command
                                    guess = random.randint(1, 100)
                                    if guess == 1:
                                        response = f"PRIVMSG #{private_message.channel} :MrDestructoid no."
                                        await ws.send(response)
                                        print(cyan(f"Bot response: no."))
                                        continue
                                    
                                    # Process specific commands
                                    if command == "!tts":
                                        response = f"PRIVMSG #{private_message.channel} :MrDestructoid Use my Text to Speech: https://rhed.rhamzthev.com/donate"
                                        await ws.send(response)
                                        print(cyan(f"Command: {command}"))
                                    
                                    elif command == "!minecraft" or command == "!mc":
                                        response = f"PRIVMSG #{private_message.channel} :MrDestructoid Join our Minecraft Server: minecraft.rhamzthev.com"
                                        await ws.send(response)
                                        print(cyan(f"Command: {command}"))

                                    elif command == "!discord":
                                        response = f"PRIVMSG #{private_message.channel} :MrDestructoid Join our Discord: https://discord.gg/jFKFhWBMbb"
                                        await ws.send(response)
                                        print(cyan(f"Command: {command}"))

                                    # TODO: Implement these commands
                                    elif command in ["!watchtime", "!followtime", "!sr"]:
                                        continue
                                
                                # Handle local WebSocket commands (starting with #)
                                elif private_message.message.startswith("#"):
                                    if local_ws and is_open(local_ws):
                                        try:
                                            display_name = private_message.tags.get("display-name")
                                            command = private_message.message + f" --name {display_name}"
                                            await local_ws.send(command)
                                            print(cyan(f"Local WS: {command}"))
                                        except Exception as e:
                                            print(red(f"Local WS error: {e}"))
                                            # Try to reconnect
                                            local_ws = await self._reconnect_websocket(local_ws, "ws://localhost:8765")

                                # Handle mentality trigger messages (ending with "mentality.")
                                elif private_message.message.endswith("mentality."):
                                    try:
                                        print(magenta("Mentality triggered"))
                                        
                                        # Save the message and username
                                        await write(src("text", "mentality.txt"), private_message.message)
                                        await write(src("text", "mentality_name.txt"), private_message.tags.get("display-name"))
                                        
                                        # Wait for the scene transition
                                        await asyncio.sleep(3)

                                        # Only trigger OBS if connection is available
                                        if obs_ws and is_open(obs_ws):
                                            # Trigger scene transition in OBS
                                            print(magenta("Scene transition"))
                                            await self._obs_trigger_hotkey(obs_ws, {
                                                "keyId": "OBS_KEY_SCROLLLOCK",
                                                "keyModifiers": {
                                                    "alt": True
                                                }
                                            })
                                        else:
                                            print(yellow("OBS not connected, skipping scene transition"))
                                        
                                        # Play the sound effect
                                        print(magenta("Playing sound"))
                                        proc = await asyncio.create_subprocess_exec(
                                            "aplay", 
                                            src("sound", "mentality.wav")
                                        )
                                        await proc.wait()  # Wait for sound to finish playing
                                        
                                        # Only trigger OBS if connection is available
                                        if obs_ws and is_open(obs_ws):
                                            # Trigger scene transition back
                                            print(magenta("Scene transition"))
                                            await self._obs_trigger_hotkey(obs_ws, {
                                                "keyId": "OBS_KEY_SCROLLLOCK",
                                                "keyModifiers": {
                                                    "alt": True
                                                }
                                            })
                                        else:
                                            print(yellow("OBS not connected, skipping scene transition"))
                                        
                                        print(green("Mentality complete"))
                                    except Exception as e:
                                        print(red(f"Mentality error: {e}"))
                        
                        except asyncio.TimeoutError:
                            # This is expected, just continue the loop to check if we should exit
                            continue
                        except websockets.exceptions.ConnectionClosed:
                            print(red("Twitch connection closed"))
                            break

                    # Send a proper goodbye message if we're still connected
                    try:
                        await ws.send(f"PART #{self._channel}")
                        print(yellow(f"Left Twitch channel: #{self._channel}"))
                    except:
                        pass
                        
            except Exception as e:
                reconnect_attempts += 1
                wait_time = min(30, 2 ** reconnect_attempts)  # Exponential backoff with max of 30 seconds
                
                if reconnect_attempts <= max_reconnect_attempts:
                    print(red(f"Bot error: {e}"))
                    print(yellow(f"Attempting to reconnect in {wait_time} seconds... (Attempt {reconnect_attempts}/{max_reconnect_attempts})"))
                    await asyncio.sleep(wait_time)
                else:
                    print(red(f"Bot failed to run after {max_reconnect_attempts} attempts. Shutting down."))
                    break
                    
        # Cleanup
        try:
            # Close all open WebSocket connections
            if obs_ws and not is_closed(obs_ws):
                await obs_ws.close()
            if local_ws and not is_closed(local_ws):
                await local_ws.close()
        except:
            pass
            
        print(yellow("Bot shutdown complete"))

    def _signal_handler(self) -> None:
        """Handle shutdown signals gracefully."""
        self._running = False
        print(red("Shutdown signal received - bot will exit shortly"))

    async def run(self) -> None:
        """Run the bot and set up signal handlers."""
        # Signal handlers removed as they may cause errors
        print(yellow("Use Ctrl+C to stop the process"))
        
        await self._run()