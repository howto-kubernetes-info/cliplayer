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

PROMPT = "\033[94mhowto-kubernetes.info - \033[91mDocker Tutorial \033[0m$ "

def load_playbook():
    playbook = open("playbook", "r")
    commands = []
    for command in playbook:
        commands.append(command.strip()) 
    return(commands)

def replace_vars(string):
    keys = globals().keys()
    for key in list(keys):
        if key.isupper():
            string = string.replace("__" + key + "__", str(globals().get(key)))
    return string

def print_slow(str):
    for letter in str:
        print(letter, flush=True, end="")
        time.sleep(random.uniform(0.0,0.18))
    time.sleep(.1)
    print("")

WAIT=True

class MyException(Exception): pass

def on_press(key):
    if key == Key.shift_l or key == Key.shift_r:
        global WAIT
        WAIT=False

workdir = ""
def signal_handler(sig, frame):
    print('\nYou stopped the tutorial with Ctrl+C!')
    print("Tutorial Cleanup!")
    print("Do you want to remove the following directory? ")
    dirpath = os.getcwd()
    print(dirpath)
    i = input("Remove?: ")
    if i.lower() in ['y', 'yes']:
        print("I clean up the remains.")
        os.system('rm -rf '+ dirpath )
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

    rows, columns = subprocess.check_output(['stty', 'size']).decode().split()

    try:
        cmd = replace_vars(cmd).strip()
        if cmd[0] == "_":
            try: 
                cmd = cmd[1:]
                print_slow(cmd.strip())
                child = pexpect.pty_spawn.spawn(cmd.strip(), encoding='utf-8', timeout=300)
                child.setwinsize(int(rows), int(columns))
                child.interact(escape_character='\x1d', input_filter=None, output_filter=None)
                child.close()
                print(PROMPT, flush=True, end="")
                WAIT=True
            except:
               pass
        elif cmd[0] == "=":
            try: 
                cmd = cmd[1:]
                cmd_1, cmd_2 = cmd.split("$$$")
                child = pexpect.spawn('/bin/bash', ['-c', cmd_1.strip()], logfile=None, encoding='utf-8', timeout=300)
                child.setwinsize(int(rows), int(columns))
                child.expect(pexpect.EOF)
                child.close()
                cmd = cmd_2.replace("VAR",child.before.strip())
                print_slow(cmd.strip())
                child = pexpect.spawn('/bin/bash', ['-c', cmd.strip()], logfile=sys.stdout, encoding='utf-8', timeout=300)
                child.setwinsize(int(rows), int(columns))
                child.expect(pexpect.EOF)
                child.close()
                print(PROMPT, flush=True, end="")
            except:
               pass
        elif cmd[0] == "+":
            try: 
                cmd = '/bin/bash --rcfile <(echo "PS1=' + "'" + PROMPT + "'" +'")'
                print("\033[0K\r", flush=True, end="")
                child = pexpect.pty_spawn.spawn('/bin/bash', ['-c', cmd], encoding='utf-8', timeout=300)
                child.setwinsize(int(rows), int(columns))
                child.interact(escape_character='\x1d', input_filter=None, output_filter=None)
                child.close()
                WAIT=True
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
            child = pexpect.spawn('/bin/bash', ['-c', cmd.strip()], logfile=sys.stdout, encoding='utf-8', timeout=300)
            child.setwinsize(int(rows), int(columns))
            child.expect(pexpect.EOF)
            child.close()
            print(PROMPT, flush=True, end="")
        time.sleep(1)
        while(WAIT):
            pass
            time.sleep(0.3)
        WAIT=True
    except MyException as e:
        print(e)
