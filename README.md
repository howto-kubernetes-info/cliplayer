# cliplayer
cliplayer helps to script shell based lectures or screencast tutorials. The player takes a playbook with shell commands that are executed live like you write them at this moment.

## Motivation
When you holding lectures or recording screencast you often need to devide your concentration between talking and typing at the same time. This cliplayer helps you to concentrate more on what you want to teach instead of what you need to type.

## Installation

`pip install cliplayer`

## Usage

    cliplayer [-h] [-p PROMPT] [-n NEXT_KEY] [-s SPEED] [-i INTERACTIVE_KEY] [playbook]

    -h
       Show the cli help
    
    -p PROMPT
       Change the PS1 prompt of the player
    
    -n NEXT_KEY
       Change the key that is used to execute the next command. Default: Scroll Lock

    -i INTERACTIVE_KEY
       key to press for a interactive bash as the next command. Default: Pause

    -s SPEED
       Set the max speed of typing one character. Default: 0.18
    
    playbook
       Path and name of the playbook to execute


## Config file

After the first usage, there is a configuration file in the home directory to manipulate the default settings.

    $ cat ~/.config/cliplayer/cliplayer.cfg
    [DEFAULT]
    prompt = \033[94mhowto-kubernetes.info \033[92m- \033[91mKubernetes Training \033[0m$
    playbook_name = ./playbook
    next_key = scroll_lock
    interactive_key = pause
    max_speed = 0.18

## Playbook Options

There are a few playbook options that control how and if a line in a playbook is executed. Use the defined characters as the first character in a line to use the available options.

1. "!"

    Comment in the playbook. The content of this line will not be shown or executed

    Example:

        ! This is a comment with some important information


1. " "  
    
    If no special character is used as the first character, the command is printed
    and executed as a normal non interactive shell command

    Examples:

        echo "Get free tutorials for Git, Docker, Kubernetes and other topics" > howto-kubernetes.info
        cat howto-kubernetes.info


1. "*"

    Create a directory and execute following commands in this directory

    Examples:

        * ../../git_tutorial
        * /tmp/git_tutorial


1. "_"

    Execute a command and get interactive control over it.
    This is used since you don't want or can't automate every command.

    Examples:

       _vim Readme.txt
       _man docker


1. "="
    
    A two part command. The first part is executed but not shown. The output of the first part, 
    replace a variable in the second non interactive command part. The two command parts are seperated by three
    dollar signs "$$$". The variable that changed is named VAR.

    Example:

        = cat .git/refs/heads/master | cut -c1-7 $$$ git cat-file -p VAR


1. "$"
    
    Same as the = option with the difference that you get interactive control over the second command.

    Example:

        = git rev-parse HEAD^^^ | cut -c1-7 $$$ git revert VAR


1. "+"
    
    Get an interactive bash prompt to execute commands that you don't want to automate.
    To exit an interactive session, press Ctrl - ] 

    Examples:

        +
        + You can write everything you want behind a +. It will not be shown or executed

## Links
[Official cliplayer video tutorial](https://howto-kubernetes.info/cliplayer/tutorial)

[Official playbook examples](https://howto-kubernetes.info/cliplayer/playbook_examples)

[Key codes for next_key and interactive_key options](https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key)

[How to create a prompt](https://wiki.archlinux.org/index.php/Bash/Prompt_customization)
