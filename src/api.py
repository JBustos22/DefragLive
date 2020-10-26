import time
import keyboard

import config


def exec_command(cmd):
    with open(config.DF_DIR + "\\twitch_cmd.cfg", "w+") as f:
        f.write(cmd)
        f.close()
    press_key(config.get_bind("exec twitch_cmd.cfg"))


def enter_input(cmd):
    keyboard.write(cmd, delay=0.03)


def press_key(x):
    print("pressing key: ", x)
    keyboard.send(x)


def press_key_mult(x, amount, delay=0.03):
    for _ in range(amount):
        press_key(x)
        time.sleep(delay)


# duration in seconds
def hold_key(x, duration):
    keyboard.press(x)
    time.sleep(duration)
    keyboard.release(x)
