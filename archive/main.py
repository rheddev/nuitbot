import asyncio
import websockets
import os
import signal
import random
import requests
from dotenv import load_dotenv

load_dotenv()

# Replace with your values
TWITCH_OAUTH = os.getenv("TWITCH_OAUTH")
TWITCH_NICK = os.getenv("TWITCH_NICK")
TWITCH_CHANNEL = os.getenv("TWITCH_CHANNEL")

# ANSI color codes
GREEN = "\033[32m"
RED = "\033[31m"
BLUE = "\033[34m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
MAGENTA = "\033[35m"
RESET = "\033[0m"

# Helper functions for colored text
def green(text): return f"{GREEN}{text}{RESET}"
def red(text): return f"{RED}{text}{RESET}"
def blue(text): return f"{BLUE}{text}{RESET}"
def cyan(text): return f"{CYAN}{text}{RESET}"
def yellow(text): return f"{YELLOW}{text}{RESET}"
def magenta(text): return f"{MAGENTA}{text}{RESET}"

# Global variable to control the main loop
running = True

async def write(filename, content):
    """Write content to a file in a separate thread to avoid blocking the event loop"""
    def _write(filename, content):
        with open(filename, "w") as f:
            return f.write(content)
    
    return await asyncio.to_thread(_write, filename, content)

async def websocket_connect(uri: str):
    try:
        socket = await websockets.connect(uri)
        print(green(f"Connected to {socket}"))
        return socket
    except Exception as e:
        print(red(f"Failed to connect to {uri}: {e}"))
        return None

async def twitch_chat_bot():
    uri = "wss://irc-ws.chat.twitch.tv:443"
    local_ws = None
    # obs_ws = None
    
    try:
        # Connect to local WebSocket server(s)
        local_ws = await websocket_connect("ws://localhost:8765")
        # obs_ws = websocket_connect("...")
    
        async with websockets.connect(uri) as ws:
            # Request commands and tags capabilities
            await ws.send("CAP REQ :twitch.tv/commands twitch.tv/tags")

            # Authenticate
            await ws.send(f"PASS oauth:{TWITCH_OAUTH}")
            await ws.send(f"NICK {TWITCH_NICK}")
            await ws.send(f"JOIN #{TWITCH_CHANNEL}")

            print(green(f"Connected to #{TWITCH_CHANNEL}"))

            while running:
                try:
                    # Use a timeout to allow checking the running flag
                    message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    print(blue(f"Received: {message.strip()}"))

                    if message.startswith("PING"):
                        await ws.send("PONG")
                        print(cyan("Sent PONG"))

                    elif "PRIVMSG" in message:
                        # Parse and print user messages
                        # Extract username and message content
                        parts = message.split("PRIVMSG")[1].split(":", 1)
                        if len(parts) > 1:
                            channel = parts[0].strip()
                            content = parts[1].strip()
                            
                            # Extract display name from tags
                            display_name = None
                            if "display-name=" in message:
                                tags = message.split(";")
                                for tag in tags:
                                    if tag.startswith("display-name="):
                                        display_name = tag.split("=")[1]
                                        break
                            
                            # Handle commands
                            if content.startswith("!"):
                                command = content.split()[0].lower()
                                
                                # Random number from 1 to 100
                                guess = random.randint(1, 100)

                                # if number is 1, send no.
                                if guess == 1:
                                    response = "MrDestructoid no."
                                    await ws.send(response)
                                    print(cyan(f"Sent: {response}"))
                                else:
                                    if command == "!tts":
                                        response = f"PRIVMSG {channel} :MrDestructoid Use my Text to Speech: https://rhed.rhamzthev.com/donate"
                                        await ws.send(response)
                                        print(cyan(f"Sent: {response}"))
                                    
                                    elif command == "!minecraft" or command == "!mc":
                                        response = f"PRIVMSG {channel} :MrDestructoid Join our Minecraft Server: minecraft.rhamzthev.com"
                                        await ws.send(response)
                                        print(cyan(f"Sent: {response}"))

                                    elif command == "!discord":
                                        response = f"PRIVMSG {channel} :MrDestructoid Join our Discord: https://discord.gg/jFKFhWBMbb"
                                        await ws.send(response)
                                        print(cyan(f"Sent: {response}"))

                                    # TODO: Make these.
                                    elif command == "!watchtime":
                                        continue

                                    elif command == "!followtime":
                                        continue

                                    elif command == "!sr":
                                        continue
                                    
                            elif content.startswith("#"):
                                if local_ws:
                                    try:
                                        message = content
                                        if display_name:
                                            message += f" --name {display_name}"
                                        await local_ws.send(message)
                                        print(cyan(f"Sent to local WebSocket: {message}"))
                                    except Exception as e:
                                        print(red(f"Failed to send to local WebSocket: {e}"))
                                        # Try to reconnect
                                        try:
                                            local_ws = await websockets.connect("ws://localhost:8765")
                                            print(green("Reconnected to local WebSocket server"))
                                        except:
                                            local_ws = None

                            # This will have {text} mentality., where text is the text to say. We'll update mentality.txt with this content. Then we'll do everything else.
                            elif content.endswith("mentality."):
                                try:
                                    print(yellow(f"Processing mentality command: {content}"))
                                    
                                    # Extract the text before "mentality."
                                    print(yellow(f"Writing to mentality.txt: {content}"))
                                    
                                    # Replace mentality.txt with the text - run in thread
                                    await write("mentality.txt", content)
                                    await write("mentality_name.txt", display_name)
                                    
                                    await asyncio.sleep(3)

                                    print(magenta("Pressing alt+Scroll_Lock first time"))
                                    # key alt+scroll lock
                                    await asyncio.create_subprocess_exec("xdotool", "keydown", "alt+Scroll_Lock")
                                    await asyncio.sleep(0.1)
                                    await asyncio.create_subprocess_exec("xdotool", "keyup", "alt+Scroll_Lock")
                                    await asyncio.sleep(0.1)
                                    
                                    print(magenta("Playing mentality.wav"))
                                    # Play mentality.wav from sounds/
                                    proc = await asyncio.create_subprocess_exec(
                                        "aplay", 
                                        "/home/rhamsez/Coding/rheddev/nuitbot/sounds/mentality.wav"
                                    )
                                    await proc.wait()  # Wait for sound to finish playing
                                    
                                    print(magenta("Pressing alt+Scroll_Lock second time"))
                                    # Press the key combo again
                                    await asyncio.sleep(0.06)
                                    await asyncio.create_subprocess_exec("xdotool", "keydown", "alt+Scroll_Lock")
                                    await asyncio.sleep(0.1)
                                    await asyncio.create_subprocess_exec("xdotool", "keyup", "alt+Scroll_Lock")
                                    
                                    print(green("Mentality command completed"))
                                except Exception as e:
                                    print(red(f"Error processing mentality command: {e}"))
                
                except asyncio.TimeoutError:
                    # This is expected, just continue the loop to check if we should exit
                    continue
                except websockets.exceptions.ConnectionClosed:
                    print(red("Connection closed"))
                    break
            
            # Send a proper goodbye message if we're still connected
            try:
                await ws.send(f"PART #{TWITCH_CHANNEL}")
                print(yellow(f"Left channel #{TWITCH_CHANNEL}"))
            except:
                pass
                
    except Exception as e:
        print(red(f"Error: {e}"))
    finally:
        print(yellow("Bot shutdown complete"))

def signal_handler():
    global running
    running = False
    print(red("\nShutting down bot gracefully... (this may take a moment)"))

async def main():
    # Set up signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    # Run the Minecraft server

    await twitch_chat_bot()

if __name__ == "__main__": 
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # This is a fallback in case the signal handler doesn't work
        print(red("\nShutting down via KeyboardInterrupt"))
    print(yellow("Bot has exited."))
