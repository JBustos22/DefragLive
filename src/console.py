import os
import time
import api as api
from termcolor import colored
import commands
import traceback
import re


def read(file_path, verbose=True):
    while not os.path.isfile(file_path):
        time.sleep(1)

    with open(file_path, 'r') as log:
        while 1:
            where = log.tell()
            line = log.readline()
            if not line:
                time.sleep(1)
                log.seek(where)
            elif "serverCommand" in line:
                line_data = process_line(line)

                if line_data["type"] == "SAY":
                    process_command(line_data, line_data["content"])



def process_line(line):
    line = line.strip()

    line_data = {"type" : "MISC", "command" : None, "author" : None, "content" : line}

    # SERVERCOMMAND
    try:
        sc_r = r"^\^5serverCommand:\s*(\d+?)\s*:\s*(.+?)$"
        match = re.match(sc_r, line)

        command_id = match.group(1)
        command = match.group(2)

        line_data["command"] = command

        def parse_chat_message(command):
            # CHAT MESSAGE (BY PLAYER)
            chat_message_r = r"^chat\s*\"[\x19]*\[*(.*?)[\x19]*?\]*?\x19:\s*(.*?)\".*?$"
            match = re.match(chat_message_r, command)

            chat_name = match.group(1)
            chat_message = match.group(2)

            line_data["type"] = "SAY"
            line_data["author"] = chat_name
            line_data["content"] = chat_message

        def parse_chat_announce(command):
            # CHAT ANNOUNCEMENT
            chat_announce_r = r"^chat\s*\"(.*?)\".*?$"
            match = re.match(chat_announce_r, command)

            chat_announcement = chat_announce_r.group(1)

            line_data["type"] = "ANNOUNCE"
            line_data["author"] = None
            line_data["content"] = chat_announcement

        def parse_print(command):
            # PRINT
            print_r = r"^print\s*\"(.*?)$" # Prints have their ending quotation mark on the next line, very strange
            match = re.match(print_r, command)

            print_message = match.group(1)

            line_data["type"] = "PRINT"
            line_data["author"] = None
            line_data["content"] = print_message

        for fun in [parse_chat_message, parse_chat_announce, parse_print]:
            try:
                fun(command)
                break
            except:
                continue
    except:
        return line_data

    print(line_data)
    return line_data


def process_command(line_data, message):
    # TODO: Should find a way not to have a bunch of if statements
    # TODO: Use command functions from command.py to process for each situation

    # Proof of concept code:
    # TODO: Change conditionals to use command param, etc.
    if "?nospec" in message: # switch this to a RE match
        # no spec logic or function with logic here
        api.exec_command(f"say Nospec command received.")
    elif "?info" in message:
        info_string = "This is a 24/7 livestream: https://www.twitch.tv/defraglive. Contact: defragtv@gmail.com. " \
                      "Use ?help for all the available commands"
        api.exec_command(f"say {info_string}")
    elif "?help" in message:
        help_string = "Current commands are ?nospec, ?info, and ?help"
        api.exec_command(f"say {help_string}")
