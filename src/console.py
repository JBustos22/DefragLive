import time
import api as api
from termcolor import colored


#import command functions from another


def read(file_path, verbose=True):
    with open(file_path, 'r') as log:
        while 1:
            where = log.tell()
            line = log.readline()
            if not line:
                time.sleep(1)
                log.seek(where)
            elif "serverCommand" in line:
                process_line(line)
                if verbose:
                    print(colored(line, 'yellow'))


def process_line(line):
    # RE stuff, calls command functions go here
    # this is proof of concept, we should find a way not to have a bunch of if statements
    if ": ^2?nospec" in line: # switch this to a RE match
        # no spec logic or function with logic here
        api.exec_command(f"say Nospec command received.")
    elif ": ^2?info" in line:
        info_string = "This is a 24/7 livestream: https://www.twitch.tv/defraglive. Contact: defragtv@gmail.com. " \
                      "Use ?help for all the available commands"
        api.exec_command(f"say {info_string}")
    elif ": ^2?help" in line:
        help_string = "Current commands are ?nospec, ?info, and ?help"
        api.exec_command(f"say {help_string}")