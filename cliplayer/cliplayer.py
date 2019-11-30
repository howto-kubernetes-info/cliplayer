#!/usr/bin/env python
import yaml
import time
import random
from pynput.keyboard import Key, Listener
import pexpect
import sys
import subprocess
import signal
import os
import argparse
from shutil import copyfile
from pathlib import Path
import configparser
import codecs

home = str(Path.home())

if not os.path.isfile(home + "/.config/cliplayer/cliplayer.cfg"):
    os.makedirs(home + "/.config/cliplayer/", exist_ok=True)
    copyfile(
        sys.prefix + "/config/cliplayer.cfg", home + "/.config/cliplayer/cliplayer.cfg"
    )

config = configparser.ConfigParser(interpolation=None)
config.read(home + "/.config/cliplayer/cliplayer.cfg")

parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--prompt",
    default=codecs.decode(config["DEFAULT"]["prompt"], "unicode-escape") + " ",
    help="prompt to use with playbook. Build it like a normal $PS1 prompt.",
)
parser.add_argument(
    "-n",
    "--next-key",
    default=config["DEFAULT"]["next_key"],
    help="key to press for next command. Default: " + config["DEFAULT"]["next_key"],
)
parser.add_argument(
    "playbook",
    nargs="?",
    default=config["DEFAULT"]["playbook_name"],
    help="path and name to playbook. Default: " + config["DEFAULT"]["playbook_name"],
)
args = parser.parse_args()

PROMPT = args.prompt


def load_playbook():
    try:
        playbook = open(args.playbook, "r")
    except Exception as e:
        print("You need to provide a playbook")
        sys.exit(0)
    commands = []
    for command in playbook:
        commands.append(command.strip())
    return commands


def print_slow(str):
    for letter in str:
        print(letter, flush=True, end="")
        time.sleep(random.uniform(0.0, 0.18))
    time.sleep(0.1)
    print("")


class MyException(Exception):
    pass


def on_press(key):
    if key == getattr(Key, args.next_key):
        global WAIT
        WAIT = False


def signal_handler(sig, frame):
    print("\nYou stopped the tutorial with Ctrl+C!")
    print("Tutorial Cleanup!")
    print("Do you want to remove the following directory? ")
    dirpath = os.getcwd()
    print(dirpath)
    i = input("Remove?: ")
    if i.lower() in ["y", "yes"]:
        print("I clean up the remains.")
        os.system("rm -rf " + dirpath)
        print("Goodbye!")
    else:
        print("I dont' clean up. Goodbye!")
    sys.exit(0)


WAIT = ""


def play():

    signal.signal(signal.SIGINT, signal_handler)

    listener = Listener(on_press=on_press)
    try:
        listener.start()
    except MyException as e:
        print("Listener exception")
        pass

    playbook = load_playbook()
    print(PROMPT, flush=True, end="")

    global WAIT
    WAIT = True
    while WAIT:
        time.sleep(0.3)

    for cmd in playbook:
        if len(cmd.strip()) != 0:
            rows, columns = subprocess.check_output(["stty", "size"]).decode().split()

            try:
                if cmd[0] == "_":
                    try:
                        cmd = cmd[1:]
                        print_slow(cmd.strip())
                        child = pexpect.pty_spawn.spawn(
                            cmd.strip(), encoding="utf-8", timeout=300
                        )
                        child.setwinsize(int(rows), int(columns))
                        child.interact(
                            escape_character="\x1d",
                            input_filter=None,
                            output_filter=None,
                        )
                        child.close()
                        print(PROMPT, flush=True, end="")
                        WAIT = True
                    except:
                        pass
                elif cmd[0] == "!":
                    continue
                elif cmd[0] == "=":
                    try:
                        cmd = cmd[1:]
                        cmd_1, cmd_2 = cmd.split("$$$")
                        child = pexpect.spawn(
                            "/bin/bash",
                            ["-c", cmd_1.strip()],
                            logfile=None,
                            encoding="utf-8",
                            timeout=300,
                        )
                        child.setwinsize(int(rows), int(columns))
                        child.expect(pexpect.EOF)
                        child.close()
                        cmd = cmd_2.replace("VAR", child.before.strip())
                        print_slow(cmd.strip())
                        child = pexpect.spawn(
                            "/bin/bash",
                            ["-c", cmd.strip()],
                            logfile=sys.stdout,
                            encoding="utf-8",
                            timeout=300,
                        )
                        child.setwinsize(int(rows), int(columns))
                        child.expect(pexpect.EOF)
                        child.close()
                        print(PROMPT, flush=True, end="")
                    except:
                        pass
                elif cmd[0] == "+":
                    try:
                        cmd = (
                            '/bin/bash --rcfile <(echo "PS1='
                            + "'"
                            + PROMPT
                            + "'"
                            + '")'
                        )
                        print("\033[0K\r", flush=True, end="")
                        child = pexpect.pty_spawn.spawn(
                            "/bin/bash", ["-c", cmd], encoding="utf-8", timeout=300
                        )
                        child.setwinsize(int(rows), int(columns))
                        child.interact(
                            escape_character="\x1d",
                            input_filter=None,
                            output_filter=None,
                        )
                        child.close()
                        WAIT = True
                    except:
                        pass
                elif cmd[0] == "*":
                    try:
                        path = cmd[1:]
                        os.makedirs(path, exist_ok=True)
                        os.chdir(path)
                    except:
                        pass
                else:
                    print_slow(cmd.strip())
                    child = pexpect.spawn(
                        "/bin/bash",
                        ["-c", cmd.strip()],
                        logfile=sys.stdout,
                        encoding="utf-8",
                        timeout=300,
                    )
                    child.setwinsize(int(rows), int(columns))
                    child.expect(pexpect.EOF)
                    child.close()
                    print(PROMPT, flush=True, end="")
                time.sleep(1)
                while WAIT:
                    pass
                    time.sleep(0.3)
                WAIT = True
            except MyException as e:
                print(e)


if __name__ == "__main__":
    play()
