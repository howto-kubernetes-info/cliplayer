#!/usr/bin/env python

"""
cliplayer: A module to play playbooks with Bash commands as if they are being typed in real-time.
"""

import argparse
import configparser
import codecs
import os
import signal
import subprocess
import sys
import tty
import termios
import select
import time
import random
from shutil import copyfile
from pathlib import Path
import pexpect

KEY_NAME_MAPPING = {
    'ENTER': '\n',
    'RETURN': '\n',
    'END': '\x1b[F',
    'HOME': '\x1b[H',
    'INSERT': '\x1b[2~',
    'DELETE': '\x1b[3~',
    'PAGE_UP': '\x1b[5~',
    'PAGE_DOWN': '\x1b[6~',
    'UP': '\x1b[A',
    'DOWN': '\x1b[B',
    'LEFT': '\x1b[D',
    'RIGHT': '\x1b[C',
    'ESC': '\x1b',
    'SPACE': ' ',
    'TAB': '\t',
    'BACKSPACE': '\x7f',
}

def map_key(key_str):
    """
    Maps a key string from the configuration to its corresponding escape sequence or character.
    Supports named keys and single character keys.
    """

    key_str_upper = key_str.upper()
    if key_str_upper in KEY_NAME_MAPPING:
        return KEY_NAME_MAPPING[key_str_upper]
    if len(key_str) == 1:
        return key_str
    raise ValueError(f"Unknown key: {key_str}")

class KeyCapture:
    """
    Captures key presses from the user.
    """

    def __init__(self):
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setcbreak(self.fd)
        self.key_pressed = None

    def get_key(self):
        """
        Get the key pressed by the user.
        """

        dr = select.select([sys.stdin], [], [], 0.05)
        if dr:
            c1 = sys.stdin.read(1)
            if c1 == '\x1b':
                # Escape sequence
                seq = c1
                # Read additional characters
                while True:
                    c = sys.stdin.read(1)
                    seq += c
                    # Break if no more characters are coming
                    if c.isalpha() or c == '~':
                        break
                self.key_pressed = seq
            else:
                self.key_pressed = c1
            return self.key_pressed
        return None

def get_arguments():
    """
    Get command line arguments and return them.
    """
    home = str(Path.home())
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
        "-i",
        "--interactive-key",
        default=config["DEFAULT"]["interactive_key"],
        help="key to press for a interactive bash as the next command. Default: "
        + config["DEFAULT"]["interactive_key"],
    )
    parser.add_argument(
        "-b",
        "--base-speed",
        default=config["DEFAULT"]["base_speed"],
        help="base speed to type one character. Default: "
        + config["DEFAULT"]["base_speed"],
    )
    parser.add_argument(
        "-m",
        "--max-speed",
        default=config["DEFAULT"]["max_speed"],
        help="max speed to type one character. Default: "
        + config["DEFAULT"]["max_speed"],
    )
    parser.add_argument(
        "playbook",
        nargs="?",
        default=config["DEFAULT"]["playbook_name"],
        help="path and name to playbook. Default: "
        + config["DEFAULT"]["playbook_name"],
    )
    return parser.parse_args()

def create_config_file():
    """
    Create a config file in the home directory if it is not there already
    """
    home = str(Path.home())
    if not os.path.isfile(home + "/.config/cliplayer/cliplayer.cfg"):
        os.makedirs(home + "/.config/cliplayer/", exist_ok=True)
        copyfile(
            sys.prefix + "/config/cliplayer.cfg",
            home + "/.config/cliplayer/cliplayer.cfg",
        )

def execute_interactive_command(cmd):
    """
    Function to execute an interactive command and return the output of the command if there is some
    """
    try:
        rows, columns = subprocess.check_output(["stty", "size"]).decode().split()
        child = pexpect.pty_spawn.spawn(cmd.strip(), encoding="utf-8", timeout=300)
        child.setwinsize(int(rows), int(columns))
        child.interact(
            escape_character="\x1d", input_filter=None, output_filter=None,
        )
        child.close()
        return child.before

    except pexpect.exceptions.ExceptionPexpect as e:
        print(e)
        print("Error in command: " + cmd)
        return None

def execute_command(cmd, logfile):
    """
    Function to execute a non-interactive command and
    return the output of the command if there is some
    """
    try:
        rows, columns = subprocess.check_output(["stty", "size"]).decode().split()
        child = pexpect.spawn(
            "/bin/bash",
            ["-c", cmd.strip()],
            logfile=logfile,
            encoding="utf-8",
            timeout=300,
        )
        child.setwinsize(int(rows), int(columns))
        child.expect(pexpect.EOF)
        child.close()
        return child.before
    except pexpect.exceptions.ExceptionPexpect as e:
        print(e)
        print("Error in command: " + cmd)
        return None

class MyException(Exception):
    """
    Basic Exception
    """

class CliPlayer: # pylint: disable=too-few-public-methods
    """
    Class to play playbooks with Bash commands as if they are being typed in real-time.
    """
    wait = True
    directories = []

    def __init__(
            self,
            prompt,
            base_speed,
            max_speed,
            next_key,
            interactive_key,
            show_message,
            playbook,
    ):
        """
        Initializes the CliPlayer with the provided configurations.
        """
        self.prompt = prompt
        self.base_speed = base_speed
        self.max_speed = max_speed

        try:
            self.next_key = map_key(next_key)
        except ValueError as e:
            print(f"Invalid next_key: {next_key}. {e}")
            sys.exit(1)
        try:
            self.interactive_key = map_key(interactive_key)
        except ValueError as e:
            print(f"Invalid interactive_key: {interactive_key}. {e}")
            sys.exit(1)

        self.playbook = playbook
        self.show_message = show_message
        self.key_capture = KeyCapture()
        self.wait = True
        self.directories = []

    def load_playbook(self):
        """
        Loading commands from a playbook and returning a list with the commands.
        """
        try:
            playbook = open(self.playbook, "r",  encoding="utf-8")
        except FileNotFoundError:
            print("You need to provide a playbook")
            sys.exit(0)
        commands = []
        for command in playbook:
            commands.append(command.strip())
        return commands

    def print_slow(self, string):
        """
        Printing characters like you type it at the moment without returning anything
        """
        for letter in string:
            print(letter, flush=True, end="")
            time.sleep(random.uniform(float(self.base_speed), float(self.max_speed)))
        time.sleep(0.1)
        print("\r", flush=True)

    def create_directory(self, path):
        """
        Function to create a directory and change the working directory to it
        """
        try:
            os.makedirs(path.strip(), exist_ok=True)
            os.chdir(path.strip())

            dirpath = os.getcwd()
            self.directories.append(dirpath)

        except PermissionError as e:
            print(e)
            print("Error in command: *" + path)

    def interactive_bash(self):
        """
        Start a new bash and give interactive control over it
        """
        try:
            rows, columns = subprocess.check_output(["stty", "size"]).decode().split()
            cmd = '/bin/bash --rcfile <(echo "PS1=' + "'" + self.prompt + "'" + '")'
            print("\033[0K\r", flush=True, end="")
            child = pexpect.pty_spawn.spawn(
                "/bin/bash", ["-c", cmd], encoding="utf-8", timeout=300
            )
            child.setwinsize(int(rows), int(columns))
            child.interact(
                escape_character="\x1d", input_filter=None, output_filter=None,
            )
            child.close()
            self.wait = True
            time.sleep(1.0)
        except pexpect.exceptions.ExceptionPexpect as e:
            print(e)

    def on_press(self, key):
        """
        Called on every key press to check if the next command
        or an interactive bash should be executed
        """

        #print(f"DEBUG: on_press called with key: {repr(key)}")  # Debug-Ausgabe
        if key == self.next_key:
            self.wait = False
        if key == self.interactive_key:
            self.interactive_bash()

    def cleanup(self):
        """
        Called on end of playbook or after Ctrl-C to clean up directories
        that are created with the playbook option *
        """

        os.system("stty echo")
        if self.directories:
            print("\r\n**** Training Cleanup! ****\n")
            if len(self.directories) > 1:
                print("Do you want to remove the following directories?: ")
            else:
                print("Do you want to remove the following directory?: ")
            for directory in self.directories:
                print(directory)
            i = input("\nRemove?: ")
            if i.lower() in ["y", "yes"]:
                print("\nI clean up the remains.")
                for directory in self.directories:
                    os.system("rm -rf " + directory)
            else:
                print("\r\nI don't clean up.")

        print("\r\n**** End Of Training ****\r\n")

        if self.show_message.lower() == "true":
            print(
                "Remember to visit howto-kubernetes.info - "
                "The cloud native active learning community."
            )
            print(
                "Get free commercial usable trainings and playbooks for Git,"
                " Docker, Kubernetes and more!"
            )

    def signal_handler(self, sig, frame):  # pylint: disable=W0613
        """
        Catch Ctrl-C and clean up the remains before exiting the cliplayer
        """

        print("\r\nYou stopped cliplayer with Ctrl+C!")
        self.cleanup()
        sys.exit(0)

    def play(self):
        """
        Main function that runs a loop to play all commands of an existing playbook
        """

        playbook = self.load_playbook()
        os.system("stty -echo")
        print(self.prompt, flush=True, end="")

        while self.wait:
            key = self.key_capture.get_key()
            if key is not None:
                #print("key: " + str(ord(key)))
                self.on_press(key)
            time.sleep(0.05)

        for cmd in playbook:
            if len(cmd.strip()) != 0:
                try:
                    if cmd[0] == "_":
                        cmd = cmd[1:]

                        self.print_slow(cmd.strip())
                        execute_interactive_command(cmd)

                        print(self.prompt, flush=True, end="")
                        self.wait = True

                    elif cmd[0] == "!":
                        continue

                    elif cmd[0] == "=":
                        cmd_1, cmd_2 = cmd[1:].split("$$$")
                        output = execute_command(cmd_1.strip(), logfile=None)
                        cmd_2 = cmd_2.replace("VAR", output.strip())

                        self.print_slow(cmd_2.strip())
                        execute_command(cmd_2, logfile=sys.stdout)

                        print(self.prompt, flush=True, end="")
                        self.wait = True

                    elif cmd[0] == "$":
                        cmd_1, cmd_2 = cmd[1:].split("$$$")
                        output = execute_command(cmd_1.strip(), logfile=None)
                        cmd_2 = cmd_2.replace("VAR", output.strip())

                        self.print_slow(cmd_2.strip())
                        execute_interactive_command(cmd_2.strip())

                        print(self.prompt, flush=True, end="")
                        self.wait = True

                    elif cmd[0] == "+":
                        self.interactive_bash()
                        self.wait = True

                    elif cmd[0] == "*":
                        self.create_directory(cmd[1:])
                        self.wait = False

                    else:
                        self.print_slow(cmd.strip())
                        execute_command(cmd.strip(), logfile=sys.stdout)
                        print(self.prompt, flush=True, end="")
                        self.wait = True
                    time.sleep(1)

                    while self.wait:
                        key = self.key_capture.get_key()
                        if key:
                            #print("key: " + str(key))
                            self.on_press(key)
                        time.sleep(0.05)
                    self.wait = True

                except MyException as e:
                    print(e)
                    print("Error in command: " + cmd)
        self.cleanup()

def main():
    """
    Main function that configures and runs the cliplayer
    """

    create_config_file()

    args = get_arguments()

    home = str(Path.home())
    config = configparser.ConfigParser(interpolation=None)
    config.read(home + "/.config/cliplayer/cliplayer.cfg")

    player = CliPlayer(
        prompt=args.prompt,
        base_speed=args.base_speed,
        max_speed=args.max_speed,
        next_key=args.next_key,
        interactive_key=args.interactive_key,
        show_message=config["DEFAULT"]["message"],
        playbook=args.playbook,
    )

    signal.signal(signal.SIGINT, player.signal_handler)

    player.play()

if __name__ == "__main__":
    main()
