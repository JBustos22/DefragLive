import time
import keyboard
from pywinauto import application

import config

df_window = None

def api_init(df_exe_p):
    global df_window

    if df_exe_p is not None:
        df_window = application.Application().connect(path=df_exe_p)
    else:
        df_window = application.Application().connect(title='iDFe')


def exec_command(cmd):
    with open(config.DF_DIR + "\\twitch_cmd.cfg", "w+") as f:
        f.write(cmd)
        f.close()
    press_key(config.get_bind("exec twitch_cmd.cfg"))


# Not needed anymore?
# def enter_input(cmd):
#     keyboard.write(cmd, delay=0.03)


def press_key(x):
    print("pressing key: ", x)
    if df_window is not None:
        df_window.iDFe.send_keystrokes('{%s}' % x.upper())
    else:
        keyboard.send(x)


def press_key_mult(x, amount, delay=0.03):
    print(f"pressing {x} {amount} times with a delay of {delay}")
    for _ in range(amount):
        press_key(x)
        time.sleep(delay)


# duration in seconds
def hold_key(x, duration):
    print(f"holding {x} for {duration} seconds")

    # this method makes the defrag window active automatically
    if df_window is not None:
        df_window.iDFe.type_keys('{%s down}' % x)
        time.sleep(duration)
        df_window.iDFe.type_keys('{%s up}' % x)
    else:
        keyboard.press(x)
        time.sleep(duration)
        keyboard.release(x)
