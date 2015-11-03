#! /usr/bin/env python

import requests

from logger import *

class Agent:
    """Controls an agent in the copenhagent environment."""

    def __init__(self, token=None, name=None, hostname=None):
        """
        Constructs an Agent() used to control an <agent> in the copenhagent
        environment, using exactly either the <agentToken> of an existing
        <agent> or a specified $name to create a new <agent>.
        """

        self.HOSTNAME = hostname if hostname != None else 'localhost'

        if (token, name).count(None) != 1: 
            raise ValueError(
                'Must construct Agent() with either $token or $name (not both).'
            )
        
        if token == None:
            self.agent_token = self.poll_api('environment/connect?name=' + name)
        else:
            self.agent_token = token
            
        self.agent_token = token
        self.header = {u'agentToken':self.agent_token}

        self.location = None
        self.n_credits = 0
        self.n_actions = 0

        # this no longer costs an action
        # the only cost is the time it takes to generate the <FullResponse>
        self.update_with(self.init_control())


    def init_control(self):
        """
        Executes environment/agent/say('python connected').
        Returns the generated <requests> object.
        """
        return self.say('python connected')
 

    def drop_control(self, msg=None):
        """
        Executes environment/agent/say('python disconnected').
        Returns the generated <requests> object.
        """
        return self.say('python disconnected')
    

    def update_with(self, r):
        """Take a <requests> object and update the internal state."""
        if r.status_code == 401 and r.json()['code'] == 'Unauthorized':
            raise ValueError(r.json()['message'])
        r = r.json()

        if 'action' in r:   self.update_with_action(r['action'])
        if 'state' in r:    self.update_with_state(r['state'])


    def update_with_action(self, r):
        self.n_credits += 0
        self.n_actions += 1


    def update_with_state(self, r):
        r = r['agents'][self.agent_token]
        self.location = r['locationId'] if 'locationId' in r else self.location
        self.n_credits = r['utility']
        self.n_actions = r['actionsPerformed']
    

    def say(self, msg):
        """
        Polls the API at environment/agent/say() with message=$msg.
        
        Returns the <requests> received from said API query.
        """
        return self.poll_api('environment/agent/say?message=%s' % msg)


    def poll_api(self, api_path):
        """
        Polls the API at $api_path to control the <agent> and updates internal
        state appropriately.

        Returns the <requests> received from said API query.
        """
        r = requests.get(api_url(api_path), headers=self.header)
        self.update_with(r)
        return r
    

    def api_url(path, query=''):
        """Returns properly formed URL from a $path and $query."""
        try:
            if path[0] == '/': path = path[1:]      # trim leading /
            if path[-1] == '?': path = path[:-1]    # trim trailing /
            if query[0] == '?': query = query[1:]   # trim leading ?
        except IndexError: pass

        return 'http://{hostname}:3000/api/{path}?{query}'.format(
            hostname=self.HOSTNAME,
            path=path,
            query=query
            )