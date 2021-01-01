"""This file contains all the handling logic for each twitchbot command available to DeFRaG players"""

import api
import requests
supported_commands = ["nospec", "info", "help", "howmany", "clear"]


def scan_for_command(message):
    """
    Scans a message content for a command
    :param message: The message content to scan
    :return: The command that has been called. None if no command found
    """
    for command in supported_commands:
        if message.startswith(f"?{command}"):
            return command
    return None


# The following are all the handler functions. They each take in line_data and return None

def handle_help(line_data):
    reply_string = "^7Current commands are ^3?^7nospec, ^3?^7info, ^3?^7help, ^3?^7clear, and ^3?^7howmany"
    api.exec_command(f"say {reply_string}")
    return None


def handle_nospec(line_data):
    api.exec_command(f"say ^7Don't want to be spectated? do ^3/color1 nospec^7, To allow spectating change it ^3/color1 specme")
    return None


def handle_info(line_data):
    reply_string_1 = "^7This is a ^324/7 ^7livestream: ^3https://defrag.tv ^7| Contact: ^3defragtv@gmail.com."
    reply_string_2 = "^7Use ^3?^7help for a list of commands"
    api.exec_command(f"say {reply_string_1}")
    api.exec_command(f"say {reply_string_2}")
    return None


def handle_howmany(line_data):
    client_id = "u8qaeps5664v7ddm7hgh42d9ynkanr"
    client_secret = "mp8m7yb3nsgq9c7j2ifwnfcufac4c4"
    token_url = f"https://id.twitch.tv/oauth2/token?client_id={client_id}&client_secret={client_secret}&grant_type=client_credentials"
    r = requests.post(token_url)
    token = r.json()['access_token']
    stream_url = f"https://api.twitch.tv/helix/streams?user_login={'defraglive'}"
    headers = {"Authorization": f"Bearer {token}", "Client-Id": client_id}
    r = requests.get(stream_url, headers=headers)
    stream_data = r.json()['data']
    viewer_count = stream_data[0]['viewer_count']
    reply_string = f"$chsinfo(117) ^2-- you are being watched by {viewer_count} viewer" + ("s" if viewer_count > 0 else "")
    api.exec_command(f"varcommand say {reply_string}")
    return None


def handle_clear(line_data):
   reply_string = "^7Ingame chat for viewers has been ^1erased."
   api.exec_command(f"clear; say {reply_string}")
   return None