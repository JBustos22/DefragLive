from ahk import AHK
from ahk.utils import escape_sequence_replace

import config

AHK = AHK()
WINDOW = AHK.find_window(title=config.DF_WIN_TITLE)


def exec_command(cmd):
    with open(config.DF_DIR + "\\twitch_cmd.cfg", "w+") as f:
        f.write(cmd)
        f.close()
    enter_input(config.get_bind("exec twitch_cmd.cfg"))


def enter_input(cmd):
    WINDOW.send(cmd + "{Enter}", raw=False, delay=30, blocking=True, press_duration=30)


def press_key(x):
    WINDOW.send(x, raw=False, blocking=True, press_duration=30)


def hold_key(x, duration):
    WINDOW.send(x, raw=False, blocking=True, press_duration=duration)


# Question 1: How to force console state open/closed?
# Answer: Escape -> Escape -> Console Bind
# This will force the console open regardless of its initial state
# def open_console():
#     cmd = "{Esc}{Esc}" + "+" + config.get_bind("toggleconsole")
#     WINDOW.send(cmd, raw=False, delay=100, blocking=True, press_duration=100)


# def close_console():
#     cmd = "{Esc}{Esc}"
#     WINDOW.send(cmd, raw=False, delay=100, blocking=True, press_duration=100)


def escape(arg):
    return escape_sequence_replace(arg)
