"""This file contains all the handling logic for each twitchbot command available to DeFRaG players"""

import api
supported_commands = ["nospec", "info", "help", "howmany"]


def scan_for_command(message):
    """
    Scans a message content for a command
    :param message: The message content to scan
    :return: The command that has been called. None if no command found
    """
    for command in supported_commands:
        if message.startswith(f"^2?{command}"):
            return command
    return None


"""
The following are all the handler functions. They each take in line_data and return None
"""


def handle_help(line_data):
    reply_string = "Current commands are ?nospec, ?info, and ?help, and ?howmany"
    api.exec_command(f"say {reply_string}")
    return None


def handle_nospec(line_data):
    # le extreme logic
    api.exec_command(f"Coming soon.")
    return None


def handle_info(line_data):
    reply_string = "This is a 24/7 livestream: https://www.twitch.tv/defraglive. Contact: defragtv@gmail.com. " \
                  "Use ?help for all the available commands"
    api.exec_command(f"say {reply_string}")
    return None


def handle_howmany(line_data):
    viewer_count = 5
    reply_string = f"Your are being watched by {viewer_count} viewer" + ("s" if viewer_count > 0 else "")
    api.exec_command(f"say {reply_string}")
    return None