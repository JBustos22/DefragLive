import os
import time
import keyboard
from pywinauto import application
import logging

from ahk import AHK

import config

AHK = AHK()
WINDOW = None


class WindowNotFoundError(Exception):
    pass


def api_init():
    global WINDOW

    WINDOW = AHK.find_window(process=config.DF_EXE_PATH)

    if WINDOW == None:
        raise WindowNotFoundError


def exec_command(cmd, verbose=True):
    if verbose:
        logging.info(f"Execing command {cmd}")

    with open(os.path.join(config.DF_DIR, 'twitch_cmd.cfg'), "w+") as f:
        f.write(cmd)

    press_key(config.get_bind(f"execq twitch_cmd.cfg"), verbose=False)


def exec_state_command(cmd):
    with open(os.path.join(config.DF_DIR, 'state_cmd.cfg'), "w+") as f:
        f.write(cmd)

    press_key(config.get_bind(f"execq state_cmd.cfg"), verbose=False)


def press_key(key, verbose=True):
    try:
        if verbose:
            logging.info(f"Pressing key {key}")
        WINDOW.send(key, blocking=True, press_duration=30)
    except AttributeError:
        logging.info(f"Window not active. {key} was not sent to the client.")


def press_key_mult(x, amount, delay=0.03, verbose=True):
    try:
        if verbose:
            logging.info(f"Pressing {x} {amount} times with a delay of {delay}")
        for _ in range(amount):
            WINDOW.send(x, blocking=True, press_duration=30)
            time.sleep(delay)
    except AttributeError:
        logging.info(f"Window not active. {x} was not sent to the client.")


# duration in seconds
def hold_key(x, duration):
    try:
        logging.info(f"Holding {x} for {duration} seconds")

        WINDOW.send(x, blocking=True, press_duration=duration * 1000)
    except AttributeError:
        logging.info(f"Window not active. {x} was not sent to the client.")