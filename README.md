# cliplayer
cliplayer helps to script shell based lectures or screencast trainings. The player takes a playbook with shell commands that are executed live like you write them at this moment. 

## Motivation
When holding lectures or recording screencast you often need to devide your attention between talking and typing at the same time. This cliplayer helps you to concentrate more on what you want to teach instead of what you need to type.

## Hint
Corona Edition - howto-kubernetes.info is not live at the moment

## Installation

`pip install cliplayer`

## Usage

    cliplayer [-h] [-p PROMPT] [-n NEXT_KEY] [-i INTERACTIVE_KEY] 
                   [-b BASE_SPEED] [-m MAX_SPEED]
                   [playbook]

    -h
       Show the cli help
    
    -p PROMPT
       Change the PS1 prompt of the player
    
    -n NEXT_KEY
       key to press to execute the next command. Default: Enter

    -i INTERACTIVE_KEY
       key to press for a interactive bash as the next command. Default: End

    -b BASE_SPEED
       Set the base speed of typing one character. Default: 0.03
    
    -m MAX_SPEED
       Set the max speed of typing one character. Default: 0.15

    playbook
       Path and name of the playbook to execute


## Config file

After the first usage, there is a configuration file in the home directory to manipulate the default settings.

    $ cat ~/.config/cliplayer/cliplayer.cfg
    [DEFAULT]
    prompt = \033[94mhowto-kubernetes.info \033[92m- \033[91mKubernetes Training \033[0m$
    playbook_name = ./playbook
    next_key = enter
    interactive_key = end
    base_speed = 0.03
    max_speed = 0.15

## Playbook Options

There are a few playbook options that control how and if a line in a playbook is executed. Use the defined characters as the first character in a line to use the available options.

1. "!"

    Comment in the playbook. The content of this line will not be shown or executed.

    Example:

        ! This is a comment with some important information


1. " "
    
    If no special character is used as the first character, the command is printed
    and executed as a normal non interactive shell command.

    Examples:

        echo "Get playbooks for Git, Docker, Kubernetes and other topics" > howto-kubernetes.info
        cat howto-kubernetes.info


1. "*"

    Create a directory and execute the following playbook commands in this directory. These directories can be removed at the end of the training or stopping the playbook with Ctrl-C.

    Examples:

        * ../../git_training
        * /tmp/git_training


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
        + You can write everything you want behind a +. It will not be shown or executed.


## Special keys

1. "Enter"

    To execute the next command of the playbook, press the "Enter" key.

    
1. "End"

    To get a interactive bash, press the "End" key after a playbook command.


1. "Ctrl-]"

    To exit a interactive bash sequence, press "Ctrl-]".


1. "Ctrl-C"

    To exit the cliplayer before the playbook is finished, press "Ctrl-C". 



Hint
> The keys are chosen because most notebooks have them. If your you don't like the default keys, reconfigure the player with the configuration file or while starting cliplayer.


## Links
[Key codes for next_key and interactive_key options](https://pynput.readthedocs.io/en/latest/keyboard.html#pynput.keyboard.Key)

[How to create a prompt](https://wiki.archlinux.org/index.php/Bash/Prompt_customization)
