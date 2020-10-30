import time
import api as api
import config
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
    if "?nospec" in line: # switch this to a RE match
        api.exec_command(f"say Nospec activated!")
