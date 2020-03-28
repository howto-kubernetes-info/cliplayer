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
    Function to execute a interactive command and return the output of the command if there is some
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


class CliPlayer:
    """
    Class to play playbooks with bash commands like typing them at the moment
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
        self.prompt = prompt
        self.base_speed = base_speed
        self.max_speed = max_speed
        self.next_key = next_key
        self.interactive_key = interactive_key
        self.playbook = playbook
        self.show_message = show_message

    def load_playbook(self):
        """
        Loading commands from a playbook and returning a list with the commands.
        """
        try:
            playbook = open(self.playbook, "r")
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
        print("")

    def create_directory(self, path):
        """
        Function to create a directory and change the working directory to it
        """
        try:
            os.makedirs(path, exist_ok=True)
            os.chdir(path)

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
        if key == getattr(Key, self.next_key):
            self.wait = False
        if key == getattr(Key, self.interactive_key):
            self.interactive_bash()

    def cleanup(self):
        """
        Called on end of playbook or after Ctrl-C to clean up directories
        that are created with the playbook option *
        """
        os.system("stty echo")
        if self.directories:
            print("\n**** Training Cleanup! ****\n")
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
                print("\nI don't clean up.")
        print("\n**** End Of Training ****")
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
        print("\nYou stopped cliplayer with Ctrl+C!")
        self.cleanup()
        sys.exit(0)

    def start_key_listener(self):
        """
        Start to listen for key presses and Ctrl-C sequence
        """
        signal.signal(signal.SIGINT, self.signal_handler)

        listener = Listener(on_press=self.on_press)
        try:
            listener.start()
        except MyException as e:
            print("Listener exception:" + e)

    def play(self):
        """
        Main function that runs a loop to play all commands of a existing playbook
        """
        self.start_key_listener()

        playbook = self.load_playbook()
        os.system("stty -echo")
        print(self.prompt, flush=True, end="")

        while self.wait:
            time.sleep(0.3)

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

                        # except ValueError as e:
                        #    print(e)
                        #    print("Error in command: " + cmd)

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
                        time.sleep(0.3)

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

    player.play()


if __name__ == "__main__":
    main()
