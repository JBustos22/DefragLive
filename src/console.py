"""
This file has the following purposes:
1. Reads the console in real time.
2. Listens for commands and starts the proper pipeline when a command is activated.
3. Formats chat, server prints, and server notifications nicely for the twitch extension.
"""


import os
import time
from termcolor import colored
import dfcommands as cmd
import traceback
import re


def read(file_path: str):
    """
    Reads the console log file every second and sends the console lines for processing
    :param file_path: Full file path to the qconsole.log file
    :return: None
    """

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
                if line_data["command"] is not None:
                    command = line_data["command"]
                    handle_command = getattr(cmd, f"handle_{command}")
                    handle_command(line_data)


def process_line(line):
    """
    Processes a console line into a more useful format. Extracts type (say, announcement, print) as well as author
    and content if applicable.
    :param line: Console line to be processed
    :return: Data dictionary containing useful data about the line
    """
    line = line.strip()

    line_data = {"type": "MISC", "command": None, "author": None, "content": line}

    # SERVERCOMMAND
    try:
        sc_r = r"^\^5serverCommand:\s*(\d+?)\s*:\s*(.+?)$"
        match = re.match(sc_r, line)

        sv_command_id = match.group(1)
        sv_command = match.group(2)

        def parse_chat_message(command):
            # CHAT MESSAGE (BY PLAYER)
            chat_message_r = r"^chat\s*\"[\x19]*\[*(.*?)[\x19]*?\]*?\x19:\s*(.*?)\".*?$"
            match = re.match(chat_message_r, command)

            chat_name = match.group(1)
            chat_message = match.group(2)

            line_data["type"] = "SAY"
            line_data["author"] = chat_name
            line_data["content"] = chat_message
            line_data["command"] = cmd.scan_for_command(chat_message)

        def parse_chat_announce(command):
            # CHAT ANNOUNCEMENT
            chat_announce_r = r"^chat\s*\"(.*?)\".*?$"
            match = re.match(chat_announce_r, command)

            chat_announcement = match.group(1)

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
                fun(sv_command)
                break
            except:
                continue
    except:
        return line_data

    print(colored(line_data, "yellow"))
    return line_data
