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
import config
import threading
from termcolor import colored


SERVER = None
stop_state = threading.Event()


class Server:
    def __init__(self, ip, secret, server_info, players, bot_id):
        for key in server_info:
            setattr(self, key.lstrip('sv_'), server_info[key])
        self.players = players
        self.secret = secret
        self.bot_id = bot_id
        self.ip = ip
        self.current_player = None

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def update_info(self, server_info):
        for key in server_info:
            setattr(self, key.lstrip('sv_'), server_info[key])


class Player:
    def __init__(self, id, player_data):
        self.id = id
        for key in player_data:
            setattr(self, key, player_data[key])
        self.nospec = 'nospec' in player_data['dfn']


def connect(ip):
    global SERVER

    stop_state.set()
    time.sleep(1)
    # Set a secret model
    secret = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
    print(colored(f"Connecting to {ip}...", "green"))
    api.exec_command("connect " + ip, verbose=False)
    ts = time.time()
    console.wait_log(start_ts=ts, end_content="report written to")

    # Read report
    server_info, players = get_svinfo_report(config.INITIAL_REPORT_P)
    bot_player = [player for player in players if player.dfn == secret]

    # In case something goes wrong on the first rodeo
    while server_info is None or bot_player == []:
        api.exec_command(f"seta df_name {secret}", verbose=False)
        api.exec_command("svinfo_report initialstate.txt", verbose=False)
        server_info, players = get_svinfo_report(config.INITIAL_REPORT_P)
        bot_player = [player for player in players if player.dfn == secret]
        time.sleep(1)

    bot_id = bot_player[0].id  # Find our own ID
    # Create global server object
    SERVER = Server(ip, secret, server_info, players, bot_id)

    api.press_key(config.get_bind("+attack"))
    api.exec_command(f"seta df_name nospec", verbose=False)
    stop_state.clear()
    state_refresher = threading.Thread(target=refresh_server_state, args=(stop_state,), daemon=True)
    state_refresher.start()


def get_svinfo_report(filename):
    global SERVER

    with open(filename, "r") as svinfo_report_f:
        lines = svinfo_report_f.readlines()
        info = parse_svinfo_report(lines)

        # Parse into objects
        if bool(info):
            server_info = info["Server Info"]
            server_info['current_player'] = info['Info']['player']
        else:
            return None, None
        players = []

    for header in info:
        try:
            match = re.match(r"^Client Info (\d+?)$", header)
            id = match.group(1)
            player_data = info[header]
            players.append(Player(id, player_data))
        except:
            continue
    return server_info, players


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


def initialize_serverstate(sv_log_path):
    api.exec_command("varcommand $get_state")
    while True:
        with open(sv_log_path, "r") as test_f:
            lines = test_f.readlines()
            print(parse_svinfo_report(lines))
        time.sleep(2)


def refresh_server_state(stop_state):
    global SERVER
    prev_state = ""
    while not stop_state.is_set():
        time.sleep(1)
        api.exec_command("silent svinfo_report serverstate.txt", verbose=False)
        server_info, players = get_svinfo_report(config.STATE_REPORT_P)

        if bool(server_info):
            SERVER.players = players
            SERVER.update_info(server_info)
            curr_state = f"Spectating {SERVER.current_player} on {SERVER.mapname} in server {SERVER.hostname} | ip: {SERVER.ip}"
            if curr_state != prev_state:
                print(colored(curr_state, "blue"))
            switch_if_nospec()
            prev_state = curr_state


def switch_if_nospec():
    global SERVER
    spec_dfn = SERVER.current_player
    if "nospec" in spec_dfn:
        print(colored(f"Skipping no-specced player", "red"))
        api.press_key(config.get_bind("+attack"))