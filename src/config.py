import re
import os
import api
from dotenv import load_dotenv

load_dotenv()
DF_DIR, CFG_NAME = os.environ['DF_DIR'], os.environ['CFG_NAME']
DF_EXE_NAME = "iDFe.exe"
DF_WIN_TITLE = b"iDFe"
CFG_P = os.path.join(DF_DIR, CFG_NAME)

BINDS = None


def get_bind(cmd):
    global BINDS

    return BINDS[cmd]


def get_bind_fuzzy(rx, raw=False):
    global BINDS

    if not raw:
        rx = "^.+?" + rx + ".+?$"

    for cmd, bind in BINDS.items():
        if re.search(rx, cmd):
            return bind

    raise RuntimeError("Could not find bind for " + rx)


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
