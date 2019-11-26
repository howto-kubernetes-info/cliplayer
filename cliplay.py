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

parser = argparse.ArgumentParser()
parser.add_argument(
    "-p",
    "--prompt",
    default="\033[94mhowto-kubernetes.info \033[92m- \033[91mKubernetes Training \033[0m$ ",
    help="prompt to use with playbook. Build it like a normal $PS1 prompt.",
)
parser.add_argument(
    "-n",
    "--next-key",
    default="scroll_lock",
    help="key to press for next command. Default: scroll_lock",
)
parser.add_argument(
    "playbook",
    nargs="?",
    default="./playbook",
    help="path and name to playbook. Default: ./playbook",
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


WAIT = True


class MyException(Exception):
    pass


def on_press(key):
    # if key == Key.shift_l or key == Key.shift_r:
    if key == Key.scroll_lock:
        global WAIT
        WAIT = False


workdir = ""


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


signal.signal(signal.SIGINT, signal_handler)

listener = Listener(on_press=on_press)
try:
    listener.start()
except MyException as e:
    print("Listener exception")
    pass

playbook = load_playbook()
for cmd in playbook:

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
                    escape_character="\x1d", input_filter=None, output_filter=None
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
                cmd = '/bin/bash --rcfile <(echo "PS1=' + "'" + PROMPT + "'" + '")'
                print("\033[0K\r", flush=True, end="")
                child = pexpect.pty_spawn.spawn(
                    "/bin/bash", ["-c", cmd], encoding="utf-8", timeout=300
                )
                child.setwinsize(int(rows), int(columns))
                child.interact(
                    escape_character="\x1d", input_filter=None, output_filter=None
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
                workdir = path
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
