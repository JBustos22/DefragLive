import os
import time
import keyboard
from pywinauto import application
import logging

from ahk import AHK

import config


AHK = AHK()
CONSOLEWINDOW = "TwitchBot Console"
ENGINEWINDOW = "TwitchBot Engine"


class WindowNotFoundError(Exception):
    pass


def api_init():
    """Grab both engine and console windows. Thanks to run for this code"""
    global CONSOLE
    global WINDOW

    CONSOLE = AHK.run_script("WinShow," + CONSOLEWINDOW + \
                   "\nControlGet, console, Hwnd ,, Edit1, " + CONSOLEWINDOW + \
                   "\nWinHide," + CONSOLEWINDOW + \
                   "\nFileAppend, %console%, * ;", blocking=True)
    WINDOW = AHK.find_window(process=config.DF_EXE_PATH, title=b"TwitchBot Engine")

    if CONSOLE is None or WINDOW is None:
        raise WindowNotFoundError


def exec_command(cmd, verbose=True):
    if verbose:
        logging.info(f"Execing command {cmd}")
    # send the text to the console window, escape commas (must be `, to show up in chat)
    AHK.run_script("ControlSetText, , " + cmd.replace(',', '`,') + ", ahk_id " + CONSOLE+ \
                "\nControlSend, , {Enter}, ahk_id " + CONSOLE, blocking=True)


def press_key(key, verbose=True):
    try:
        if verbose:
            logging.info(f"Pressing key {key}")
        WINDOW.send(key, blocking=True, press_duration=30)
    except AttributeError:
        logging.info(f"Window not active. {key} was not sent to the client.")


# duration in seconds
def hold_key(x, duration):
    try:
        logging.info(f"Holding {x} for {duration} seconds")

        WINDOW.send(x, blocking=True, press_duration=duration * 1000)
    except AttributeError:
        logging.info(f"Window not active. {x} was not sent to the client.")