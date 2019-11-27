# cliplayer
cliplayer helps to script shell based lectures or screencast tutorials. The player takes a playbook with shell commands that are executed live like you write them at this moment.

There are a few playbook options that control how and if a line in a playbook is executed. Use the defined characters as the first character in a line to use the available options.

## Motivation
When you holding lectures or recording screencast you often need to devide your concentration between talking and typing at the same time. This cliplayer helps you to concentrate more on what you want to teach instead of what you need to type.

## Installation

`pip install cliplayer`

## Usage

`cliplayer`

Hint: You need a playbook in the directory you execute the cliplayer command

You execute the next line in the playbook by pressing the "scroll lock" key

You can stop the playbook by pressing Ctrl - C 

##Playbook Options

1. " "  
    
    If no special character is used as the first character, the command is printed
    and executed as a normal non interactive shell command

    Examples:

        `echo "Get free tutorials for Git, Docker, Kubernetes and other topics" > howto-kubernetes.info`
        `cat howto-kubernetes.info`


1. "*"

    Create a directory and execute following commands in this directory

    Examples:

        `* ../../git_tutorial`
        `* /tmp/git_tutorial`


1. "_"

    Execute a command and get interactive control over it.
    This is used since you don't want or can't automate every command.

    Examples:

       `_vim Readme.txt`
       `_man docker`


1. "="
    
    A two part command. The first part is executed but not shown. The output of the first part, 
    replace a variable in the second non interactive command part. The two command parts are seperated by three
    dollar signs "$$$". The variable that changed is named VAR.

    Example:

        `= cat .git/refs/heads/master | cut -c1-7 $$$ git cat-file -p VAR`


1. "+"
    
    Get an interactive bash prompt to execute commands that you don't want to automate.
    To exit an interactive session, press Ctrl - ] 

    Examples:

        `+`
        `+ You can write everything you want behind a +. It will not be shown or executed`


1. "!"

    Comment in the playbook. The content of this line will not be shown or executed

    Example:

        `! This is a comment with some important informations`
