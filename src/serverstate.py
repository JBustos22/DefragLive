"""
This file contains two important classes that keep the current state of the game:
State - stores information about the current server, such meta data and players. It contains a set of methods to
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


STATE = None
STOP_STATE = threading.Event()
ALREADY_CONNECTING = False


class State:
    def __init__(self, secret, server_info, players, bot_id):
        for key in server_info:
            setattr(self, key.replace('sv_', ''), server_info[key])
        self.players = players
        self.secret = secret
        self.bot_id = bot_id
        self.current_player = None
        self.current_player_id = -1
        self.idle_counter = 0
        if self.bot_id in self.spec_ids:
            self.spec_ids.remove(self.bot_id)

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


def start():
    global STATE

    prev_state, curr_state = None, None
    initialize_state()
    init_time = time.time()

    while True:
        time.sleep(1)
        if new_report_exists(config.INITIAL_REPORT_P, init_time):
            print("New connection detected. Re-initializing state...")
            initialize_state()
            init_time = time.time()
            prev_state, curr_state = None, None
        else:
            pre_time = time.time()
            api.exec_command("silent svinfo_report serverstate.txt", verbose=False)

            if new_report_exists(config.STATE_REPORT_P, pre_time):
                server_info, players = get_svinfo_report(config.STATE_REPORT_P)
                if bool(server_info):
                    STATE.players = players
                    STATE.update_info(server_info)
                    validate_state()
                    if STATE.current_player is not None:
                        curr_state = f"Spectating {STATE.current_player.n} on {STATE.mapname} in server {STATE.hostname} | ip: {STATE.ip}"
                    if curr_state != prev_state:
                        print(colored(curr_state, "blue"))
                    prev_state = curr_state
                    display_player_name(STATE.current_player_id)
            else:
                time.sleep(5)  # Either map is loading or console is open, wait a little bit to avoid crashes


def initialize_state():
    global STATE

    try:
        # Set a secret color cvar
        secret = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        server_info, bot_player, timeout_flag, reconnect_tries = None, [], 0, 1

        while server_info is None or bot_player == []:
            init_time = time.time()
            api.exec_command(f"seta color1 {secret};silent svinfo_report serverstate.txt", verbose=False)
            if new_report_exists(config.STATE_REPORT_P, init_time):
                server_info, players = get_svinfo_report(config.STATE_REPORT_P)  # Read report
                bot_player = [player for player in players if player.c1 == secret]
            else:
                time.sleep(5)  # In menu, connecting, or other.

        bot_id = bot_player[0].id  # Find our own ID

        # Create global server object
        STATE = State(secret, server_info, players, bot_id)
        STATE.current_player_id = bot_id
        print("State Initialized.")
    except:
        return False

    return True


def validate_state():
    global STATE
    global STOP_STATE

    MAX_STRIKES = 10  # TODO: move this over to configurable setting by user
    continue_refresh = True
    spectating_self = STATE.curr_dfn == 'twitchbot' or STATE.current_player_id == STATE.bot_id
    spectating_nospec = STATE.current_player_id not in STATE.spec_ids and STATE.current_player_id != STATE.bot_id

    if spectating_self or spectating_nospec:
        follow_id = random.choice(STATE.spec_ids) if STATE.spec_ids != [] else -1

        if follow_id != -1:
            if spectating_nospec:
                print(colored('Nospec detected. Switching...', 'green'))
            display_player_name(follow_id)
            api.exec_command(f"follow {follow_id}", verbose=False)
            STATE.idle_counter = 0
        else:
            if STATE.current_player_id != -1:
                api.exec_command(f"follow {follow_id}", verbose=False)
                STATE.current_player_id = -1

            STATE.idle_counter += 1
            print(f"Not spectating. Strike {STATE.idle_counter}/{MAX_STRIKES}")

            if STATE.idle_counter >= MAX_STRIKES:  # There's been no one on the server to spec, switch servers.
                new_ip = servers.get_most_popular_server(ignore_ip=STATE.ip)
                connection_success = connect(new_ip)
                return not connection_success  # if false, continue working as normal. Else, stop refresh.
        STATE.current_player_id = follow_id
        STATE.current_player = STATE.get_player_by_id(follow_id)

    return continue_refresh


def connect(ip):
    if ip.split(':')[0] not in config.IP_WHITELIST:
        print(f"Server \"{ip}\" is not whitelisted. Refusing connection.")
        return

    connection_time = time.time()
    print(f"Connecting to {ip}...")
    api.exec_command("connect " + ip, verbose=False)
    time.sleep(5)

    max_attempts = 2
    attempt = 1
    while not new_report_exists(config.INITIAL_REPORT_P, connection_time) and attempt <= max_attempts:
        print(f"Retrying connection... (Attempt {attempt}/{max_attempts})")
        restart_connect(ip)
        time.sleep(5 * attempt)
        attempt += 1


def restart_connect(ip):
    api.press_key_mult("{Esc}", 2, verbose=False)
    api.press_key("{Enter}", verbose=False)
    api.press_key_mult("{Tab}", 10, verbose=False)
    api.press_key("{Enter}", verbose=False)
    time.sleep(1)
    api.exec_command("connect " + ip, verbose=False)


def new_report_exists(path, time_pov):
    report_mod_time = os.path.getmtime(path)
    return report_mod_time > time_pov


def switch_spec(direction='next'):
    global STATE
    global STOP_STATE

    spec_ids = STATE.spec_ids if direction == 'next' else STATE.spec_ids[::-1]

    if STATE.current_player_id != -1:
        next_id_index = spec_ids.index(STATE.current_player_id) + 1
        if next_id_index > len(spec_ids) - 1:
            next_id_index = 0
        follow_id = spec_ids[next_id_index]

        if follow_id == STATE.current_player_id:
            print("No other players to switch to.")
            api.exec_command("displaymessage 380 10 ^1No other players to switch to.", verbose=False)
        else:
            display_player_name(follow_id)
            api.exec_command(f"follow {follow_id}", verbose=False)
            STATE.idle_counter = 0
            STATE.current_player_id = follow_id


def display_player_name(follow_id):
    follow_player = STATE.get_player_by_id(follow_id)
    if follow_player is not None:
        player_name = follow_player.n
        display_name = player_name if player_name.strip() not in config.BLACKLISTED_WORDS else "*" * len(player_name)
        api.exec_command(f"set player-name {display_name}", verbose=False)


def get_svinfo_report(filename):
    global STATE

    with open(filename, "r") as svinfo_report_f:
        lines = svinfo_report_f.readlines()
        info, ip = parse_svinfo_report(lines)

        # Parse into objects
        if "Server Info" in info:
            server_info = info["Server Info"]
            server_info['physics'] = info['Info']['physics']
            server_info['curr_dfn'] = info['Info']['player']
            server_info['ip'] = ip
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

    title_r = r"= Report for (.*) \(*."
    header_r = r"^\*\*\* (.*)$"
    kv_r = r"^(.+?)\s+(.*)$"

    ip = None
    for line in [line for line in lines if line != ""]:

        # Check for ip
        if ip is None:
            try:
                ip = re.match(title_r, line).group(1)
            except:
                pass

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

    return info, ip