#!/usr/bin/env python

import readline, sys, argparse
import requests, json
import time
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

def log_error(e):
    if isinstance(e, Exception): e = (type(e).__name__, e.message.lower())
    print '[ ERROR: %12.12s ] %s' % e

class CustomProgramError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

    
class Shell:
    """Open a shell to control agents in the copenhagent environment."""

    api_commands = {
        'map': {
            'enter': {},
            'metro': {
                'direction': ['cw', 'ccw']
            },
            'bike': {
                'locationId':
                [   'dis', 'koedbyen', 'frederiksberg', 'louises',
                    'noerrebrogade', 'jaegersborggade', 'parken', 
                    'langelinie', 'christianshavn', 'bryggen', 'folkentinget' ]
            },
            'leave': {}
        },
        'navigation': {
            'enter': {},
            'lane': {
                'direction':['left', 'stay', 'right']
            },
            'leave': {}
        },
        'papersoccer': {
            'enter': {},
            'play': {
                'direction': ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']
            },
            'leave': {}
        }
    }


    def __init__(self, token=None, name=None):
        """Initialize the shell."""
        if (token, name).count(None) != 1: sys.exit(0)
        #if token == None: token = 'c838f91f0fdcaba5946b5f02f67ce1b2'
        self.active_agent = None
        self.set_active_agent(token, name)

    def run(self, cmd=None):
        """Run the shell. If $cmd is specified, attempts to run it and 
        immediately exists after running."""
        while True:
            usi = raw_input('disai> ') if cmd == None else cmd
            if usi == 'exit':  break
            try:
                self.try_command(usi)
            except (AttributeError, ValueError) as e:
                log_error(e)
            if cmd != None: break

    def set_active_agent(self, token=None, name=None):
        try:
            if self.active_agent != None: self.active_agent.drop_control()
            self.active_agent = Agent(token, name)
        except (AttributeError, ValueError) as e:
            log_error(e)
    
    def try_command(self, argstr):
        """
        Return <requests> from executing shell command $argstr.
        If executing a repeated command, returns the last <requests>."""
        # assume $argstr is a <str> but allow it to be a <list> as well
        try:
            argv = argstr.split()
        except AttributeError:
            argv = argstr
            argstr = ' '.join(argv)

        try:
            # repeat command $argv[0] times if $argv[0] is a number
            # execute command if it passes verification
            #   verification fills in endpoints and params if none given
            #   also reformats $argv if necessary
            if argv[0].isdigit():
                n = int(argv.pop(0))
                # TODO: adjust so that it doesn't repeat a bad command n times
                #if self.verify_api_command(argv):
                #    for i in range(n): r = self.try_command(argv)
                #    return r
                #else: return None
                for i in range(n): r = self.try_command(argv)
                return r
            try:
                self.run_custom_program(argstr)
            except CustomProgramError:
                if self.verify_api_command(argv):  
                    return self.do_api_command(argv)
        except IndexError:
            return None

    def verify_api_command(self, argv):
        """
        Verify $argv is a sound shell command, i.e. has format

            <command> <endpoint> <query>

        where <query> takes form <param>=<value>.

        If <endpoint> or <query> are omitted, prompt user for
        <endpoint> or <value>s for each <param> as appropriate.
        """

        
        api_commands = self.api_commands

        def log_unk(msg): log_error(('unrecognized', msg))

        # verify <command>
        command = argv[0]

        # FAIL if $command is not valid
        if command not in api_commands:
            log_unk('%s not recognized as <command>' % repr(command))
            return False

        # verify <endpoint>; prompt if none provided
        try:
            endpoint = argv[1]
        except IndexError:
            # accept <query> if specified
            argv.extend(raw_input(
                'enter a %s endpoint (%s): ' % (
                    command, list_reprs(api_commands[command]))
            ).split())
        finally:
            endpoint = argv[1]

        # FAIL if $endpoint is not valid
        if endpoint not in api_commands[command]:
            log_unk('%s not recognized as <endpoint> for %s' % (
                repr(endpoint), repr(command)))
            return False
        
        # verify <query>; prompt if none provided and <query> required
        # NOTE: <param>, '=', and <value> can be separated by spaces now
        queries = argv[2:]
        queries = ' '.join(queries).replace('=', ' = ').split()
        queries = ' '.join(queries).replace(' = ', '=').split()
        try:
            # handle trailing '='s
            if queries[-1] == '=' and len(queries) > 1: 
                queries.pop(-1)
                queries[-1] += '='
        except IndexError: 
            pass

        queries = { param:val 
                    for [param,val] 
                    in [q.split('=') if q.count('=') == 1 else [q,'']
                        for q in queries ]}

        # prompt for <value>s if no <query> provided
        if len(queries) == 0 and len(api_commands[command][endpoint]) != 0:
            for param in api_commands[command][endpoint]:
                queries[param] = raw_input(
                    'enter a %s value (%s): %s=' % (
                        param,
                        list_reprs(api_commands[command][endpoint][param]),
                        param) )

        # FAIL if a <value> is not valid, or wrong <param>s provided
        if queries.viewkeys() == api_commands[command][endpoint].viewkeys():
            for param in queries:
                if queries[param] not in api_commands[command][endpoint][param]:
                    log_unk('%s not recognized as valid <value> for %s' % (
                        repr(queries[param]), repr(param)))
                    return False
        else:
            log_unk('%s not recognized as valid <query> for %s' % ( 
                ', '.join(('%s=%s' % (param, repr(queries[param])) 
                           for param in queries)),
                endpoint))
            return False
        
        # if no failure points reached
        argv[2:] = ['%s=%s' % query for query in queries.viewitems()]
        return True

    def do_api_command(self, argv):
        """Returns <requests> received from telling $agent to poll the API."""
        if self.active_agent == None:
            raise ValueError('not currently controlling an agent')
        return self.active_agent.poll_api(
            api_url_for('%s/%s?' % tuple(argv[:2]), '&'.join(argv[2:]))
        )
        
    def run_custom_program(self, argstr):
        is_custom = True

        argv = argstr.split()
        if argv[0] == 'copenhagent':
            if len(argv[2:]) != 1: is_custom = False
            else:
                # 'copenhagent new _____'
                if argv[1] == 'new':  self.set_active_agent(name=argv[2])
                # 'copenhagent agent _____'
                elif argv[1] == 'agent':  self.set_active_agent(token=argv[2])
        if argstr == 'navigation ai':  navigation_ai(self)
        elif False: pass
        else: raise CustomProgramError('run_custom_program(): not a custom program')

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
        
class Logger:
    """Builds a formatter for messages logged to the console."""

    def __init__(self, function=None):
        if function != None: self.log_runtime_of(function)

    def log_runtime_of(self, function):
        """Run $function and log its start, end, and runtime."""
        f_name = function.__name__
        f_event_str = '%-10.10s %s' % (function.__name__, '%9.9s')

        start = self.log(f_event_str % '<start>')
        self.function_output = function()
        end = self.log(f_event_str % '<end>')
        
        runtime = end-start
        self.log(f_event_str % '<runtime>', 
                 '%10.10s() runtime was %10.8f' % (f_name, runtime))

    def log(self, event, message=''):
        """Log to console in specific format: [time] event : message."""
        t = time.clock()
        print '[ %10.8f ] %20.20s : %-50.50s' % (t, event, message)
        return t

    def f_output(self):
        """Return the output of the function called in log_runtime_of."""
        return self.function_output

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
#        return nav_agent.nav_generic_breadth_first()
        return nav_agent.nav_generic_depth_first()
#        return nav_agent.nav_generic_greedy_best_first()

    nav_agent = Logger(nav_setup).f_output()
    Logger(nav_solve) 
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
