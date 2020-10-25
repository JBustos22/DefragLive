# bot.py
import os # for importing env vars for the bot to use
from twitchio.ext import commands
import config
import api
import time
from env import environ

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
    debounce = 2
    author = ctx.author.name
    message = ctx.content
    # make sure the bot ignores itself and the streamer
    if ctx.author.name.lower() == environ['BOT_NICK'].lower():
        return

    # bot.py, at the bottom of event_message
    if message.startswith("?"):  # spectator client customization and controls
        print("Command received")
        message = message.strip('?').lower()
        if ";" in message:
            message = message[:message.index(";")]
        split_msg = message.split(' ')
        cmd = split_msg[0]
        args = split_msg[1:] if len(split_msg) > 0 else None

        if cmd == "connect":
            api.exec_command(message)
        elif cmd == "start":
            api.press_key_mult("esc", 2)
            api.press_key_mult("down", 4)
            api.press_key("enter")
            time.sleep(5)
            api.press_key("space")
            api.press_key("up")
            api.press_key_mult("down", 15, 0.01)
            api.press_key_mult("tab", 6)
            api.press_key("enter")
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
            api.press_key(config.get_bind("toggle scr_triggers_draw 0 1"))
        elif cmd == "clips":
            api.press_key(config.get_bind("toggle scr_clips_draw 0 1"))
        elif cmd == "snaps":
            api.press_key(config.get_bind("toggle scr_hud_snap_draw 0 1"))
        elif cmd == "cgaz":
            mode = args[0] if len(args) > 0 and 0 < int(args[0]) <= 15 else "toggle"
            if mode == "toggle":
                api.press_key(config.get_bind("toggle df_hud_cgaz 0 13"))
            else:
                api.exec_command(f"df_hud_cgaz {mode}")
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
        # elif cmd == "cv" and "kick" not in message:
        #     api.exec_command(f"{message}")
        elif cmd == "vote":
            api.press_key(config.get_bind(f"vote {args[0]}"))
        elif cmd == "help":
            help_message = "Client Controls (?command): [start (if on menu), connect <ip>, next <#>(opt), prev <#>(opt), scores, triggers," \
                           " clips, snaps, checkpoints, nodraw, angles, obs, clean, sky, vote <yes/no>, cgaz <1-15>(opt)]" \
                           " ||| Chat in DF: [> your message]" \
                           " ||| mDd Commands: [All commands available through mDd servers (!top, !rank, etc.)]"
            await ctx.channel.send(help_message)
        time.sleep(debounce)

    elif message.startswith(">"):  # chat bridge
        message = message.strip('>')
        if ";" in message:
            message = message[:message.index(";")]
        author_color_char = author[0]
        api.exec_command(f"say !me ^{author_color_char}{author}^7: ^2{message}")
        print("Chat message sent")
        time.sleep(debounce)

    elif message.startswith("!"):  # proxy mod commands (!top, !rank, etc.)
        print("proxy command received")
        if ";" in message:
            message = message[:message.index(";")]
        api.exec_command(message)
        time.sleep(debounce)
    return


if __name__ == "__main__":
    bot.run()
