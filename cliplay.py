#!/usr/bin/env python
import yaml
import time
import random
from pynput.keyboard import Key, Listener
import pexpect
import sys

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

listener = Listener(on_press=on_press)
try:
    listener.start()
except MyException as e:
    print("Listener exception")
    pass

playbook = load_playbook()
for cmd in playbook:
    try:
        cmd = replace_vars(cmd).strip()
        if cmd[0] == "_":
            try: 
                cmd = cmd[1:]
                print_slow(cmd.strip())
                child = pexpect.pty_spawn.spawn(cmd.strip(), encoding='utf-8')
                child.interact(escape_character='\x1d', input_filter=None, output_filter=None)
                child.close()
            except:
               pass
        else:
            tmp = '/bin/bash -c "' + cmd.strip() + '"'
            print_slow(cmd.strip())
            child = pexpect.spawn(tmp, logfile=sys.stdout, encoding='utf-8')
            child.expect(pexpect.EOF)
            child.close()
        print(PROMPT, flush=True, end="")
        while(WAIT):
            pass
            time.sleep(0.3)
        WAIT=True
    except MyException as e:
        print(e)
