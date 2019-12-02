#!/usr/bin/env python

"""
This is a Module to play a playbook with bash commands like they typed in the moment
"""

import argparse
import configparser
import codecs
import os
import signal
import subprocess
import sys
import time
import random
from shutil import copyfile
from pathlib import Path
import pexpect
from pynput.keyboard import Key, Listener

HOME = str(Path.home())

if not os.path.isfile(HOME + "/.config/cliplayer/cliplayer.cfg"):
    os.makedirs(HOME + "/.config/cliplayer/", exist_ok=True)
    copyfile(
        sys.prefix + "/config/cliplayer.cfg", HOME + "/.config/cliplayer/cliplayer.cfg"
    )

CONFIG = configparser.ConfigParser(interpolation=None)
CONFIG.read(HOME + "/.config/cliplayer/cliplayer.cfg")

PARSER = argparse.ArgumentParser()
PARSER.add_argument(
    "-p",
    "--prompt",
    default=codecs.decode(CONFIG["DEFAULT"]["prompt"], "unicode-escape") + " ",
    help="prompt to use with playbook. Build it like a normal $PS1 prompt.",
)
PARSER.add_argument(
    "-n",
    "--next-key",
    default=CONFIG["DEFAULT"]["next_key"],
    help="key to press for next command. Default: " + CONFIG["DEFAULT"]["next_key"],
)
PARSER.add_argument(
    "-i",
    "--interactive-key",
    default=CONFIG["DEFAULT"]["interactive_key"],
    help="key to press for a interactive bash as the next command. Default: "
    + CONFIG["DEFAULT"]["interactive_key"],
)
PARSER.add_argument(
    "-b",
    "--base-speed",
    default=CONFIG["DEFAULT"]["base_speed"],
    help="base speed to type one character. Default: "
    + CONFIG["DEFAULT"]["base_speed"],
)
PARSER.add_argument(
    "-m",
    "--max-speed",
    default=CONFIG["DEFAULT"]["max_speed"],
    help="max speed to type one character. Default: " + CONFIG["DEFAULT"]["max_speed"],
)
PARSER.add_argument(
    "playbook",
    nargs="?",
    default=CONFIG["DEFAULT"]["playbook_name"],
    help="path and name to playbook. Default: " + CONFIG["DEFAULT"]["playbook_name"],
)
ARGS = PARSER.parse_args()

PROMPT = ARGS.prompt


def load_playbook():
    """
    Loading commands from a playbook and returning a list with the commands.
    """
    try:
        playbook = open(ARGS.playbook, "r")
    except FileNotFoundError:
        print("You need to provide a playbook")
        sys.exit(0)
    commands = []
    for command in playbook:
        commands.append(command.strip())
    return commands


def print_slow(string):
    """
    Printing characters like you type it at the moment.
    """
    for letter in string:
        print(letter, flush=True, end="")
        time.sleep(random.uniform(float(ARGS.base_speed), float(ARGS.max_speed)))
    time.sleep(0.1)
    print("")


class MyException(Exception):
    pass


def interactive_bash():
    """
    Start a new bash and give interactive control over it
    """
    try:
        rows, columns = subprocess.check_output(["stty", "size"]).decode().split()
        cmd = '/bin/bash --rcfile <(echo "PS1=' + "'" + PROMPT + "'" + '")'
        print("\033[0K\r", flush=True, end="")
        child = pexpect.pty_spawn.spawn(
            "/bin/bash", ["-c", cmd], encoding="utf-8", timeout=300
        )
        child.setwinsize(int(rows), int(columns))
        child.interact(
            escape_character="\x1d", input_filter=None, output_filter=None,
        )
        child.close()
        global WAIT
        WAIT = True
        time.sleep(1.0)
    except pexpect.exceptions.ExceptionPexpect as e:
        print(e)


def on_press(key):
    """
    Called on every key press to check if the next command or an interactive bash should be executed
    """
    if key == getattr(Key, ARGS.next_key):
        global WAIT
        WAIT = False
    if key == getattr(Key, ARGS.interactive_key):
        interactive_bash()


DIRECTORIES = []


def cleanup():
    """
    Called on end of playbook or after Ctrl-C to clean up directories
    that are created with the playbook option *
    """
    global DIRECTORIES
    if DIRECTORIES:
        print("\n**** Training Cleanup! ****\n")
        if len(DIRECTORIES) > 1:
            print("Do you want to remove the following directories?: ")
        else:
            print("Do you want to remove the following directory?: ")
        for directory in DIRECTORIES:
            print(directory)
        i = input("\nRemove?: ")
        if i.lower() in ["y", "yes"]:
            print("\nI clean up the remains.")
            for directory in DIRECTORIES:
                os.system("rm -rf " + directory)
        else:
            print("\nI don't clean up.")
    print("\n**** End Of Training ****")
    if CONFIG["DEFAULT"]["message"].lower() == "true":
        print(
            "Remember to visit howto-kubernetes.info - The cloud native active learning community."
        )
        print(
            "Get free commercial usable trainings and playbooks for Git,"
            "Docker, Kubernetes and more!"
        )


def signal_handler(sig, frame):  # pylint: disable=W0613
    """
    Catch Ctrl-C and clean up the remains before exiting the cliplayer
    """
    print("\nYou stopped cliplayer with Ctrl+C!")
    cleanup()
    sys.exit(0)


WAIT = ""


def play():
    """
    Main function that runs a loop to play all commands of a existing playbook
    """

    signal.signal(signal.SIGINT, signal_handler)

    listener = Listener(on_press=on_press)
    try:
        listener.start()
    except MyException as e:
        print("Listener exception:" + e)

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
                    except pexpect.exceptions.ExceptionPexpect as e:
                        print(e)
                        print("Error in command: " + cmd)
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
                    except ValueError as e:
                        print(e)
                        print("Error in command: " + cmd)
                elif cmd[0] == "$":
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
                        cmd_2 = cmd_2.replace("VAR", child.before.strip())
                        print_slow(cmd_2.strip())
                        child = pexpect.pty_spawn.spawn(
                            cmd_2.strip(), encoding="utf-8", timeout=300
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
                    except ValueError as e:
                        print(e)
                        print("Error in command: " + cmd)
                    except pexpect.exceptions.ExceptionPexpect as e:
                        print(e)
                        print("Error in command: " + cmd)
                elif cmd[0] == "+":
                    interactive_bash()
                elif cmd[0] == "*":
                    try:
                        path = cmd[1:]
                        os.makedirs(path, exist_ok=True)
                        os.chdir(path)

                        global DIRECTORIES
                        dirpath = os.getcwd()
                        DIRECTORIES.append(dirpath)

                    except PermissionError as e:
                        print(e)
                        print("Error in command: " + cmd)
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
                    time.sleep(0.3)
                WAIT = True
            except MyException as e:
                print(e)
                print("Error in command: " + cmd)
    cleanup()


if __name__ == "__main__":
    play()
