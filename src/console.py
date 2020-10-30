import time
import api as api
from termcolor import colored
import commands


def read(file_path, verbose=True):
    with open(file_path, 'r') as log:
        while 1:
            where = log.tell()
            line = log.readline()
            if not line:
                time.sleep(1)
                log.seek(where)
            elif "serverCommand" in line:
                if verbose:
                    print(colored(line, 'yellow'))
                line_data = process_line(line)
                if bool(line_data):  # check if line is a command TODO: Use some something like bool(line_data.command)
                    process_command(line_data, "use line_data.command here")
                else:
                    ""
                    print("Not a command")
                    # something else


def process_line(line):
    # TODO: Add formatting logic here. RE stuff should go here. Format into a nice dictionary like this

    # formatting...
    # line_data = {"type": line_type, "command": command, "author": author, "content": content, ...}
    # return line_data
    return line


def process_command(line_data, command):
    # TODO: Should find a way not to have a bunch of if statements
    # TODO: Use command functions from command.py to process for each situation

    # Proof of concept code:
    # TODO: Change conditionals to use command param, etc.
    if ": ^2?nospec" in line_data: # switch this to a RE match
        # no spec logic or function with logic here
        api.exec_command(f"say Nospec command received.")
    elif ": ^2?info" in line_data:
        info_string = "This is a 24/7 livestream: https://www.twitch.tv/defraglive. Contact: defragtv@gmail.com. " \
                      "Use ?help for all the available commands"
        api.exec_command(f"say {info_string}")
    elif ": ^2?help" in line_data:
        help_string = "Current commands are ?nospec, ?info, and ?help"
        api.exec_command(f"say {help_string}")