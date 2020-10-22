# bot.py
import os # for importing env vars for the bot to use
from twitchio.ext import commands
from dotenv import load_dotenv
import actions
import config
import api

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

    # bot.py, at the bottom of event_message
    if message.startswith("!"):
        split_msg = message.strip('!').split(' ')
        cmd = split_msg[0]
        args = split_msg[1:] if len(split_msg) > 0 else None

        if cmd == "connect":
            server_ip = args[0]
            reply = actions.connect(server_ip)
            await ctx.Channel.send(reply)
        elif cmd == "switch":
            api.send_input(config.get_bind("+attack"))
        elif cmd == "scores":
            api.hold_key(config.get_bind("+scores"), 2000)
        elif cmd == "triggers":
            api.send_input(config.get_bind("toggle scr_triggers_draw 0 1"))
        elif cmd == "clips":
            api.send_input(config.get_bind("toggle scr_clips_draw 0 1"))
        elif cmd == "cgaz":
            api.send_input(config.get_bind("toggle df_hud_cgaz 0 13"))
        elif cmd == "snaps":
            api.send_input(config.get_bind("toggle scr_hud_snap_draw 0 1"))
        elif cmd == "checkpoints":
            api.send_input(config.get_bind("toggle df_checkpoints 0 2"))
        elif cmd == "nodraw":
            api.send_input(config.get_bind("toggle df_mp_NoDrawRadius 100 100000"))
        elif cmd == "angles":
            api.send_input(config.get_bind("toggle df_chs1_Info6 0 40"))
        elif cmd == "obs":
            api.send_input(config.get_bind("toggle df_chs1_Info7 0 50"))
        elif cmd == "clean":
            api.send_input(config.get_bind("toggle cg_draw2D 0 1"))
    return


if __name__ == "__main__":
    bot.run()
