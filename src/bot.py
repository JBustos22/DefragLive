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

df_channel = environ['CHANNEL'] if 'CHANNEL' in environ and environ['CHANNEL'] != "" else input("Your twitch channel name: ")

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
    print(f"{environ['BOT_NICK']} is online!")
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
        print(f"TWITCH COMMAND RECEIVED: '{cmd}' from user '{author}'")

        if cmd in ["connect", "c"]:
            ip = args[0]
            if ip.split(':')[0] not in config.get_list("whitelist_servers"):
                msg = f"Server \"{ip}\" is not whitelisted. Refusing connection."
                api.exec_command(f"cg_centertime 5;displaymessage 140 8 ^3{author} ^1{msg};")
                print(msg)
                await ctx.channel.send(msg)
                return
            serverstate.connect(ip)
        elif cmd == "restart":
            connect_ip = servers.get_most_popular_server()
            api.press_key_mult("{Esc}", 2)
            api.press_key("{Enter}")
            api.press_key_mult("{Tab}", 10)
            api.press_key("{Enter}")
            time.sleep(1)
            serverstate.connect(connect_ip)
        elif cmd in ["next", "n"]:
            await serverstate.switch_spec('next', channel=ctx.channel)
            api.exec_command(f"cg_centertime 2;displaymessage 140 12 ^3{author} ^7has switched to ^3Next player")
        elif cmd in ["prev", "p"]:
            await serverstate.switch_spec('prev', channel=ctx.channel)
            api.exec_command(f"cg_centertime 2;displaymessage 140 12 ^3{author} ^7has switched to ^3Previous player")
        elif cmd in ["scores", "scoreboard","score","scoreboards","scr","sc","scrs","scors","scroes","scar","scora","sorces","scoars","scs","scrose"]:
            api.hold_key(config.get_bind("+scores"), 4.5)
        elif cmd == "reconnect":
            serverstate.connect(serverstate.STATE.ip)
        elif cmd == "triggers":
            api.exec_command(f"toggle r_rendertriggerBrushes 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Render Triggers")
        elif cmd == "clips":
            api.exec_command(f"toggle r_renderClipBrushes 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Render Clips")
        elif cmd == "clear":
            api.exec_command(f"clear;cg_centertime 3;cg_centertime 3;displaymessage 140 12 ^3{author} ^1Ingame chat has been erased ^3:(")
        elif cmd == "lagometer":
            api.exec_command(f"toggle cg_lagometer 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Lagometer")
        elif cmd == "snaps":
            api.exec_command(f"toggle mdd_snap 0 3;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3snaps hud")
        elif cmd == "fixchat":
            api.exec_command(f"cl_noprint 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has fixed: ^3ingame chat")
        elif cmd == "cgaz":
            api.exec_command(f"toggle mdd_cgaz 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Cgaz hud")
        elif cmd == "nodraw":
            api.exec_command(f"toggle df_mp_NoDrawRadius 100 100000;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Players visibility")
        elif cmd == "angles":
            api.exec_command(f"toggle df_chs1_Info6 0 40;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Weapon angles")
        elif cmd == "obs":
            api.exec_command(f"toggle df_chs1_Info7 0 50;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3OverBounces")
        elif cmd == "drawgun":
            api.exec_command(f"toggle cg_drawgun 1 2;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Gun movement")
        elif cmd == "clean":
            api.exec_command(f"toggle cg_draw2D 0 1;wait 10;toggle mdd_hud 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Clean POV")
        elif cmd == "sky":
            api.exec_command(f"toggle r_fastsky 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Sky")
        elif cmd in ["vote", "f1", "f2"]:
            if cmd != "vote":
                arg = "yes" if cmd == "f1" else "no"
            else:
                arg = args[0]
            api.press_key(config.get_bind(f"vote {arg}"))
            api.exec_command(f"say ^3{author} ^7voted ^3{arg};cg_centertime 3;displaymessage 140 12 ^3{author} ^7voted ^3{arg}")
        elif cmd == "speedinfo":
            api.exec_command(f"toggle df_chs1_Info5 0 23;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Speedometer (chs info)")
        elif cmd == "speedorig":
            api.exec_command(f"toggle df_drawSpeed 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Speedometer (hud element)")
        elif cmd == "gibs":
            api.exec_command(f"toggle cg_gibs 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Gibs after kill")
        elif cmd == "blood":
            api.exec_command(f"toggle com_blood 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Blood after kill")
        elif cmd == "thirdperson":
            api.exec_command(f"toggle cg_thirdperson 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Thirdperson\n POV")
        elif cmd == "miniview":
            api.exec_command(f"toggle df_ghosts_MiniviewDraw 0 6;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Miniview")
        elif cmd == "inputs":
            api.exec_command(f"toggle df_chs0_draw 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Inputs (WASD...)")
        elif cmd == "slick":
            api.exec_command(f"toggle r_renderSlickSurfaces 0 1;cg_centertime 3;displaymessage 140 12 ^3{author} ^7has changed: ^3Slick highlighted")
        elif cmd == "n1":
            api.exec_command(f"varcommand say ^{author[0]}{author} ^7> ^2Nice one, $chsinfo(117) ^2!")
        elif cmd == "map":
            api.exec_state_command(f"cg_centertime 4;displaymessage 140 12 ^7The current map is: ^3{serverstate.STATE.mapname};")
            msg = f"The current map is: {serverstate.STATE.mapname}"
            await ctx.channel.send(msg)
        elif cmd == "speclist":
            msg = f"Watchable players:" \
                  f" {serverstate.STATE.get_specable_players()} " \
                  f"-- Do ?spec # to spectate a specific player, where # is their id number."
            await ctx.channel.send(msg)
            api.hold_key(config.get_bind("+scores"), 4.5)

            if len(serverstate.STATE.nospec_ids) > 0:
                nospec_msg = f"NOTE: " \
                       f"The following player{'s' if len(serverstate.STATE.nospec_ids) > 1 else ''} " \
                       f"{'have' if len(serverstate.STATE.nospec_ids) > 1 else 'has'} disabled spec permissions: " \
                       f"{serverstate.STATE.get_nospec_players()}"
                await ctx.channel.send(nospec_msg)

        elif cmd == "spec":
            follow_id = args[0]
            msg = serverstate.spectate_player(follow_id)
            await ctx.channel.send(msg)
            api.exec_state_command(f"cg_centertime 3;varcommand displaymessage 140 12 ^3{author} ^7has switched to $chsinfo(117)")

        elif cmd == "server" or cmd == "sv":
            msg = f"The current server is \"{serverstate.STATE.hostname}\" ({serverstate.STATE.ip})"
            await ctx.channel.send(msg)

        # Mod commands, 166 ;wait; needs to stay, otherwise error msg appears and cl_noprint 1 is somehow triggered
        elif cmd == "brightness":
            whitelisted_twitch_users = config.get_list('whitelist_twitchusers')
            if author not in whitelisted_twitch_users and not ctx.author.is_mod:
                await ctx.channel.send(f"{author}, you do not have the correct permissions to use this command. "
                                       f"Please message the broadcaster or a moderator.")
                return
            value = args[0]
            if value.isdigit() and (0 < int(value) <= 5):
                print("vid_restarting...")
                serverstate.VID_RESTARTING = True
                api.exec_command(f"r_mapoverbrightbits {value};vid_restart")
            else:
                await ctx.channel.send(f" {author}, the valid values for brightness are 1-5.")
        elif cmd == "picmip":
            whitelisted_twitch_users = config.get_list('whitelist_twitchusers')
            if author not in whitelisted_twitch_users and not ctx.author.is_mod:
                await ctx.channel.send(f"{author}, you do not have the correct permissions to use this command.")
                return
            value = args[0]
            if value.isdigit() and (0 <= int(value) <= 6):
                print("vid_restarting..")
                serverstate.VID_RESTARTING = True
                api.exec_command(f"r_picmip {value};vid_restart")
            else:
                await ctx.channel.send(f"{author}, the allowed values for picmip are 0-5.")

        # Disabled. Possibly useful for the future:

        # elif cmd == "cgaz":
        #     mode = args[0] if len(args) > 0 and 0 < int(args[0]) <= 15 else "toggle"
        #     if mode == "toggle":
        #         api.press_key(config.get_bind("toggle mdd_cgaz 0 1"))
        #     else:
        #         api.exec_command(f"df_hud_cgaz {mode}")

        # elif cmd == "cv" and "kick" not in message:
        #     api.exec_command(f"{message}")

        time.sleep(debounce)

    elif message.startswith(">") or message.startswith("<"):  # chat bridge
        message = message.lstrip('>').lstrip('<').lstrip(' ')
        blacklisted_words = config.get_list("blacklist_chat")

        for word in blacklisted_words:
            if word in message:
                print(f"Blacklisted word '{word}' detected in message \"{message}\" by \"{author}\". Aborting message.")
                return

        if author.lower() == 'nightbot'.lower():  # ignore twitch Nightbot's name
            author = ''
            author_color_char = 0
        else:
            author += ' ^7> '
            author_color_char = author[0]

        api.exec_command(f"say ^{author_color_char}{author} ^2{message}")
        print("Chat message sent")
        time.sleep(debounce)

    elif message.startswith("**"):  # team chat bridge
        message = message.lstrip('**')
        blacklisted_words = config.get_list("blacklist_chat")

        for word in blacklisted_words:
            if word in message:
                print(f"Blacklisted word '{word}' detected in message \"{message}\" by \"{author}\". Aborting message.")
                return

        if author.lower() == 'nightbot'.lower():  # ignore twitch Nightbot's name
            author = ''
            author_color_char = 0
        else:
            author += ' ^7> '
            author_color_char = author[0]

        api.exec_command(f"say_team ^{author_color_char}{author} ^5{message}")
        print("Chat message sent")
        time.sleep(debounce)

    elif message.startswith("!"):  # proxy mod commands (!top, !rank, etc.)
        print("proxy command received")
        api.exec_command(message)
        time.sleep(debounce)

    return


def launch():
    launch_ip = servers.get_most_popular_server()

    if not os.path.isfile(config.DF_EXE_PATH):
        print("Could not find engine or it was not provided. You will have to start the engine and the bot manually. ")
        return None

    # Make sure to set proper CWD when using subprocess.Popen from another directory
    # iDFe will automatically take focus when launching
    subprocess.Popen(args=[config.DF_EXE_PATH, "+connect", launch_ip], cwd=os.path.dirname(config.DF_EXE_PATH))


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
        print('ERROR [on_ws_message]:', e)
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
            print("proxy command received")
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
                    print('\nDisconnected from WS server?')
                    print('Trying reconnect. Please check if the websocket server is running!\n')
                    websocket = websockets.connect(uri)
                    
                await asyncio.sleep(1)
                continue


def ws_worker(q, loop):
    try:
        loop.run_until_complete(ws_send(config.WS_ADDRESS, q))
    except websockets.exceptions.WebSocketException as e:
        print('\nWebsocket error:', e)
        print('Please check if the websocket server is running!\n')
        time.sleep(1)
    finally:
        ws_worker(q, loop)


if __name__ == "__main__":
    config.read_cfg()
    window_flag = False

    try:
        api.api_init()
        window_flag = True
        print("Found defrag window.")
    except:
        print("Defrag not running, starting...")
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
                print("Found defrag window.")
                window_flag = True
                serverstate.PAUSE_STATE = False
        except api.WindowNotFoundError:
            if not serverstate.VID_RESTARTING:
                window_flag = False
                print("Defrag window lost. Restarting...")
                df_process = Process(target=launch)
                df_process.start()
                console.STOP_CONSOLE = True
                time.sleep(12)
                con_thread = threading.Thread(target=console.read, args=(logfile_path,), daemon=True)
                con_thread.start()