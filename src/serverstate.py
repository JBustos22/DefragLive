"""
This file contains two important classes that contain the current live state of the game:
State - stores information about the current server, such meta data and players. It contains a set of methods to
         conveniently query information that is expected to be needed frequently.
Player - stores individual in-depth information about each player. The server object's players attribute contains a
         list of these objects

It also contains many important methods that handle different parts of the server state process. See their documentation
for details.
"""

import api
import re
import time
import random
import config
import os
import servers


# Configurable variables
MESSAGE_REPEATS = 1  # How many times to spam info messages. 0 for no messages.
AFK_TIMEOUT = 60  # Switch after afk detected x consecutive times.
IDLE_TIMEOUT = 5  # Alone in server timeout.
INIT_TIMEOUT = 10  # Determines how many times to try the state initialization before giving up.
MAP_LOAD_WAIT = 3  # Time to wait for a map to load. (Will increase proportional to retries count)


STATE = None
PAUSE_STATE = False
IGNORE_IPS = []
RECONNECTING = False
VID_RESTARTING = False
STATE_INITIALIZED = False
LAST_REPORT_TIME = time.time()
LAST_INIT_REPORT_TIME = time.time()

class State:
    """
    Class that stores data about the state of the server and players
    """
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
        self.afk_ids = []

    def __str__(self):
        return str(self.__class__) + ": " + str(self.__dict__)

    def update_info(self, server_info):
        """Helper function for resetting the class's properties on state referesh"""
        for key in server_info:
            setattr(self, key.replace('sv_', ''), server_info[key])
        self.current_player = self.get_player_by_id(self.current_player_id)
        if self.bot_id in self.spec_ids:
            self.spec_ids.remove(self.bot_id)
        # remove afk players from speccable id list
        [self.spec_ids.remove(afk_id) for afk_id in self.afk_ids if afk_id in self.spec_ids]

    def get_player_by_id(self, c_id):
        """Helper function for easily retrieving a player object from a client id number"""
        id_player = [player for player in self.players if player.id == c_id]
        id_player = id_player[0] if len(id_player) > 0 else None
        return id_player

    def get_inputs(self):
        """Helper functions for easily retrieving the latest inputs recorded from the watched player."""
        bot_player = self.get_player_by_id(self.bot_id)
        return bot_player.c2.replace(' ', '')


class Player:
    """
    Simple class for storing data about each client/player present in the server.
    """
    def __init__(self, id, player_data):
        self.id = id
        for key in player_data:
            setattr(self, key, player_data[key])
        self.nospec = self.c1 == 'nospec'


def start():
    """
    The main gateway for fetching the server state through /svinfo_report. It runs through a loop indefinitely and
    attempts to extract new data only if state is not paused through the PAUSE_STATE flag.
    """
    global STATE
    global PAUSE_STATE
    global VID_RESTARTING

    while True:
        try:
            if PAUSE_STATE:
                raise Exception("Paused.")

            prev_state, curr_state = None, None
            initialize_state()  # Handle the first state fetch. Some extra processing needs to be done this time.

            # Only refresh the STATE object if new data has been read and if state is not paused
            while not new_report_exists(config.INITIAL_REPORT_P) and not PAUSE_STATE:
                time.sleep(2)

                if not PAUSE_STATE:
                    api.exec_state_command("varmath color2 = $chsinfo(152);"  # Store inputs in color2
                                           "silent svinfo_report serverstate.txt")  # Write a new report
                elif not VID_RESTARTING:
                    raise Exception("Paused.")

                if new_report_exists(config.STATE_REPORT_P):
                    # Given that a new report exists, read this new data.
                    server_info, players = get_svinfo_report(config.STATE_REPORT_P)

                    if bool(server_info):  # New data is not empty and valid. Update the state object.
                        STATE.players = players
                        STATE.update_info(server_info)
                        validate_state()  # Check for nospec, self spec, afk, and any other problems.
                        if STATE.current_player is not None and STATE.current_player_id != STATE.bot_id:
                            curr_state = f"Spectating {STATE.current_player.n} on {STATE.mapname}" \
                                         f" in server {STATE.hostname} | ip: {STATE.ip}"
                        if curr_state != prev_state:
                            print(curr_state)
                        prev_state = curr_state
                        display_player_name(STATE.current_player_id)
        except:
            pass


def initialize_state():
    """
    Handles necessary processing on the first iteration of state retrieval.
    Important steps done here:
        - Check if there's a valid connection
        - Retrieve the bot's client id using the "color1" cvar and a fresh secret code
    """
    global STATE
    global PAUSE_STATE
    global INIT_TIMEOUT
    global STATE_INITIALIZED

    try:
        # Create a secret code. Only "secret" for one use.
        secret = ''.join(random.choice('0123456789ABCDEF') for i in range(16))
        server_info, bot_player, timeout_flag = None, [], 0

        init_counter = 0
        while server_info is None or bot_player == []:  # Continue running this block until valid data and bot id found
            init_counter += 1
            if not PAUSE_STATE:
                # Set color1 to secret code to determine bot's client id
                api.exec_state_command(f"seta color1 {secret};silent svinfo_report serverstate.txt")
            else:
                raise Exception("Paused.")

            if new_report_exists(config.STATE_REPORT_P):  # New data detected
                server_info, players = get_svinfo_report(config.STATE_REPORT_P)  # Read data
                # Select player that contains this secret as their color1, this will be the bot player.
                bot_player = [player for player in players if player.c1 == secret]

            # If loop hits the max iterations, the connection was not established properly
            if init_counter >= INIT_TIMEOUT:
                # Retry a connection to best server
                new_ip = servers.get_next_active_server(IGNORE_IPS)
                connect(new_ip)

        bot_id = bot_player[0].id  # Find our own ID

        # Create global server object
        STATE = State(secret, server_info, players, bot_id)
        STATE.current_player_id = bot_id
        STATE_INITIALIZED = True
        print("State Initialized.")
    except:
        return False

    return True


def validate_state():
    """
    Analyzes the server state data any issues in our current state, specifically for:
    - An idle bot (self-spectating)
    - A lack of players to spec
    - AFK player detection
    - No-specced player detection
    """
    global STATE
    global PAUSE_STATE
    global IGNORE_IPS

    # Current player spectated is our bot, and thus idle.
    spectating_self = STATE.curr_dfn == STATE.get_player_by_id(STATE.bot_id).dfn \
                      or STATE.current_player_id == STATE.bot_id

    # Current player spectated has turned on the no-spec system
    spectating_nospec = STATE.current_player_id not in STATE.spec_ids and STATE.current_player_id != STATE.bot_id

    # The player that we are spectating has been AFK for our set limit of AFK strikes
    spectating_afk = STATE.afk_counter >= AFK_TIMEOUT

    # AFK player pre-processing
    if spectating_afk:
        try:
            STATE.spec_ids.remove(STATE.current_player_id)  # Remove afk player from list of spec-able players
            # Add them to the afk list
            STATE.afk_ids.append(STATE.current_player_id) if STATE.current_player_id not in STATE.afk_ids else None
            if not PAUSE_STATE:
                print("AFK. Switching...")
                api.exec_state_command("echo ^2---^3AFK player detected."
                                       " Switching to the next player.^2---;" * MESSAGE_REPEATS)
                STATE.afk_counter = 0  # Reset AFK strike counter for next player
        except ValueError:
            pass

    # Next player choice logic
    if spectating_self or spectating_nospec or spectating_afk:
        follow_id = random.choice(STATE.spec_ids) if STATE.spec_ids != [] else STATE.bot_id  # Find someone else to spec

        if follow_id != STATE.bot_id:  # Found someone successfully, follow this person
            if spectating_nospec:
                if not PAUSE_STATE:
                    print('Nospec detected. Switching...')
                    api.exec_state_command("echo ^2---^3Player with no-spec detected. "
                                           "Switching to the next player.^2---;" * MESSAGE_REPEATS)
            display_player_name(follow_id)
            api.exec_state_command(f"follow {follow_id}")
            STATE.idle_counter = 0  # Reset idle counter

        else:  # Only found ourselves to spec.
            if STATE.current_player_id != STATE.bot_id:  # Stop spectating player, go to free spec mode instead.
                api.exec_state_command(f"follow {follow_id}")
                STATE.current_player_id = STATE.bot_id
            else:  # Was already spectating self. This is an idle strike
                STATE.idle_counter += 1
                print(f"Not spectating. Strike {STATE.idle_counter}/{IDLE_TIMEOUT}")
                if not PAUSE_STATE:
                    api.exec_state_command(f"echo ^2---^3Not spectating. "
                                           f"Strike {STATE.idle_counter}/{IDLE_TIMEOUT}^2---")

            if STATE.idle_counter >= IDLE_TIMEOUT or spectating_afk:
                # There's been no one on the server for a while or only afks. Switch servers.

                # Ignore this ip until a good server is found
                IGNORE_IPS.append(STATE.ip) if STATE.ip not in IGNORE_IPS else None
                new_ip = servers.get_next_active_server(IGNORE_IPS)
                if bool(new_ip):
                    connect(new_ip)
                    return
                else:  # No ip left to connect to, reset ip blacklist.
                    IGNORE_IPS = []
        STATE.current_player_id = follow_id  # Spectating someone.
        STATE.current_player = STATE.get_player_by_id(follow_id)

    else:  # AFK detection
        inputs = STATE.get_inputs()
        if inputs == '': # Empty key presses. This is an AFK strike.
            STATE.afk_counter += 1
            if STATE.afk_counter >= 15 and STATE.afk_counter % 5 == 0:
                print(f"AFK detected. Strike {STATE.afk_counter}/{AFK_TIMEOUT}")
                api.exec_state_command(f"echo ^2---^3AFK player detected. Switching in"
                                       f" {(int(AFK_TIMEOUT-STATE.afk_counter)*2)} seconds.^2---;" * MESSAGE_REPEATS)
        else:
            # Activity detected, reset AFK strike counter and empty AFK list + ip blacklist
            STATE.afk_counter = 0
            STATE.afk_ids = []
            IGNORE_IPS = []


def connect(ip):
    """
    Handles connection to a server and re-attempts if connection is not resolved.
    """
    global PAUSE_STATE
    global MAP_LOAD_WAIT
    global STATE_INITIALIZED

    STATE_INITIALIZED = False
    print(f"Connecting to {ip}...")
    PAUSE_STATE = True
    api.exec_state_command("connect " + ip)
    time.sleep(2)

    max_reattempts, reattempt_count = 2, 0
    max_wait_time, wait_count = 10, 1

    # Loop until a new initial_report.txt is found. (Automatically created on respawn per respawn.cfg)
    while (not new_report_exists(config.INITIAL_REPORT_P) and not STATE_INITIALIZED) and reattempt_count <= max_reattempts:
        # Respawn file is not found. This is a connection strike.
        print(f"Connection not detected. Strike {wait_count}/{max_wait_time}")
        if wait_count >= max_wait_time:
            reattempt_count += 1
            if reattempt_count >= max_reattempts:
                IGNORE_IPS.append(ip) if ip not in IGNORE_IPS else None
            else:
                max_wait_time = 10 * (reattempt_count + 1)  # Make wait time proportional to re-attempt iteration
                MAP_LOAD_WAIT = reattempt_count + 1 * MAP_LOAD_WAIT
                wait_count = 1
                print(f"Retrying connection. Re-attempt {reattempt_count}/{max_reattempts}."
                      f" Bumping wait time to {max_wait_time}")
                restart_connect(ip)
        else:
            wait_count += 1
        time.sleep(1)


def restart_connect(ip):
    """
    Handles hard server connection restart. This method of connecting is menu-proof, in case we were stuck in the menu.
    """
    global PAUSE_STATE

    global RECONNECTING

    PAUSE_STATE, RECONNECTING = True, True
    api.press_key_mult("{Esc}", 2)
    api.press_key("{Enter}")
    api.press_key_mult("{Tab}", 10)
    api.press_key("{Enter}")
    time.sleep(2)
    api.exec_state_command("connect " + ip)


def new_report_exists(path):
    """
    Helper function for checking if the report is new relative to a given time stamp.
    """
    global LAST_INIT_REPORT_TIME, LAST_REPORT_TIME
    curr_report_mod_time = os.path.getmtime(path)
    if path == config.INITIAL_REPORT_P:
        last_report_ts = LAST_INIT_REPORT_TIME
        LAST_INIT_REPORT_TIME = curr_report_mod_time
    else:
        last_report_ts = LAST_REPORT_TIME
        LAST_REPORT_TIME = curr_report_mod_time
    return curr_report_mod_time > last_report_ts


async def switch_spec(direction='next', channel=None):
    """
    Handles "smart" spec switch. Resets data relevant to old connections and players. Can move either forward (default)
    or backwards (used by ?prev).
    """
    global STATE
    global IGNORE_IPS

    IGNORE_IPS = []
    STATE.afk_list = []
    spec_ids = STATE.spec_ids if direction == 'next' else STATE.spec_ids[::-1]  # Reverse spec_list if going backwards.

    if STATE.current_player_id != STATE.bot_id:
        # Determine the next followable id. If current id is at the last index, wrap to the beginning of the list.
        next_id_index = spec_ids.index(STATE.current_player_id) + 1
        if next_id_index > len(spec_ids) - 1:
            next_id_index = 0
        follow_id = spec_ids[next_id_index]

        if follow_id == STATE.current_player_id: # Landed on the same id (list is length 1). No other players to spec.
            msg = "No other players to spectate."
            api.exec_command(f"echo ^1{msg};" * MESSAGE_REPEATS)
            print(msg)
            if channel is not None:
                await channel.send(msg)
        else:
            display_player_name(follow_id)
            api.exec_command(f"follow {follow_id}")  # Follow this player.
            STATE.idle_counter = 0  # Reset idle strike flag since a followable non-bot id was found.
            STATE.current_player_id = follow_id  # Notify the state object of the new player we are spectating.

    return True


def display_player_name(follow_id):
    """
    Displays the player's name in the player-name custom cvar. Censor if in the list of blacklisted words.
    """
    follow_player = STATE.get_player_by_id(follow_id)
    if follow_player is not None:
        player_name = follow_player.n
        display_name = player_name if player_name.strip() not in config.BLACKLISTED_WORDS else "*" * len(player_name)
        # api.exec_state_command(f"set player-name {display_name}")


def get_svinfo_report(filename):
    """
    Handles parsed data of the server info report. Turns the parsed data into coherent objects.
    """
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

            if player_data['c1'] != 'nospec': # Filter out nospec'd players out of followable ids
                players.append(Player(cli_id, player_data))
                if player_data['t'] != '3':  # Filter out spectators out of followable ids.
                    spec_ids.append(cli_id)
        except:
            continue

    server_info['spec_ids'] = spec_ids
    return server_info, players


def parse_svinfo_report(lines):
    """
    Handles parsing of the server report files. Extracts only the necessary information, such as server and player data.
    """
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
                ip = re.match(title_r, line).group(1)  # Extract server's ip
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
