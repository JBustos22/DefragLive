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
    # make sure the bot ignores itself and the streamer
    if ctx.author.name.lower() == environ['BOT_NICK'].lower():
        return

    if ";" in message:  # prevent q3 command injections
        message = message[:message.index(";")]

    # bot.py, at the bottom of event_message
    if message.startswith("?"):  # spectator client customization and controls
        print("Command received")
        message = message.strip('?').lower()
        split_msg = message.split(' ')
        cmd = split_msg[0]
        args = split_msg[1:] if len(split_msg) > 0 else None

        if cmd == "connect":
            serverstate.connect(args[0])
        elif cmd == "restart":
            connect_ip = servers.get_most_popular_server()
            api.press_key_mult("{Esc}", 2)
            api.press_key("{Enter}")
            api.press_key_mult("{Tab}", 10)
            api.press_key("{Enter}")
            time.sleep(1)
            serverstate.connect(connect_ip)
        elif cmd == "next":
            serverstate.switch_spec(fwd=True)
        elif cmd == "prev":
            serverstate.switch_spec(fwd=False)
        elif cmd == "scores":
            api.hold_key(config.get_bind("+scores"), 3.5)
        elif cmd == "triggers":
            api.press_key(config.get_bind_fuzzy("scr_triggers_draw"))
        elif cmd == "clips":
            api.press_key(config.get_bind_fuzzy("scr_clips_draw"))
        elif cmd == "snaps":
            api.press_key(config.get_bind_fuzzy("mdd_snap"))
        elif cmd == "cgaz":
            api.press_key(config.get_bind_fuzzy("mdd_cgaz"))
        elif cmd == "checkpoints":
            api.press_key(config.get_bind_fuzzy("df_checkpoints"))
        elif cmd == "nodraw":
            api.press_key(config.get_bind_fuzzy("df_mp_NoDrawRadius"))
        elif cmd == "angles":
            api.press_key(config.get_bind("toggle df_chs1_Info6 0 40"))
        elif cmd == "obs":
            api.press_key(config.get_bind("toggle df_chs1_Info7 0 50"))
        elif cmd == "clean":
            api.press_key(config.get_bind_fuzzy("cg_draw2D"))
        elif cmd == "sky":
            api.press_key(config.get_bind_fuzzy("r_fastsky"))
        elif cmd == "vote":
            api.press_key(config.get_bind(f"vote {args[0]}"))
        elif cmd == "speedinfo":
            api.press_key(config.get_bind("toggle df_chs1_Info5 0 1"))
        elif cmd == "speedorig":
            api.press_key(config.get_bind_fuzzy("df_drawSpeed"))
        elif cmd == "huds":
            api.press_key(config.get_bind("toggle mdd_hud 0 1"))
        elif cmd == "inputs":
            api.press_key(config.get_bind_fuzzy("df_chs0_draw"))
        elif cmd == "n1":
            api.exec_command(api.exec_command(f"varcommand say ^{author[0]}{author} ^7> ^2Nice one, $chsinfo(117) ^2!"))

        # Mod commands
        elif cmd == "brightness":
            if not ctx.author.is_mod:
                await ctx.channel.send(f"{author}, you do not have the correct permissions to use this command.")
                return
            value = args[0]
            if value.isdigit() and (0 < int(value) <= 5):
                api.exec_command(f"r_mapoverbrightbits {value};vid_restart")
            else:
                await ctx.channel.send(f" {author}, the valid values for brightness are 1-5.")
        elif cmd == "picmip":
            if not ctx.author.is_mod:
                await ctx.channel.send(f"{author}, you do not have the correct permissions to use this command.")
                return
            value = args[0]
            if value.isdigit() and (0 <= int(value) <= 6):
                api.exec_command(f"r_picmip {value};vid_restart")
            else:
                await ctx.channel.send(f"{author}, the allowed values for picmip are 0-5.")

        # Currently disabled. Possibly useful for the future:

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
        if author.lower() == 'nightbot'.lower():  # ignore twitch Nightbot's name
            author = ''
            author_color_char = 0
        else:
            author += ' ^7> '
            author_color_char = author[0]
        message = message.lstrip('>').lstrip('<')
        api.exec_command(f"say ^{author_color_char}{author} ^2{message}")
        print("Chat message sent")
        time.sleep(debounce)

    elif message.startswith("!"):  # proxy mod commands (!top, !rank, etc.)
        print("proxy command received")
        api.exec_command(message)
        time.sleep(debounce)

    return


def launch():
    connect_ip = servers.get_most_popular_server()

    if not os.path.isfile(config.DF_EXE_P):
        print("Could not find engine or it was not provided. You will have to start the engine and the bot manually. ")
        return None

    # Make sure to set proper CWD when using subprocess.Popen from another directory
    # iDFe will automatically take focus when launching
    process = subprocess.Popen(args=[config.DF_EXE_P, "+map", "q3ctf1"], stdout=subprocess.PIPE, creationflags=0x08000000, cwd=os.path.dirname(config.DF_EXE_P))


# Flask api for the twitch extensions

from flask import Flask, jsonify, request
app = Flask(__name__)


@app.route('/console')
def parsed_console_log():
    output = console.LOG_PARSED[::-1]
    return jsonify(output)


@app.route('/console/raw')
def raw_console_log():
    output = console.CONSOLE_DISPLAY[::-1]
    return jsonify(output)


@app.route('/console/send', methods=['POST'])
def send_message():
    msg_json = request.get_json()
    author = msg_json.get("author", None)
    message = msg_json.get("message", None)
    command = msg_json.get("command", None)
    if command is not None and command.startswith("!"):
        if ";" in command:  # prevent q3 command injections
            command = command[:command.index(";")]
        api.exec_command(command)
        return f"Sent mdd command {command}"
    else:
        if ";" in message:  # prevent q3 command injections
            message = message[:message.index(";")]
        api.exec_command(f"say {author} ^7> ^2{message}")
        return f"Sent {author} ^7> ^2{message}"


if __name__ == "__main__":
    config.read_cfg()

    while True:
        try:
            api.api_init()
            break
        except:
            if input("Your DeFRaG engine is not running. Would you like us to launch it for you? [Y/n]: ").lower() == "y":
                launch()

                time.sleep(2)

    logfile_path = config.DF_DIR + '\\qconsole.log'
    con_process = threading.Thread(target=console.read, args=(logfile_path,), daemon=True)
    con_process.start()
    #flask_process = threading.Thread(target=app.run, daemon=True)
    #flask_process.start()
    #sv_log_path = config.DF_DIR + '\\system\\reports\\serverstate.txt'
    #sv_state_process = threading.Thread(target=initialize_serverstate, args=(sv_log_path,), daemon=True)
    #time.sleep(10)
    #sv_state_process.start()
    # sv_state = serverstate.Server('defrag.rocks')

    bot.run()
