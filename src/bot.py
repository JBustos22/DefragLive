# bot.py
import os # for importing env vars for the bot to use
from twitchio.ext import commands
import config
import api
import subprocess
import servers
import time
import console
import serverstate
from env import environ
import threading
import asyncio
import websockets
import json
from multiprocessing import Process
import logging
from datetime import datetime
import sys
import pathlib
import twitch_commands

df_channel = environ['CHANNEL'] if 'CHANNEL' in environ and environ['CHANNEL'] != "" else input("Your twitch channel name: ")

# To add any sound command, add the command name to the list of commands
# then add the sound file to the music/common/ directory in the /defrag/ folder
# Note: sound file name music be the same as command name (without $)
SOUND_CMDS = [
    '$4ity',
    '$holy',
    '$holy1'
]

# Twitch commands that start with (?), to add a command
# add it as an array inside this array, where multiple entries are aliases, and the first entry is the actual command
# also add the function of the command inside twitch_commands.py (command function must be named as the first entry of your command)
TWITCH_CMDS = [
    ["restart"],
    ["reconnect"],
    ["triggers"],
    ["clips"],
    ["clear"],
    ["lagometer"],
    ["snaps"],
    ["fixchat"],
    ["cgaz"],
    ["nodraw"],
    ["angles"],
    ["obs"],
    ["drawgun"],
##    ["clean"],
    ["sky"],
    ["speedinfo"],
    ["speedorig"],
    ["gibs"],
    ["blood"],
    ["thirdperson"],
    ["miniview"],
    ["inputs"],
    ["slick"],
    ["n1"],
    ["map"],
    ["check"],
##    ["speclist"],
    ["spec"],
    ["brightness"],
    ["picmip"],
    ["gamma"],
    ["connect", "c"],
    ["reshade"],
    ["next", "n"],
    ["prev", "p"],
##    ["scores", "scoreboard","score","scoreboards","scr","sc","scrs","scors","scroes","scar","scora","sorces","scoars","scs","scrose"],
    ["server", "sv"],
    ["ip"]
]

# bot setup
bot = commands.Bot(
    irc_token=environ['TMI_TOKEN'],
    client_id=environ['CLIENT_ID'],
    nick=environ['BOT_NICK'],
    prefix=environ['BOT_PREFIX'],
    initial_channels=[df_channel]
)

@bot.event
async def event_ready():
    """Called once when the bot goes online."""
    logging.info(f"{environ['BOT_NICK']} is online!")
    ws = bot._ws  # this is only needed to send messages within event_ready
    await ws.send_privmsg(df_channel, f"/me has landed!")


@bot.event
async def event_message(ctx):
    """Activates for every message"""
    debounce = 1  # interval between consecutive commands and messages
    author = ctx.author.name
    message = ctx.content

    if ";" in message:  # prevent q3 command injections
        message = message[:message.index(";")]

    # bot.py, at the bottom of event_message
    if message.startswith("?"):  # spectator client customization and controls
        message = message.strip('?').lower()
        split_msg = message.split(' ')
        cmd = split_msg[0]
        args = split_msg[1:] if len(split_msg) > 0 else None
        logging.info(f"TWITCH COMMAND RECEIVED: '{cmd}' from user '{author}'")

        for command in TWITCH_CMDS:
            if cmd in command:
                twitch_function = getattr(twitch_commands, command[0])
                await twitch_function(ctx, author, args)
        time.sleep(debounce)

    elif message.startswith(">") or message.startswith("<"):  # chat bridge
        message = message.lstrip('>').lstrip('<').lstrip(' ')
        blacklisted_words = config.get_list("blacklist_chat")

        for word in blacklisted_words:
            if word in message:
                logging.info(f"Blacklisted word '{word}' detected in message \"{message}\" by \"{author}\". Aborting message.")
                return

        if author.lower() == 'nightbot'.lower():  # ignore twitch Nightbot's name
            author = ''
            author_color_char = 0
        else:
            author += ' ^7> '
            author_color_char = author[0]

        api.exec_command(f"say ^{author_color_char}{author} ^2{message}")
        logging.info("Chat message sent")
        time.sleep(debounce)

    elif message.startswith("**"):  # team chat bridge
        message = message.lstrip('**')
        blacklisted_words = config.get_list("blacklist_chat")

        for word in blacklisted_words:
            if word in message:
                logging.info(f"Blacklisted word '{word}' detected in message \"{message}\" by \"{author}\". Aborting message.")
                return

        if author.lower() == 'nightbot'.lower():  # ignore twitch Nightbot's name
            author = ''
            author_color_char = 0
        else:
            author += ' ^7> '
            author_color_char = author[0]

        api.exec_command(f"say_team ^{author_color_char}{author} ^5{message}")
        logging.info("Chat message sent")
        time.sleep(debounce)

    elif message.startswith("!"):  # proxy mod commands (!top, !rank, etc.)
        logging.info("proxy command received")
        api.exec_command(message)
        time.sleep(debounce)

    elif  message.startswith("$"):  # viewer sound commands
        for sound_cmd in SOUND_CMDS:
            if message.startswith(sound_cmd):
                logging.info(f"Sound command recieved ({sound_cmd})")
                api.play_sound(sound_cmd.replace('$', '') + '.wav') #odfe appears to only support .wav format, not mp3, so we can hardcode it
                time.sleep(debounce)
    return


def launch():
    if environ['DEVELOPMENT']:
        launch_ip = servers.get_least_popular_server()
    else:
        launch_ip = servers.get_most_popular_server()

    if not os.path.isfile(config.DF_EXE_PATH):
        logging.info("Could not find engine or it was not provided. You will have to start the engine and the bot manually. ")
        return None

    # Make sure to set proper CWD when using subprocess.Popen from another directory
    # iDFe will automatically take focus when launching
    subprocess.Popen(args=[config.DF_EXE_PATH, "+cl_title", "TwitchBot Engine", "+con_title", "TwitchBot Console", "+connect", launch_ip], cwd=os.path.dirname(config.DF_EXE_PATH))


# ------------------------------------------------------------
# - Flask API for the twitch extension
# ------------------------------------------------------------

from flask import Flask, jsonify, request
app = Flask(__name__)


@app.route('/console')
def parsed_console_log():
    output = console.CONSOLE_DISPLAY[-75:] # [::-1] = reversed. console needs new messages at bottom
    output = jsonify(output)

    # TODO: fix CORS for production
    output.headers['Access-Control-Allow-Origin'] = '*'

    return output


@app.route('/console/raw')
def raw_console_log():
    output = console.LOG[::-1]
    output = jsonify(output)

    # TODO: fix CORS for production
    output.headers['Access-Control-Allow-Origin'] = '*'

    return output


@app.route('/console/send', methods=['POST'])
def send_message():
    author = request.form.get('author', None)
    message = request.form.get('message', None)
    command = request.form.get('command', None)

    if command is not None and command.startswith("!"):
        if ";" in command:  # prevent q3 command injections
            command = command[:command.index(";")]
        api.exec_command(command)
        return jsonify(result=f"Sent mdd command {command}")
    else:
        if ";" in message:  # prevent q3 command injections
            message = message[:message.index(";")]
        api.exec_command(f"say {author} ^7> ^2{message}")
        return jsonify(result=f"Sent {author} ^7> ^2{message}")

    return jsonify(result="Unknown message")


# ------------------------------------------------------------
# - Websocket client
# ------------------------------------------------------------

def on_ws_message(msg):
    message = {}

    if msg is None:
        return

    try:
        message = json.loads(msg)
    except Exception as e:
        logging.info('ERROR [on_ws_message]:', e)
        return

    # if there is no origin, exit
    # this function only processes messages directly from twitch console extension
    if 'origin' not in message:
            return
    
    if 'message' in message:
        if message['message'] is None:
            message['message'] = {}

        message_text = message['message']['content']

        if ";" in message_text:  # prevent q3 command injections
            message_text = message_text[:message_text.index(";")]

        if message_text.startswith("!"):  # proxy mod commands (!top, !rank, etc.)
            logging.info("proxy command received")
            api.exec_command(message_text)
            time.sleep(1)
        else:
            author = message['message']['author']
            author += ' ^7> '
            author_color_num = min(ord(author[0].lower()), 9) # replace ^[a-z] with ^[0-9]
            message_content = message_text.lstrip('>').lstrip('<')
            api.exec_command(f"say ^{author_color_num}{author} ^2{message_content}")


async def ws_send(uri, q):
    async with websockets.connect(uri) as websocket:
         while True:
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=0.5)
                on_ws_message(msg)
            except asyncio.TimeoutError:
                if not q.empty():
                    msg = q.get()
                    if msg == '>>quit<<':
                        await websocket.close(reason='KTHXBYE!')
                    else:
                        await websocket.send(msg)
            except:
                if(websocket.closed):
                    logging.info('\nDisconnected from WS server?')
                    logging.info('Trying reconnect. Please check if the websocket server is running!\n')
                    websocket = websockets.connect(uri)
                    
                await asyncio.sleep(1)
                continue


def ws_worker(q, loop):
    try:
        loop.run_until_complete(ws_send(config.WS_ADDRESS, q))
    except websockets.exceptions.WebSocketException as e:
        logging.info('\nWebsocket error:', e)
        logging.info('Please check if the websocket server is running!\n')
        time.sleep(1)
    finally:
        ws_worker(q, loop)


if __name__ == "__main__":
    config.read_cfg()
    window_flag = False

    twitchbot_logfile =f'{datetime.now().strftime("%m-%d-%Y_%H-%M-%S")}_twitchbot.log'
    file_handler = logging.FileHandler(filename=os.path.join(environ['LOG_DIR_PATH'], twitchbot_logfile))
    stdout_handler = logging.StreamHandler(sys.stdout)
    handlers = [file_handler, stdout_handler]
    logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S', level=logging.INFO, handlers=handlers)

    try:
        api.api_init()
        window_flag = True
        logging.info("Found defrag window.")
    except:
        logging.info("Defrag not running, starting...")
        df_process = Process(target=launch)
        df_process.start()
        time.sleep(15)

    from multiprocessing import Process

    logfile_path = config.DF_DIR + '\\qconsole.log'
    con_thread = threading.Thread(target=console.read, args=(logfile_path,), daemon=True)
    con_thread.start()

    serverstate_thread = threading.Thread(target=serverstate.start, daemon=True)
    serverstate_thread.start()

    # flask_thread = threading.Thread(target=app.run, daemon=True)
    # flask_thread.start()
    #
    # ws_loop = asyncio.new_event_loop()
    # ws_thread = threading.Thread(target=ws_worker, args=(console.WS_Q, ws_loop,), daemon=True)
    # ws_thread.start()

    bot_thread = threading.Thread(target=bot.run, daemon=True)
    bot_thread.start()

    while True:
        try:
            api.api_init()
            time.sleep(5)
            if not window_flag:
                logging.info("Found defrag window.")
                window_flag = True
                serverstate.PAUSE_STATE = False
        except api.WindowNotFoundError:
            if not serverstate.VID_RESTARTING:
                window_flag = False
                logging.info("Defrag window lost. Restarting...")
                df_process = Process(target=launch)
                df_process.start()
                console.STOP_CONSOLE = True
                time.sleep(12)
                con_thread = threading.Thread(target=console.read, args=(logfile_path,), daemon=True)
                con_thread.start()