import requests
import webbrowser
from urllib.parse import urlencode
from utils import *
from dataclasses import dataclass
import random
import os
import asyncio
import websockets
import signal

TWITCH_WS_URI = "wss://irc-ws.chat.twitch.tv:443"

def src(*paths: str) -> str:
    """Get the full path to a resource file in a subdirectory."""
    return os.path.join(os.path.dirname(__file__), *paths)

@dataclass
class PrivateMessage:
    tags: dict[str, str]
    channel: str
    user: str
    message: str

    def __init__(self, message: str):
        message_without_at = message[1:] if message.startswith("@") else message

        # Separate on first instance of a space. First part is tags_str, and second part is command_str
        tags_str, command_str = message_without_at.split(" ", 1)

        # tags_list = tags_str split by semi-colon
        tags_list: list[str] = tags_str.split(";")

        tags_dict: dict[str, str] = dict()
        # tags_dict = tags_list where each tag is formatted like "key=value"
        for tag in tags_list:
            if "=" in tag:
                key, value = tag.split("=", 1)
                tags_dict[key] = value

        # Retrieve channel, name, and message from command. Example above. Format is the following: :<user>!<user>@<user>.tmi.twitch.tv PRIVMSG #<channel> :<message>
        user_part, channel_message_part = command_str.split(" PRIVMSG ", 1)
        user = user_part[1:].split("!")[0]  # Remove leading ":" and extract username before "!"

        channel_part, message_part = channel_message_part.split(" :", 1)
        channel = channel_part[1:]  # Remove "#" prefix from channel

        self.tags = tags_dict
        self.channel = channel
        self.user = user
        self.message = message_part.strip()
        
    def __str__(self) -> str:
        display_name = self.tags.get("display-name", self.user)
        return f"[#{self.channel}] {display_name}: {self.message}"

async def write(filename, content):
    """Write content to a file in a separate thread to avoid blocking the event loop"""
    def _write(filename, content):
        with open(filename, "w") as f:
            return f.write(content)
    
    return await asyncio.to_thread(_write, filename, content)

class NuitBot:

    def __init__(self, nick: str, channel: str) -> None:

        self._nick = nick
        self._channel = channel.lower()

        self._access_token = ""
        self._refresh_token = ""

        self._running = True

    def get_access_token(self):
        return self._access_token

    def get_refresh_token(self):
        return self._refresh_token

    def authorize(self, client_id: str, redirect_uri: str, scopes: list[str]):
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

    def token(self, client_id: str, client_secret: str, code: str, redirect_uri: str):
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

    async def _join(self, ws: websockets.ClientConnection):
        await ws.send("CAP REQ :twitch.tv/commands twitch.tv/tags")

        # Authenticate
        await ws.send(f"PASS oauth:{self._access_token}")
        await ws.send(f"NICK {self._nick}")
        await ws.send(f"JOIN #{self._channel}")

        print(green(f"Connected to Twitch channel: #{self._channel}"))

    async def _websocket_connect(uri: str):
        try:
            socket = await websockets.connect(uri)
            print(green(f"WebSocket connection established"))
            return socket
        except Exception as e:
            print(red(f"WebSocket connection failed: {e}"))
            return None

    async def _run(self):
        try:
            async with websockets.connect(TWITCH_WS_URI) as ws:
                await self._join(ws)

                while self._running:
                    try:
                        # Use a timeout to allow checking the running flag
                        command = await asyncio.wait_for(ws.recv(), timeout=1.0)
                        print(blue(f"IRC: {command.strip()}"))

                        # Ping
                        if command.startswith("PING"):
                            await ws.send("PONG")
                            print(cyan("Sent PONG response"))

                        # For messages received
                        elif "PRIVMSG" in command:

                            private_message = PrivateMessage(command)
                            print(private_message.message)

                            # Handle commands
                            if private_message.message.startswith("!"):
                                command = private_message.message.split()[0].lower()
                                
                                # Random number from 1 to 100
                                guess = random.randint(1, 100)

                                # if number is 1, send no.
                                if guess == 1:
                                    response = f"PRIVMSG {private_message.channel} :MrDestructoid no."
                                    await ws.send(response)
                                    print(cyan(f"Bot response: no."))
                                else:
                                    if command == "!tts":
                                        response = f"PRIVMSG {private_message.channel} :MrDestructoid Use my Text to Speech: https://rhed.rhamzthev.com/donate"
                                        await ws.send(response)
                                        print(cyan(f"Command: {command}"))
                                    
                                    elif command == "!minecraft" or command == "!mc":
                                        response = f"PRIVMSG {private_message.channel} :MrDestructoid Join our Minecraft Server: minecraft.rhamzthev.com"
                                        await ws.send(response)
                                        print(cyan(f"Command: {command}"))

                                    elif command == "!discord":
                                        response = f"PRIVMSG {private_message.channel} :MrDestructoid Join our Discord: https://discord.gg/jFKFhWBMbb"
                                        await ws.send(response)
                                        print(cyan(f"Command: {command}"))

                                    # TODO: Make these.
                                    elif command == "!watchtime":
                                        continue

                                    elif command == "!followtime":
                                        continue

                                    elif command == "!sr":
                                        continue
                                    
                            elif private_message.message.startswith("#"):
                                if local_ws:
                                    try:
                                        display_name = private_message.tags.get("display-name")
                                        command = private_message.message + f" --name {display_name}"
                                        await local_ws.send(command)
                                        print(cyan(f"Local WS: {command}"))
                                    except Exception as e:
                                        print(red(f"Local WS error: {e}"))
                                        # Try to reconnect
                                        try:
                                            local_ws = await websockets.connect("ws://localhost:8765")
                                            print(green("Local WS reconnected"))
                                        except:
                                            local_ws = None

                            # This will have {text} mentality., where text is the text to say. We'll update mentality.txt with this content. Then we'll do everything else.
                            elif private_message.message.endswith("mentality."):
                                    try:
                                        print(yellow(f"Mentality trigger detected"))
                                        
                                        # Extract the text before "mentality."
                                        await write(src("texts", "mentality.txt"), private_message.message)
                                        await write(src("texts", "mentality_name.txt"), private_message.tags.get("display-name"))
                                        
                                        await asyncio.sleep(3)

                                        print(magenta("Trigger: alt+Scroll_Lock"))
                                        # key alt+scroll lock
                                        proc = await asyncio.create_subprocess_exec("xdotool", "key", "alt+Scroll_Lock")
                                        await proc.wait()
                                        
                                        print(magenta("Playing mentality sound"))
                                        # Play mentality.wav from sounds/
                                        proc = await asyncio.create_subprocess_exec(
                                            "aplay", 
                                            src("sounds", "mentality.wav")
                                        )
                                        await proc.wait()  # Wait for sound to finish playing
                                        
                                        print(magenta("Trigger: alt+Scroll_Lock"))
                                        # Press the key combo again
                                        proc = await asyncio.create_subprocess_exec("xdotool", "key", "alt+Scroll_Lock")
                                        await proc.wait()
                                        
                                        print(green("Mentality sequence complete"))
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
                    await ws.send(f"PART #{private_message.channel}")
                    print(yellow(f"Left Twitch channel: #{private_message.channel}"))
                except:
                    pass

        except Exception as e:
            print(red(f"Bot error: {e}"))
        finally:
            print(yellow("Bot shutdown complete"))

    def _signal_handler(self):
        self._running = False
        print(red("Shutdown signal received - bot will exit shortly"))

    async def run(self):
        # Only set up signal handlers if we're in the main thread
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, self._signal_handler)
        except RuntimeError:
            # Not in main thread, can't set signal handlers
            print(yellow("Running in thread - signal handlers unavailable"))
        
        await self._run()