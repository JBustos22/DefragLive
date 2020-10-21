import re
import os
import api

DF_WIN_TITLE = b"iDFe"
SRC_DIR = "C:\\Users\Donald\\Documents\\GitHub\\DFTwitchBot\\src"

DF_DIR = "E:\\GAMES\\DEFRAG SCRAPE\\defrag"
CFG_NAME = "q3config.cfg"
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

    # Replace all binds with their AHK equivalents, if necessary
    BINDS["toggleconsole"] = "{VKDC}"

    for (cmd, bind) in BINDS.items():
        if cmd == "toggleconsole":
            continue
        elif bind == "ENTER":
            BINDS[cmd] = "{Enter}"
        elif bind == "ESCAPE":
            BINDS[cmd] = "{Escape}"
        elif bind == "TAB":
            BINDS[cmd] = "{Tab}"
        elif re.match(r"F\d+?", bind):
            BINDS[cmd] = "{" + bind + "}"
        else:
            BINDS[cmd] = api.escape(bind)
