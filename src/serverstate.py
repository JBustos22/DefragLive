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
PAUSE_STATE = False
MESSAGE_REPEATS = 0 # How many times to spam info messages. 0 for none
AFK_TIMEOUT = 30  # switch after afk detected x consecutive times
IDLE_TIMEOUT = 10  # alone in server


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
        self.afk_counter = 0
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

    def get_inputs(self):
        bot_player = self.get_player_by_id(self.bot_id)
        return bot_player.c2.replace(' ', '')


class Player:
    def __init__(self, id, player_data):
        self.id = id
        for key in player_data:
            setattr(self, key, player_data[key])
        self.nospec = self.c1 == 'nospec'


def start():
    global STATE
    global PAUSE_STATE

    while True:
        try:
            if PAUSE_STATE:
                raise Exception("Paused.")

            prev_state, curr_state = None, None
            initialize_state()
            init_time = time.time()

            while not new_report_exists(config.INITIAL_REPORT_P, init_time) and not PAUSE_STATE:
                time.sleep(1)
                pre_time = time.time()
                api.exec_state_command(f'varmath color2 = $chsinfo(152)')
                if not PAUSE_STATE:
                    api.exec_state_command("silent svinfo_report serverstate.txt")
                else:
                    raise Exception("Paused.")

                if new_report_exists(config.STATE_REPORT_P, pre_time):
                    server_info, players = get_svinfo_report(config.STATE_REPORT_P)

                    if bool(server_info):
                        STATE.players = players
                        STATE.update_info(server_info)
                        validate_state()
                        if STATE.current_player is not None:
                            curr_state = f"Spectating {STATE.current_player.n} on {STATE.mapname}" \
                                         f" in server {STATE.hostname} | ip: {STATE.ip}"
                        if curr_state != prev_state:
                            print(colored(curr_state, "blue"))
                        prev_state = curr_state
                        display_player_name(STATE.current_player_id)
        except:
            pass


def initialize_state():
    global STATE
    global PAUSE_STATE

    try:
        # Set a secret color cvar
        secret = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        server_info, bot_player, timeout_flag, reconnect_tries = None, [], 0, 1

        while server_info is None or bot_player == []:
            init_time = time.time()
            if not PAUSE_STATE:
                api.exec_state_command(f"seta color1 {secret};silent svinfo_report serverstate.txt")
            else:
                raise Exception("Paused.")

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
    global PAUSE_STATE

    spectating_self = STATE.curr_dfn == STATE.get_player_by_id(STATE.bot_id).dfn or STATE.current_player_id == STATE.bot_id
    spectating_nospec = STATE.current_player_id not in STATE.spec_ids and STATE.current_player_id != STATE.bot_id
    spectating_afk = STATE.afk_counter >= AFK_TIMEOUT

    if spectating_afk:
        try:
            STATE.afk_counter = 0
            STATE.spec_ids.remove(STATE.current_player_id)
            print("AFK. Switching...")
            if not PAUSE_STATE:
                api.exec_state_command("echo AFK player detected. Switching to the next player.;" * MESSAGE_REPEATS)
        except ValueError:
            pass

    if spectating_self or spectating_nospec or spectating_afk:
        follow_id = random.choice(STATE.spec_ids) if STATE.spec_ids != [] else STATE.bot_id  # Find someone else

        if follow_id != STATE.bot_id:  # Found someone successfully, follow this person
            if spectating_nospec:
                print(colored('Nospec detected. Switching...', 'green'))
                if not PAUSE_STATE:
                    api.exec_state_command("echo Player with no-spec detected. Switching to the next player.;" * MESSAGE_REPEATS)
            display_player_name(follow_id)
            api.exec_state_command(f"follow {follow_id}")
            STATE.idle_counter = 0

        else:  # Only found the bot player
            if STATE.current_player_id != STATE.bot_id:  # Stop spectating if wasn't wasn't already
                api.exec_state_command(f"follow {follow_id}")
                STATE.current_player_id = STATE.bot_id

            STATE.idle_counter += 1  # Was already spectating self, increase idle flag
            print(f"Not spectating. Strike {STATE.idle_counter}/{IDLE_TIMEOUT}")
            if not PAUSE_STATE:
                api.exec_state_command(f"echo Not spectating. Strike {STATE.idle_counter}/{IDLE_TIMEOUT}")

            if STATE.idle_counter >= IDLE_TIMEOUT or spectating_afk:
                # There's been no one on the server for a while or only afks. Switch servers.
                new_ip = servers.get_most_popular_server(ignore_ip=STATE.ip)
                connect(new_ip)
                return
        STATE.current_player_id = follow_id  # Spectating someone
        STATE.current_player = STATE.get_player_by_id(follow_id)

    else:  # check for afk
        inputs = STATE.get_inputs()
        if inputs == '':
            STATE.afk_counter += 1
        else:
            STATE.afk_counter = 0  # reset


def connect(ip):
    global PAUSE_STATE

    connection_time = time.time()
    print(f"Connecting to {ip}...")
    PAUSE_STATE = True
    api.exec_state_command("connect " + ip)
    time.sleep(5)

    max_attempts = 2
    attempt = 1
    while not new_report_exists(config.INITIAL_REPORT_P, connection_time) and attempt <= max_attempts:
        print(f"Retrying connection... (Attempt {attempt}/{max_attempts})")
        restart_connect(ip)
        time.sleep(5 * attempt)
        attempt += 1


def restart_connect(ip):
    global PAUSE_STATE
    api.press_key_mult("{Esc}", 2)
    api.press_key("{Enter}")
    api.press_key_mult("{Tab}", 10)
    api.press_key("{Enter}")
    time.sleep(1)
    api.exec_state_command("connect " + ip)


def new_report_exists(path, time_pov):
    report_mod_time = os.path.getmtime(path)
    return report_mod_time > time_pov


async def switch_spec(direction='next', channel=None):
    global STATE

    spec_ids = STATE.spec_ids if direction == 'next' else STATE.spec_ids[::-1]

    if STATE.current_player_id != STATE.bot_id:
        next_id_index = spec_ids.index(STATE.current_player_id) + 1
        if next_id_index > len(spec_ids) - 1:
            next_id_index = 0
        follow_id = spec_ids[next_id_index]

        if follow_id == STATE.current_player_id:
            msg = "No other players to spectate."
            api.exec_command(f"echo ^1{msg};" * MESSAGE_REPEATS)
            print(msg)
            if channel is not None:
                await channel.send(msg)
        else:
            display_player_name(follow_id)
            api.exec_command(f"follow {follow_id}")
            STATE.idle_counter = 0
            STATE.current_player_id = follow_id

    return True


def display_player_name(follow_id):
    follow_player = STATE.get_player_by_id(follow_id)
    if follow_player is not None:
        player_name = follow_player.n
        display_name = player_name if player_name.strip() not in config.BLACKLISTED_WORDS else "*" * len(player_name)
        api.exec_state_command(f"set player-name {display_name}")


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