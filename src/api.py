import os
import time
import keyboard
from pywinauto import application

from ahk import AHK

import config

AHK = AHK()
WINDOW = None


def api_init():
    global WINDOW

    WINDOW = AHK.find_window(process=config.DF_EXE_PATH)

    if WINDOW == None:
        raise RuntimeError


def exec_command(cmd, verbose=True):
    if verbose:
        print(f"Execing command {cmd}")

    with open(os.path.join(config.DF_DIR, 'twitch_cmd.cfg'), "w+") as f:
        f.write(cmd)

    press_key(config.get_bind(f"execq twitch_cmd.cfg"), verbose=False)


def exec_state_command(cmd):
    with open(os.path.join(config.DF_DIR, 'state_cmd.cfg'), "w+") as f:
        f.write(cmd)

    press_key(config.get_bind(f"execq state_cmd.cfg"), verbose=False)

def press_key(key, verbose=True):
    if verbose:
        print(f"Pressing key {key}")
    WINDOW.send(key, blocking=True, press_duration=30)


def press_key_mult(x, amount, delay=0.03, verbose=True):
    if verbose:
        print(f"Pressing {x} {amount} times with a delay of {delay}")
    for _ in range(amount):
        WINDOW.send(x, blocking=True, press_duration=30)
        time.sleep(delay)


# duration in seconds
def hold_key(x, duration):
    print(f"Holding {x} for {duration} seconds")

    WINDOW.send(x, blocking=True, press_duration=duration * 1000)
