#!/usr/bin/env python
import subprocess
import time
import random
from pynput.keyboard import Key, Listener

PROMPT = "howto-kubernetes.info - Docker Tutorial $ "

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
    pass

print(PROMPT, end="")
scripts=open("screenplay", "r")

for script in scripts:
    try:
        tmp = script.split()
        if len(tmp) > 1:
            for var in tmp[1:]:
                key,value = var.split(":")
                globals().update({key:value})
        command = open("scripts/"+ tmp[0], "r") 
        cmd = command.read()
        cmd = replace_vars(cmd).strip()
        if SPEED == "fast":
            #print(cmd.strip())
            pass
        else:
            print_slow(cmd.strip())
        ## FIX ME! shell=True is a security risk, but nedded for commands like
        ## echo FROM ubuntu >> Dockerfile
        process = subprocess.run(cmd.strip(), shell=True, capture_output=True)
        print(process.stdout.decode('utf-8'))
        if len(process.stderr) > 0:
            print(process.stderr.decode('utf-8'))
        print(PROMPT, flush=True, end="")
        while(WAIT):
            pass
            time.sleep(0.3)
        WAIT=True
        SPEED = "slow"
    except MyException as e:
        print("AAAAAAA")
        print(e)
        pass
