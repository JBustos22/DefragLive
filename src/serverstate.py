"""
This file contains two important classes that keep the current state of the game:
Server - stores information about the current server, such meta data and players. It contains a set of methods to
         conveniently query information that is expected to be needed frequently.
Player - stores individual in-depth information about each player. The server object's players attribute contains a
         list of these objects. Contains a set of methods that make player operations convenient.
"""

import console
import api
import re
import time
import random
import os
import config

SERVER = None


class Server:
    def __init__(self, ip, secret, info, players, bot_id):
        self.info = info
        self.players = players
        self.secret = secret
        self.bot_id = bot_id
        self.ip = ip

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


def connect(ip):
    global SERVER

    # Set a secret model
    secret = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
    api.exec_command("seta model " + secret)

    # Make sure the model is set, I hate this
    api.exec_command("model")
    api.press_key(config.get_bind("+scores;-scores"))

    # Keep track of time for proper log parsing
    ts = time.time()

    # Connect to the server, respawn.cfg will write a svinfo_report that we have to wait for
    api.exec_command("connect " + ip)

    console.wait_log(start_ts=ts, end_content="report written to")

    # Read report
    with open(config.SVINFO_REPORT_P, "r") as svinfo_report_f:
        lines = svinfo_report_f.readlines()
        info = parse_svinfo_report(lines)

    # Reset model to something sensible
    api.exec_command("model ranger/default")

    # Parse svinfo_report into objects
    server_info = info["Server Info"] if "Server Info" in info else []
    players = []

    for header in info:
        try:
            match = re.match(r"^Client Info (\d+?)$", header)
            id = match.group(1)

            player_obj = info[header]
            player_obj["id"] = id

            players.append(player_obj)
        except:
            continue

    print(server_info)
    print(players)
    print(secret)

    # Find our own ID
    bot_id = [player for player in players if player["model"] == secret][0]["id"]

    # Create global server object
    SERVER = Server(ip, secret, server_info, players, bot_id)


def switch_spec(fwd=True):
    global SERVER

    for _ in range(len(SERVER.players)):
        if fwd:
            api.press_key(config.get_bind("+attack"))
        else:
            api.press_key(config.get_bind("+speed;wait 10;-speed"))

        time.sleep(0.2)

        info = get_svinfo_report()

        spec_dfn = info["Info"]["player"]

        if "nospec" in spec_dfn or "ns" in spec_dfn:
            print("SKIPPING PLAYER", spec_dfn)
            continue
        else:
            return

    # Reset
    api.exec_command("team spectator")




def get_spec_id():
    global SERVER

    players = get_scores()

    bot_player = [player for player in players if player["id"] == SERVER.bot_id][0]

    return bot_player["spec_id"]


def get_scores():
    ts = time.time()

    # This has an internal debounce :) Holy fucking shit
    api.press_key(config.get_bind_fuzzy("+scores;-scores"))

    line = console.wait_log(start_ts=ts, end_type="SCORES")

    return parse_scores(line)


def parse_scores(line):
    parts = line.split(" ")
    num_players = int(parts[0])

    players = []

    # Work backwards since the embedded string can contain spaces
    for i in range(0, num_players * 4, 4):
        spec_id = parts[i-1]
        ping = parts[i-2]
        score = parts[i-3]
        id = parts[i-4]

        players.append({"id" : id, "score" : score, "ping" : ping, "spec_id" : spec_id})

    return players


def get_svinfo_report():
    global SERVER

    ts = time.time()
    api.press_key(config.get_bind_fuzzy("svinfo_report serverstate.txt"))
    console.wait_log(start_ts=ts, end_content="report written to")

    with open(config.SVINFO_REPORT_P, "r") as svinfo_report_f:
        lines = svinfo_report_f.readlines()
        info = parse_svinfo_report(lines)

        # Parse into objects
        server_info = info["Server Info"] if "Server Info" in info else []
        players = []

    for header in info:
        try:
            match = re.match(r"^Client Info (\d+?)$", header)
            id = match.group(1)

            player_obj = info[header]
            player_obj["id"] = id

            players.append(player_obj)
        except:
            continue

    SERVER.server_info = server_info
    SERVER.players = players

    return info


def parse_svinfo_report(lines):
    info = {}
    header = None

    header_r = r"^\*\*\* (.*)$"
    kv_r = r"^(.+?)\s+(.*)$"

    for line in [line for line in lines if line != ""]:
        # Check if line is a header
        try:
            header = re.match(header_r, line).group(1)

            # Create new dictionary for header
            if header not in info:
                info[header] = {}

            continue
        except:
            pass

        # Don't parse any lines until we have a header
        if not header:
            continue

        # Check if line is a key-value pair
        try:
            match = re.match(kv_r, line)
            key = match.group(1)
            value = match.group(2)

            info[header][key] = value
        except:
            pass

    return info
