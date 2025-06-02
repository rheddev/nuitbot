import asyncio
import json
import os
import hashlib
import base64
import uuid
from dotenv import load_dotenv
import websockets

# Load environment variables from .env file
load_dotenv()

# Get OBS WebSocket credentials from environment variables
OBS_HOST = os.getenv("OBS_HOST", "localhost")
OBS_PORT = os.getenv("OBS_PORT", "4455")
OBS_PASSWORD = os.getenv("OBS_PASSWORD", "")

# Construct WebSocket URL
ws_url = f"ws://{OBS_HOST}:{OBS_PORT}"

def generate_auth_response(password, challenge, salt):
    """Generate authentication response based on OBS WebSocket protocol"""
    # Step 1: Concatenate password and salt
    combined = password + salt
    
    # Step 2: Generate SHA256 hash and base64 encode (base64 secret)
    sha256_hash = hashlib.sha256(combined.encode()).digest()
    base64_secret = base64.b64encode(sha256_hash).decode()
    
    # Step 3: Concatenate base64_secret with challenge
    combined_secret_challenge = base64_secret + challenge
    
    # Step 4: Generate SHA256 hash of the result and base64 encode
    sha256_hash_final = hashlib.sha256(combined_secret_challenge.encode()).digest()
    authentication_string = base64.b64encode(sha256_hash_final).decode()
    
    return authentication_string

async def connect_to_obs():
    """Connect to OBS WebSocket and listen for messages"""
    print(f"Attempting to connect to OBS WebSocket at {ws_url}")
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("Connected to OBS WebSocket")
            
            # Receive the initial OpCode 0 message
            hello_message = await websocket.recv()
            hello_data = json.loads(hello_message)
            print(f"Received hello message (OpCode 0):\n{json.dumps(hello_data, indent=2)}")
            
            # Extract authentication challenge and salt
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
                print(f"Sending authentication response (OpCode 1)")
                await websocket.send(json.dumps(auth_payload))
                
                # Receive authentication result
                auth_result = await websocket.recv()
                auth_result_data = json.loads(auth_result)
                print(f"Received authentication result:\n{json.dumps(auth_result_data, indent=2)}")
                
                # Check if authentication was successful (OpCode 2)
                if auth_result_data["op"] == 2:
                    print("Authentication successful! Requesting hotkey list...")
                    
                    # Create OpCode 6 message to trigger hotkey by key sequence
                    request_id = str(uuid.uuid4())
                    hotkey_request = {
                        "op": 6,
                        "d": {
                            "requestType": "TriggerHotkeyByKeySequence",
                            "requestId": request_id,
                            "requestData": {
                                "keyId": "OBS_KEY_SCROLLLOCK",
                                "keyModifiers": {
                                    "alt": True
                                }
                            }
                        }
                    }
                    
                    # Send request to trigger hotkey
                    print(f"Sending request to trigger hotkey by key sequence (OpCode 6) with requestId: {request_id}")
                    await websocket.send(json.dumps(hotkey_request))
                    
                    # Receive response
                    hotkey_response = await websocket.recv()
                    hotkey_data = json.loads(hotkey_response)
                    print(f"Received hotkey trigger response:\n{json.dumps(hotkey_data, indent=2)}")
                
                # Keep listening for messages
                while True:
                    message = await websocket.recv()
                    # Parse JSON message
                    try:
                        data = json.loads(message)
                        print(f"Received: {json.dumps(data, indent=2)}")
                    except json.JSONDecodeError:
                        print(f"Received non-JSON message: {message}")
            else:
                print(f"Unexpected first message format: {hello_data}")
    
    except websockets.exceptions.ConnectionClosedError as e:
        print(f"Connection closed: {e}")
    except Exception as e:
        print(f"Error connecting to OBS WebSocket: {e}")

if __name__ == "__main__":
    # Run the async function
    asyncio.run(connect_to_obs())
