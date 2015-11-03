#!/usr/bin/env python

import readline, sys, argparse

import requests, json
from random import randint

import shell, structs, navigation
from logger import *


##### GLOBAL VARIABLES <START> #####

### NOTE: internal state variables are tracked in [AI FUNCTIONS]

### verbosity controls
QUIET = False
SILENT = True
dump_json_state = False


##### GLOBAL VARIABLES <END> #####

def list_reprs(iterable):
    """Returns list of elements of $iterable as repr($elem1), ... ."""
    return ', '.join([repr(elem) for elem in iterable])

class CustomProgramError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
### NAVIGATION

def navigation_ai(shell):
    debug=False
    debug=True
    
    def print_timetable(text):
        print_flag = True
        if print_flag:  print text

    def nav_setup():
        nav_inst = navigation.Instance(shell, debug=debug)
        nav_agent = navigation.Agent(nav_inst, debug=debug)
        return nav_agent

    def nav_solve():
        return nav_agent.nav_generic_breadth_first()
#del#        return nav_agent.nav_generic_depth_first()
#del#        return nav_agent.nav_generic_greedy_best_first()

    nav_agent = log(nav_setup)[1]
    log_runtime_of(nav_solve) 
    nav_agent.cmd_nav_leave()

##### AI FUNCTIONS <END> #####





#### COMMAND LINE INTERPRETERS <START> #####

def main():
    parser = argparse.ArgumentParser(
        description = ' '.join((
            'Spawns an interactive shell with which you can control an agent',
            'in the copenhagent environment. Must specify either --new or',
            '--agent when calling the script; if neither or both are',
            'specified, program will immediately exit.'
        ))
    )

    parser.add_argument(
        '--new', 
        metavar='<name>', 
        help='create a new agent with <name> and control it')
    parser.add_argument(
        '--agent',
        metavar='<agentToken>',
        help='control an existing agent with <agentToken>')
    parser.add_argument(
        '--command',
        metavar='<command>',
        help='send command to shell and close immediately after running')
    
    (name, token) = (parser.parse_args().new, parser.parse_args().agent)

    if (name, token).count(None) != 1:
        parser.print_help()
        sys.exit(0)

    opened = shell.Shell(token, name)
    try:
        opened.run(parser.parse_args().command.strip())
    except AttributeError:
        opened.run()

    sys.exit(0)



if __name__ == "__main__":
    main()

##### COMMAND LINE INTERPRETERS <END> #####
