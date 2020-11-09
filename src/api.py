import os
import time
import keyboard
from pywinauto import application

from ahk import AHK

import config

AHK = AHK()
WINDOW = AHK.find_window(title=b"iDFe")


def exec_command(cmd):
    with open(os.path.join(config.DF_DIR, "twitch_cmd.cfg"), "w+") as f:
        f.write(cmd)

    press_key(config.get_bind("exec twitch_cmd.cfg"))


def press_key(x):
    WINDOW.send(x, blocking=True, press_duration=30)


def press_key_mult(x, amount, delay=0.03):
    print(f"pressing {x} {amount} times with a delay of {delay}")
    for _ in range(amount):
        WINDOW.send(x, blocking=True, press_duration=30)
        time.sleep(delay)


# duration in seconds
def hold_key(x, duration):
    print(f"holding {x} for {duration} seconds")

    WINDOW.send(x, press_duration=duration)
