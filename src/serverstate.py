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
    def __init__(self, ip, secret, info, players):
        self.info = info
        self.players = players
        self.secret = secret
        self.bot_id = [player for player in players if player["model"] == secret][0]["id"]
        self.ip = ip

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)


def connect(ip):
    global SERVER

    secret = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
    api.exec_command("seta model " + secret)

    api.exec_command("model")
    api.press_key(config.get_bind("+scores;-scores"))

    api.exec_command("connect " + ip)

    while not os.path.isfile(config.SVINFO_REPORT_P):
        time.sleep(1)

    with open(config.SVINFO_REPORT_P, "r") as svinfo_report_f:
        lines = svinfo_report_f.readlines()
        info = parse_svinfo_report(lines)

    api.exec_command("model ranger/default")

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

    os.remove(config.SVINFO_REPORT_P)

    SERVER = Server(ip, secret, server_info, players)


def get_spec_id():
    global SERVER

    players = get_scores()

    bot_player = [player for player in players if player["id"] == SERVER.bot_id][0]

    return bot_player["spec_id"]


def get_scores():
    ts = time.time()

    api.press_key(config.get_bind_fuzzy("+scores;-scores"))

    line = console.wait_for_log_parsed(start_ts=ts, end_type="SCORES")

    # Parse scores
    nums = line["content"].split(" ")
    num_players = int(nums[0])
    nums = nums[4:]

    players = []

    for i in range(0, num_players * 4, 4):
        id = nums[i]
        score = nums[i+1]
        ping = nums[i+2]
        spec_id = nums[i+3]

        players.append({"id" : id, "score" : score, "ping" : ping, "spec_id" : spec_id})

    return players


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
