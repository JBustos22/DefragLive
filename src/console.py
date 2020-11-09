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

import api
import config

LOG = []
LOG_PARSED = []
CONSOLE_DISPLAY = []


def read(file_path: str):
    """
    Reads the console log file every second and sends the console lines for processing
    :param file_path: Full file path to the qconsole.log file
    :return: None
    """

    global LOG
    global LOG_PARSED
    global CONSOLE_DISPLAY

    while not os.path.isfile(file_path):
        time.sleep(1)

    with open(file_path, 'r') as log:
        while 1:
            where = log.tell()
            line = log.readline()
            if not line:
                time.sleep(1)
                log.seek(where)
            else:
                LOG.append(line)
            if "serverCommand" in line:
                line_data = process_line(line)

                LOG_PARSED.append(line_data)

                if line_data.pop("command") is not None:
                    command = line_data["command"]
                    handle_command = getattr(cmd, f"handle_{command}")
                    handle_command(line_data)

                if line_data["type"] in ["PRINT", "SAY"]:
                    CONSOLE_DISPLAY.append(line_data)


def process_line(line):
    """
    Processes a console line into a more useful format. Extracts type (say, announcement, print) as well as author
    and content if applicable.
    :param line: Console line to be processed
    :return: Data dictionary containing useful data about the line
    """
    line = line.strip()

    line_data = {"type": "MISC", "command": None, "author": None, "content": line, "timestamp" : time.time()}

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

        def parse_scores(command):
            # SCORES
            scores_r = r"^scores\s+(.*?)$"
            match = re.match(scores_r, command)

            scores = match.group(1)

            line_data["type"] = "SCORES"
            line_data["author"] = None
            line_data["content"] = scores

        for fun in [parse_chat_message, parse_chat_announce, parse_print, parse_scores]:
            try:
                fun(sv_command)
                break
            except:
                continue
    except:
        return line_data

    #print(colored(line_data, "yellow"))
    return line_data


def wait_for_log_parsed(start_ts=0, end_type=None, end_author=None, end_content=None, end_content_fuzzy=True, delay=0.5):
    global LOG_PARSED

    length = len(LOG_PARSED)

    def check(line, end_type, end_author, end_content, end_content_fuzzy):
        if end_type and end_type != line["type"]:
            return False

        if end_author and end_author != line["author"]:
            return False

        if end_content:
            if end_content_fuzzy:
                end_content = "^.*?" + end_content + ".*?$"

            try:
                re.match(end_content, line["content"])
            except:
                return False

        return True

    # Slice log, check lines, etc
    # Check initial slice
    slice = [line for line in LOG_PARSED if line["timestamp"] > start_ts]

    for line in slice:
        if check(line, end_type, end_author, end_content, end_content_fuzzy):
            return line

    while True:
        length_new = len(LOG_PARSED)

        if length_new == length:
            time.sleep(delay)
            continue

        slice = LOG_PARSED[length : length_new]

        for line in slice:
            if check(line, end_type, end_author, end_content, end_content_fuzzy):
                return line


def wait_for_log(start_r="", start_fuzzy=True, end_r="", end_fuzzy=True, delay=0.5):
    """
    Waits for a certain message to be logged
    :param start_r: The message regex that defines the start of the waiting period
    :param start_fuzzy: Whether or not the start regex describes the entire line, or just part of a line
    :param end_r: The message regex that defines the end of the waiting period
    :param end_fuzzy: Whether or not the end regex describes the entire line, or just part of a line
    :param delay: How long to wait inbetween checking for the end message
    :return: The first line to match end_r
    """

    global LOG

    print("WAIT", start_r if start_r != "" else "*", end_r if end_r != "" else "*")

    length = len(LOG)

    if end_fuzzy:
        end_r = "^.*" + end_r + ".*$"

    if start_r != "":
        if start_fuzzy:
            start_r = "^.*" + start_r + ".*$"

        # Check if there is already a slice to investigate
        # Iterate back-to-front over LOG until we find start_r
        # Then, check all latter elements in LOG if any exist
        for i in range(length - 1, -1, -1):
            if re.match(start_r, LOG[i]) and i < length - 1:
                # There is an initial slice to check
                extract = [line for line in LOG[i + 1 : ] if re.match(end_r, line)]

                if len(extract) > 0:
                    # The initial slice contains end_r
                    return extract[0]

                # We have found the latest occurance of start_r, stop searching
                break

    # Loop and check for new slices, then check those when they become available
    while True:
        length_new = len(LOG)

        if length_new > length:
            # A new slice has appeared
            slice = LOG[length : length_new]
            length = length_new

            extract = [line for line in slice if re.match(end_r, line)]

            if len(extract) > 0:
                return extract[0]

        time.sleep(delay)


def info_players():
    api.press_key(config.get_bind_fuzzy("info players"))
    wait_for_log(end_r="^[0-9:]*[\s]*Dumped console text to .*$", end_fuzzy=False)

    with open(config.DUMP_P, "r") as dump_f:
        lines = dump_f.readlines()

    separator_r = r"^[0-9:]*[\s]*-+$"
    separators = [x for x in range(len(lines)) if re.match(separator_r, lines[x])]

    data = lines[separators[-2] + 1 : separators[-1]]

    players = []

    for line in data:
        parse_r = r"^[0-9:]*\s*(\d+)\s+\|\s+(.+?)\s+(.*)$"

        try:
            match = re.match(parse_r, line)

            player_id = match.group(1)
            player_team = match.group(2)
            player_name = match.group(3)

            players.append({"id" : player_id, "team" : player_team, "name" : player_name})
        except:
            # Probably some other line mixed in
            continue

    print(players)

    return players


def server_status():
    api.press_key(config.get_bind_fuzzy("serverstatus"))
    wait_for_log(end_r="^[0-9:]*[\s]*Dumped console text to .*$", end_fuzzy=False)

    with open(config.DUMP_P, "r") as dump_f:
        lines = dump_f.readlines()

    start1_r = "^[0-9:]*\s*Server settings:$"
    start1 = [x for x in range(len(lines)) if re.match(start1_r, lines[x])][0] + 1

    start2_r = "^[0-9:]*\s*Players:$"
    start2 = [x for x in range(len(lines)) if re.match(start2_r, lines[x])][0] + 1

    end_r = "^[0-9:]*\s*Dumped console text to .*$"
    end = [x for x in range(len(lines)) if re.match(end_r, lines[x])][0]

    server_settings_data = lines[start1 : start2 - 1]
    parse_r = "^[0-9:]*\s*([^\s]+)\s+([^\s]+)$"

    server_settings = {}

    for line in server_settings_data:
        try:
            match = re.match(parse_r, line)

            key = match.group(1)
            value = match.group(2)

            server_settings[key] = value
        except:
            # Probably some other line mixed in
            pass

    players_data = lines[start2 + 1 : end] # Skip table header
    parse_r = "^[0-9:]*\s*(\d+)\s*(\d+)\s*(\d+)\s*\"(.+)\"$"

    players = []

    for line in players_data:
        try:
            match = re.match(parse_r, line)

            num = match.group(1)
            score = match.group(2)
            ping = match.group(3)
            name = match.group(4)

            player = {"num" : num, "score" : score, "ping" : ping, "name" : name}

            players.append(player)
        except:
            pass

    print(server_settings, players)

    return (server_settings, players)
