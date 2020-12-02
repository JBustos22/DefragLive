import asyncio
from aiorun import run
import json
import websockets
import argparse

USERS = set()

async def notify_message(message_obj):
    if USERS:  # asyncio.wait doesn't accept an empty list
        message = json.dumps(message_obj)
        await asyncio.wait([user.send(message) for user in USERS])

def register(websocket):
    USERS.add(websocket)

def unregister(websocket):
    USERS.remove(websocket)

async def ws_server(websocket, path):
    # register(websocket) sends user_event() to websocket
    register(websocket)
    print('New connection (%s total)!' % len(USERS))

    try:
        async for message in websocket:
            data = json.loads(message)
            print(data)
            if data['action'] == "message":
                await notify_message(data)
            else:
                print("unsupported message: {}", data)
    except websockets.exceptions.ConnectionClosedError:
        print('Connection closed abnormally!')
        await websocket.close()
    finally:
        unregister(websocket)

async def main(args):
    print(f'Starting WS server ({args.host}:{args.port})...\n')
    await websockets.serve(ws_server, args.host, args.port)
    await asyncio.sleep(1.0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='WebSocket server for Defrag/Twitch bot.')
    parser.add_argument('--host', dest='host', default='localhost', help='Host or IP address to connect to.')
    parser.add_argument('--port', dest='port', default=5005, help='Port to connect to.')
    args = parser.parse_args()

    run(main(args))
