# bot.py
import os # for importing env vars for the bot to use
from twitchio.ext import commands
from dotenv import load_dotenv
import actions
import config
import api
import subprocess
import servers

load_dotenv()

# bot setup
bot = commands.Bot(
    irc_token=os.environ['TMI_TOKEN'],
    client_id=os.environ['CLIENT_ID'],
    nick=os.environ['BOT_NICK'],
    prefix=os.environ['BOT_PREFIX'],
    initial_channels=[os.environ['CHANNEL']]
)

@bot.event
async def event_ready():
    """Called once when the bot goes online."""
    print(f"{os.environ['BOT_NICK']} is online!")
    ws = bot._ws  # this is only needed to send messages within event_ready
    await ws.send_privmsg(os.environ['CHANNEL'], f"/me has landed!")

@bot.event
async def event_message(ctx):
    """Activates for every message"""

    message = ctx.content.lower()
    # make sure the bot ignores itself and the streamer
    # if ctx.author.name.lower() == os.environ['BOT_NICK'].lower():
    #     return
    print("received message:", message)
    # bot.py, at the bottom of event_message
    if message.startswith("?"):
        print("command received")
        message = message.strip('?')
        if ";" in message:
            message = message[:message.index(";")]
        split_msg = message.split(' ')
        cmd = split_msg[0]

        if cmd == "connect":
            api.exec_command(message)
        elif cmd == "switch":
            try:
                api.press_key_mult(config.get_bind("+attack"), int(split_msg[1]) % 10, 0.2)
            except:
                api.press_key(config.get_bind("+attack"))
        elif cmd == "scores":
            api.hold_key(config.get_bind("+scores"), 3.5)
        elif cmd == "triggers":
            api.press_key(config.get_bind_fuzzy("scr_triggers_draw"))
        elif cmd == "clips":
            api.press_key(config.get_bind_fuzzy("scr_clips_draw"))
        elif cmd == "snaps":
            api.press_key(config.get_bind_fuzzy("scr_hud_snap_draw"))
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
        elif cmd == "cv" and "kick" not in message:
            api.exec_command(f"{message}")

    elif message.startswith(">"):
        print("chat message sent")
        message = message.strip('>')
        if ";" in message:
            message = message[:message.index(";")]
        api.exec_command(f"say !me ^7{ctx.author.name}:^2{message}")

    elif message.startswith("!"):
        print("proxy command received")
        if ";" in message:
            message = message[:message.index(";")]
        api.exec_command(message)
    return


def launch():
    connect_ip = servers.get_most_popular_server()

    df_parent = os.path.dirname(config.DF_DIR)
    df_exe_p = os.path.join(df_parent, config.DF_EXE_NAME)

    if not os.path.isfile(df_exe_p):
        print("Could not find engine, quitting...")
        sys.exit()

    # Make sure to set proper CWD when using subprocess.Popen from another directory
    # iDFe will automatically take focus when launching
    process = subprocess.Popen(args=[df_exe_p, "+connect", connect_ip], stdout=subprocess.PIPE, creationflags=0x08000000, cwd=df_parent)


if __name__ == "__main__":
    config.read_cfg()
    launch()
    bot.run()
