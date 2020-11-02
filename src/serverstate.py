"""
This file contains two important classes that keep the current state of the game:
Server - stores information about the current server, such meta data and players. It contains a set of methods to
         conveniently query information that is expected to be needed frequently.
Player - stores individual in-depth information about each player. The server object's players attribute contains a
         list of these objects. Contains a set of methods that make player operations convenient.
"""

import console
import api


class Server:
    def __init__(self, ip=None):
        self.set_server_status()
        self.multiplayer = ip is not None
        self.ip = ip
        self.nospec_list = []  # Would contain a list of player objects with no_spec activated

    def set_server_status(self):
        """Obtains data from the /serverstatus command and initializes attributes dynamically"""
        server_data, player_list = console.server_status()[:]
        for key in server_data:
            setattr(self, key, server_data[key])  # set all these key-value pairs as attributes
        self.set_players_info(player_list)

    def set_players_info(self, player_list):  # player_list unused for now. May need if ping information is required
        """Obtains data from the /info players command and initializes the player objects"""
        self.players = []
        player_data = console.info_players()
        for player_info in player_data:
            self.players.append(Player(player_info))

    def get_id_by_name(self, name):
        """Retrieves all the client ids matching a given name."""
        ids_with_name = []
        for player in self.players:
            if player.name == name:
                ids_with_name.append(player.id)
        return ids_with_name if len(ids_with_name) > 0 else None

    def get_current_physics(self):
        """Returns the current physics in human-readable format"""
        physics = "cpm" if self.df_promode == 1 else "vq3"
        suffix = f".{self.defrag_mode}" if self.defrag_gametype == '7' else ""  # For fastcaps physics
        return physics + suffix


class Player:
    def __init__(self, player_info, ping=-1):
        self.name = player_info['name']
        self.id = player_info['id']
        self.playing = False if player_info['team'] == 'SPEC' else True
        self.no_spec = False
        self.ping = ping
        self.secret_code = '123'  # use random func

    def send_pm(self, msg):
        """Send a private message in game"""
        api.exec_command(f"tell {id} {msg}")

    def toggle_nospec(self):
        """Toggle the player's nospec flag. If True, the bot will avoid spectating this player"""
        self.no_spec = not self.no_spec
