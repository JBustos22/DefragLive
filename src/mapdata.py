"""
This is the map data module
it allows us to save and load meta data related to each map
For now used to store data about gamma / reshade settings /  other visual stuff
But could be used in the future for any map specific data
"""

import sqlite3
import os.path
import json

STORAGE_PATH = "../storage/mapdata.db"
MAPDATA_TABLE = "mapdata"

singleton = lambda c: c()

@singleton
class MapData(object):
    def __init__(self):
        if not os.path.isfile(STORAGE_PATH):
            open(STORAGE_PATH, "x")

        self.con = sqlite3.connect(STORAGE_PATH)
        self.cur = self.con.cursor()

        # id (integer representing row id), mapname (string representing map name), data (json string that represents all data required)
        # we use json for data since it allows us to extra data for the future without having to change the database schema
        self.cur.execute(f"CREATE TABLE IF NOT EXISTS {MAPDATA_TABLE} (id INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE, mapname TEXT, data TEXT)")
        self.con.commit()

    def load(self, mapname):
        result = self.cur.execute(f'SELECT * FROM {MAPDATA_TABLE} WHERE mapname = ? LIMIT 1', (mapname,)).fetchone()

        return result

    def save(self, mapname, key, value):
        result = self.load(mapname)

        if result is None:
            data = {
                key: value
            }

            self.cur.execute(f'INSERT INTO {MAPDATA_TABLE} (mapname, data) VALUES (?, ?)', (
                mapname,
                json.dumps(data)
            ))
        else:
            data = json.loads(result[2])
            data[key] = value

            self.cur.execute(f'UPDATE {MAPDATA_TABLE} SET data =  ? WHERE id = ?', (
                json.dumps(data),
                result[0]
            ))

        self.con.commit()

    def clear(self, mapname):
        self.cur.execute(f'DELETE FROM {MAPDATA_TABLE} WHERE mapname = ?  LIMIT 1', (mapname,))
        self.con.commit()