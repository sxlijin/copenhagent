#!/usr/bin/env python

import readline, sys, argparse
from logger import *

import requests, json
from random import randint

import structs, navigation

##### GLOBAL VARIABLES <START> #####

### NOTE: internal state variables are tracked in [AI FUNCTIONS]

### verbosity controls
QUIET = False
SILENT = True
dump_json_state = False


##### GLOBAL VARIABLES <END> #####

HOSTNAME='localhost'

def api_url_for(path, query=''):
    """Return full concatenated API URL to request from $path and $query."""
    try:
        if path[0] == '/': path = path[1:]
        if path[-1] == '?': path = path[:-1]
        if query[0] == '?': query = query[1:]
    except IndexError: pass
    return 'http://{hostname}:3000/api/{path}?{query}'.format(
        hostname=HOSTNAME,
        path=path,
        query=query
        )

def list_reprs(iterable):
    """Returns list of elements of $iterable as repr($elem1), ... ."""
    return ', '.join([repr(elem) for elem in iterable])
class CustomProgramError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)
class Agent:
    """Controls an agent in the copenhagent environment."""
    
    def __init__(self, token=None, name=None, shell=None):
        """Take control of the agent."""
        if (token, name).count(None) != 1: 
            raise ValueError(
                'Must construct Agent() with either $token or $name (not both).'
            )

        self.shell = shell
        
        self.agent_token = None
        self.header = {}
        self.location = None
        self.n_credits = 0
        self.n_actions = 0

        if token == None:
            token = self.create_new(name)
        else:
            self.update_with_agent_token(token)

        self.init_control()
#del#
#del#    def get_header(self):
#del#        """Return the header {} containing the agent token."""
#del#        return self.header

    def create_new(self, name):
        """Create a new agent named $name and return its agent token."""
        print 'creating new %s' % name
        return self.poll_api(
            api_url_for('environment/connect', 'name=%s' % name)
            ).json()['agentToken']
    
    def init_control(self, msg=None):
        """Executes agent/say(), says 'python connected'."""
        if msg == None:  msg = 'python connected'
        self.poll_api_say(msg)
 
    def drop_control(self, msg=None):
        """Executes agent/say(), says 'python disconnected'."""
        if msg == None:  msg = 'python disconnected'
        self.poll_api_say(msg)
    
    def update_with(self, r):
        """Take a <requests> object and update the internal state."""
        if r.status_code == 401 and r.json()['code'] == 'Unauthorized':
            raise ValueError(r.json()['message'])
        r = r.json()
        if 'agentToken' in r:
            self.update_with_agent_token(r['agentToken'])
        if 'action' in r:
            self.update_with_action(r['action'])
        if 'state' in r:
            self.update_with_state(r['state'])

    def update_with_agent_token(self, token):
        self.agent_token = token
        self.header = {u'agentToken':self.agent_token}

    def update_with_action(self, r):
        self.n_credits += 0
        self.n_actions += 1

    def update_with_state(self, r):
        r = r['agents'][self.agent_token]
        self.location = r['locationId'] if 'locationId' in r else self.location
        self.n_credits = r['utility']
        self.n_actions = r['actionsPerformed']
    
    def poll_api_say(self, msg):
        return self.poll_api(
            api_url_for('environment/agent/say', 'message=%s' % msg))

    def poll_api(self, api_url):
        """Request $api_url with $self.agent_token specified in header."""
        #print 'requesting %s with agentToken %s' %(api_url, self.agent_token)
        r = requests.get(api_url, headers=self.header)
        self.update_with(r)
        return r

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

    nav_agent = logger.Logger(nav_setup).f_output()
    logger.Logger(nav_solve) 
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

    opened = Shell(token=token) if name == None else Shell(name=name)
    try:
        opened.run(parser.parse_args().command.strip())
    except AttributeError:
        opened.run()

    sys.exit(0)



if __name__ == "__main__":
    main()

##### COMMAND LINE INTERPRETERS <END> #####
