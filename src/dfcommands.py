"""This file contains all the handling logic for each twitchbot command available to DeFRaG players"""

import api
supported_commands = ["nospec", "info", "help", "viewers", "clear"]


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
    reply_string = "^7Current commands are ^3?^7nospec, ^3?^7info, ^3?^7help, ^3?^7clear, and ^3?^7viewers"
    api.exec_command(f"say {reply_string}")
    return None


def handle_nospec(line_data):
    api.exec_command(f"say ^7Don't want to be spectated? do ^3/color1 nospec^7, To allow spectating change it ^3/color1 specme")
    return None


def handle_info(line_data):
    reply_string = "^7This is a ^324/7 ^7livestream: ^3https://defrag.tv ^7| Contact: ^3defragtv@gmail.com. " \
                  "^7| Use ^3?^7help for a list of commands"
    api.exec_command(f"say {reply_string}")
    return None


def handle_viewers(line_data):
    import serverstate
    viewer_count = 5
    reply_string = f"^1{serverstate.STATE.current_player.n}^7, you are being watched by ^3{viewer_count} ^7viewer" + ("s" if viewer_count > 0 else "")
    api.exec_command(f"say {reply_string}")
    return None


def handle_clear(line_data):
   reply_string = "^7Ingame chat for viewers on stream has been ^1erased."
   api.exec_command(f"clear; say {reply_string}")
   return None