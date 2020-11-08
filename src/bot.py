# bot.py
import os # for importing env vars for the bot to use
from twitchio.ext import commands
import config
import api
import subprocess
import servers
import time
import console
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
            api.exec_command(message)
        elif cmd == "restart":
            connect_ip = servers.get_most_popular_server()
            api.press_key_mult("esc", 2)
            api.press_key("enter")
            api.press_key_mult("tab", 10)
            api.press_key("enter")
            time.sleep(1)
            api.exec_command(f"connect {connect_ip}")
        elif cmd == "next":
            try:
                api.press_key_mult(config.get_bind("+attack"), int(split_msg[1]) % 10, 0.2)
            except:
                api.press_key(config.get_bind("+attack"))
        elif cmd == "prev":
            try:
                api.press_key_mult(config.get_bind("+speed;wait 10;-speed"), int(split_msg[1]) % 10, 0.2)
            except:
                api.press_key(config.get_bind("+speed;wait 10;-speed"))
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

    df_parent = os.path.dirname(config.DF_DIR)
    df_exe_p = os.path.join(df_parent, config.DF_EXE_NAME)

    if not os.path.isfile(df_exe_p):
        print("Could not find engine or it was not provided. You will have to start the engine and the bot manually. ")
        return None

    # Make sure to set proper CWD when using subprocess.Popen from another directory
    # iDFe will automatically take focus when launching
    process = subprocess.Popen(args=[df_exe_p, "+connect", connect_ip], stdout=subprocess.PIPE, creationflags=0x08000000, cwd=df_parent)

    return df_exe_p


if __name__ == "__main__":
    config.read_cfg()
    df_exe_p = launch()

    logfile_path = config.DF_DIR + '\\qconsole.log'
    con_process = threading.Thread(target=console.read, args=(logfile_path,), daemon=True)
    con_process.start()

    api.api_init(df_exe_p)

    bot.run()
    