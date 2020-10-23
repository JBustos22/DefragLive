# bot.py
import os # for importing env vars for the bot to use
from twitchio.ext import commands
from dotenv import load_dotenv
import config
import api
import time

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
    author = ctx.author.name
    message = ctx.content
    # make sure the bot ignores itself and the streamer
    # if ctx.author.name.lower() == os.environ['BOT_NICK'].lower():
    #     return
    print("received message:", message)
    # bot.py, at the bottom of event_message
    if message.startswith("?"):  # spectator client customization and controls
        print("command received")
        message = message.strip('?').lower()
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
            api.press_key(config.get_bind("toggle scr_triggers_draw 0 1"))
        elif cmd == "clips":
            api.press_key(config.get_bind("toggle scr_clips_draw 0 1"))
        elif cmd == "snaps":
            api.press_key(config.get_bind("toggle scr_hud_snap_draw 0 1"))
        elif cmd == "checkpoints":
            api.press_key(config.get_bind("toggle df_checkpoints 0 2"))
        elif cmd == "nodraw":
            api.press_key(config.get_bind("toggle df_mp_NoDrawRadius 100 100000"))
        elif cmd == "angles":
            api.press_key(config.get_bind("toggle df_chs1_Info6 0 40"))
        elif cmd == "obs":
            api.press_key(config.get_bind("toggle df_chs1_Info7 0 50"))
        elif cmd == "clean":
            api.press_key(config.get_bind("toggle cg_draw2D 0 1"))
        elif cmd == "sky":
            api.press_key(config.get_bind("toggle r_fastsky 0 1"))
        elif cmd == "cv" and "kick" not in message:
            api.exec_command(f"{message}")

    elif message.startswith(">"):  # chat bridge
        print("chat message sent")
        message = message.strip('>')
        if ";" in message:
            message = message[:message.index(";")]
        api.exec_command(f"say !me ^7{author}:^2{message}")

    elif message.startswith("!"):  # proxy mod commands (!top, !rank, etc.)
        print("proxy command received")
        if ";" in message:
            message = message[:message.index(";")]
        api.exec_command(message)

    time.sleep(1)
    return


if __name__ == "__main__":
    bot.run()
