import re
import os
from env import environ

DF_DIR = environ['DF_DIR'] if 'DF_DIR' in environ and environ['DF_DIR'] != "" else input('Full path to your defrag folder: ')
CFG_NAME = environ['CFG_NAME']
CFG_P = os.path.join(DF_DIR, CFG_NAME)

BINDS = None


def get_bind(cmd):
    global BINDS
    if BINDS is None:
        read_cfg()

    return BINDS[cmd]


def read_cfg():
    global BINDS
    BINDS = {}

    with open(CFG_P, "r") as cfg_f:
        cfg = cfg_f.readlines()

    for line in cfg:
        try:
            r = r"bind[ ]+?(.+?)[ ]+?\"(.+?)\""
            match = re.match(r, line)
            key = match.group(1)
            cmd = match.group(2)
            BINDS[cmd] = key
        except:
            continue

    validate_cfg()


def validate_cfg():
    global BINDS

    # Replace all binds with their proper equivalents, if necessary
    BINDS["toggleconsole"] = 29

    for (cmd, bind) in BINDS.items():
        if cmd == "toggleconsole":
            continue
        elif bind == "ENTER":
            BINDS[cmd] = "enter"
        elif bind == "ESCAPE":
            BINDS[cmd] = "esc"
        elif bind == "TAB":
            BINDS[cmd] = "tab"
        else:
            pass
