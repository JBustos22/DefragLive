"""
This file contains two important classes that keep the current state of the game:
Server - stores information about the current server, such meta data and players. It contains a set of methods to
         conveniently query information that is expected to be needed frequently.
Player - stores individual in-depth information about each player. The server object's players attribute contains a
         list of these objects. Contains a set of methods that make player operations convenient.
"""

import api
import re
import time
import random
import config
import threading
from termcolor import colored
import os
import servers


SERVER = None
STOP_STATE = threading.Event()


class Server:
    def __init__(self, ip, secret, server_info, players, bot_id):
        for key in server_info:
            setattr(self, key.replace('sv_', ''), server_info[key])
        self.players = players
        self.secret = secret
        self.bot_id = bot_id
        self.spec_ids.remove(self.bot_id)
        self.ip = ip
        self.current_player = None
        self.current_player_id = -1
        self.idle_counter = 0
        self.curr_state = None
        self.prev_state = None

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def update_info(self, server_info):
        for key in server_info:
            setattr(self, key.replace('sv_', ''), server_info[key])
        self.current_player = self.get_player_by_id(self.current_player_id)
        if self.bot_id in self.spec_ids:
            self.spec_ids.remove(self.bot_id)

    def get_player_by_id(self, c_id):
        id_player = [player for player in self.players if player.id == c_id]
        id_player = id_player[0] if len(id_player) > 0 else None
        return id_player


class Player:
    def __init__(self, id, player_data):
        self.id = id
        for key in player_data:
            setattr(self, key, player_data[key])
        self.nospec = self.c1 == 'nospec'


def get_svinfo_report(filename):
    global SERVER

    with open(filename, "r") as svinfo_report_f:
        lines = svinfo_report_f.readlines()
        info = parse_svinfo_report(lines)

        # Parse into objects
        if "Server Info" in info:
            server_info = info["Server Info"]
            server_info['physics'] = info['Info']['physics']
            server_info['curr_dfn'] = info['Info']['player']
        else:
            time.sleep(5)
            return None, None
        players, spec_ids = [], []

    for header in info:
        try:
            match = re.match(r"^Client Info (\d+?)$", header)
            cli_id = match.group(1)
            player_data = info[header]
            if player_data['c1'] != 'nospec':
                players.append(Player(cli_id, player_data))
                if player_data['t'] == '0':
                    spec_ids.append(cli_id)
        except:
            continue
    server_info['spec_ids'] = spec_ids
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


def refresh_server_state():
    global SERVER
    global STOP_STATE

    while not STOP_STATE.is_set():
        time.sleep(1)
        api.exec_command("silent svinfo_report serverstate.txt", verbose=False)
        server_info, players = get_svinfo_report(config.STATE_REPORT_P)

        if bool(server_info):
            SERVER.players = players
            SERVER.update_info(server_info)
            if SERVER.current_player is not None:
                SERVER.curr_state = f"Spectating {SERVER.current_player.n} on {SERVER.mapname} in server {SERVER.hostname} | ip: {SERVER.ip}"
            if SERVER.curr_state != SERVER.prev_state:
                print(colored(SERVER.curr_state, "blue"))
            continue_refresh = check_status()
            SERVER.prev_state = SERVER.curr_state
            display_player_name(SERVER.current_player_id)
            if not continue_refresh:
                return


def restart_connect(ip):
    api.press_key_mult("{Esc}", 2)
    api.press_key("{Enter}")
    api.press_key_mult("{Tab}", 10)
    api.press_key("{Enter}")
    time.sleep(1)
    api.exec_command("connect " + ip, verbose=False)


def connect(ip):
    global SERVER
    global STOP_STATE

    if ip.split(':')[0] not in config.IP_WHITELIST:
        print(f"Server {ip} is not whitelisted. Refusing.")
        return

    STOP_STATE.set()  # stop server refresh thread
    # Set a secret color cvar
    secret = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
    print(colored(f"Connecting to {ip}...", "green"))
    connection_time = time.time()
    api.exec_command("connect " + ip, verbose=False)
    api.exec_command(f"seta color1 {secret}", verbose=False)
    server_info, bot_player, timeout_flag, reconnect_tries = None, [], 0, 0

    # Read report
    while server_info is None or bot_player == []:
        report_mod_time = os.path.getmtime(config.INITIAL_REPORT_P)
        new_report_exists = report_mod_time > connection_time

        if new_report_exists:
            server_info, players = get_svinfo_report(config.INITIAL_REPORT_P)
            bot_player = [player for player in players if player.c1 == secret]

        timeout_flag += 1
        if timeout_flag >= 10:
            print(colored(f"Connection timed out.", "green"))
            if reconnect_tries < 2:
                print(colored(f"Retrying connection to {ip}...", "green"))
                connection_time = time.time()
                restart_connect(ip)
                api.exec_command(f"seta color1 {secret}", verbose=False)
                server_info, bot_player, timeout_flag = None, [], 0
                reconnect_tries += 1
            else:
                print(f"Could not connect to {ip}")
                return

        time.sleep(1)

    print(colored(f"Connected.", "green"))
    bot_id = bot_player[0].id  # Find our own ID

    # Create global server object
    SERVER = Server(ip, secret, server_info, players, bot_id)
    SERVER.current_player_id = -1

    check_status()
    STOP_STATE.clear()
    state_refresher = threading.Thread(target=refresh_server_state, daemon=True)
    state_refresher.start()
    return True


def switch_spec(direction='next'):
    global SERVER
    global STOP_STATE

    spec_ids = SERVER.spec_ids if direction == 'next' else SERVER.spec_ids[::-1]

    if SERVER.current_player_id != -1:
        next_id_index = spec_ids.index(SERVER.current_player_id) + 1
        if next_id_index > len(spec_ids) - 1:
            next_id_index = 0
        follow_id = spec_ids[next_id_index]

        if follow_id == SERVER.current_player_id:
            print("No other players to switch to.")
            api.exec_command("displaymessage 380 10 ^1No other players to switch to.", verbose=False)
        else:
            display_player_name(follow_id)
            api.exec_command(f"follow {follow_id}")
            SERVER.idle_counter = 0
            SERVER.current_player_id = follow_id


def check_status():
    global SERVER
    global STOP_STATE

    MAX_STRIKES = 10  # TODO: move this over to configurable setting by user
    continue_refresh = True
    spectating_self = SERVER.curr_dfn == 'twitchbot'
    spectating_nospec = SERVER.current_player_id not in SERVER.spec_ids

    if spectating_self or spectating_nospec:
        follow_id = random.choice(SERVER.spec_ids) if SERVER.spec_ids != [] else -1

        if follow_id != -1:
            msg = "Spectating self, switching..." if spectating_self else "Switching to non-nospec player..."
            print(colored(msg, 'green'))
            display_player_name(follow_id)
            api.exec_command(f"follow {follow_id}")
            SERVER.idle_counter = 0
        else:
            if SERVER.current_player_id != -1:
                api.exec_command(f"follow {follow_id}", verbose=False)
                SERVER.current_player_id = -1

            SERVER.idle_counter += 1
            print(f"Not spectating. Strike {SERVER.idle_counter}/{MAX_STRIKES}")

            if SERVER.idle_counter >= MAX_STRIKES:  # There's been no one on the server to spec, switch servers.
                new_ip = servers.get_most_popular_server(ignore_ip=SERVER.ip)
                STOP_STATE.set()
                connection_success = connect(new_ip)
                return connection_success  # if false, continue working as normal. Else, stop refresh.
        SERVER.current_player_id = follow_id

    return continue_refresh


def display_player_name(follow_id):
    follow_player = SERVER.get_player_by_id(follow_id)
    if follow_player is not None:
        player_name = follow_player.n
        display_name = player_name if player_name.strip() not in config.BLACKLISTED_WORDS else "*" * len(player_name)
        api.exec_command(f"set player-name {display_name}", verbose=False)