#!/usr/bin/env python

import readline, sys
import requests, json
from time import clock as time
from random import randint

##### GLOBAL VARIABLES <START> #####

### NOTE: internal state variables are tracked in [AI FUNCTIONS]

### verbosity controls
QUIET = False
SILENT = True
dump_json_state = False


### set of all legal commands, endpoints, and parameters
COMMANDS = {
    'map': {
        'enter': {},
        'metro': {'direction':['cw', 'ccw']},
        'bike': {'locationId':
                ['bryggen', 'folketinget', 'noerrebrogade', 
                'langelinie', 'dis', 'christianshavn', 
                'jaegersborggade', 'frederiksberg', 'louises', 
                'koedbyen', 'parken']
        },
        'leave': {}
    },
    'navigation': {
        'enter': {},
        'lane': {'direction':['left', 'stay', 'right']},
        'leave': {}
    },
    'papersoccer': {
        'enter': {},
        'play': {'direction':['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']},
        'leave': {}
    }
}

##### GLOBAL VARIABLES <END> #####

HOSTNAME='localhost'

def api_url_for(path, query):
    """Return full concatenated API URL to request from $path and $query."""
    if path[0] == '/': path = path[1:]
    return 'http://{hostname}:3000/api/{path}?{query}'.format(
        hostname=HOSTNAME,
        path=path,
        query=query
        )

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


    def __init__(self):
        """Initialize the shell."""
        self.active_agent = ''

    def loop(self):
        """Run the shell."""
        while True:
            usi = raw_input('disai> ')
            if usi == 'exit':  break
            try_command(usi)

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
                for i in range(int(argv[0])): r = try_command(argv[1:])
                return r
            if verify_command(argv):  return do_command(argv)
            else:
                return run_custom_program(argstr)
        except IndexError:
            return None

    def verify_command(self, argv):
        """
        Verify $argv is a sound shell command, i.e. has format

            <command> <endpoint> <query>

        where <query> takes form <param>=<value>.

        If <endpoint> or <query> are omitted, prompt user for
        <endpoint> or <value>s for each <param> as appropriate.
        """

        # verify <command>
        command = argv[0]

        # FAIL if $command is not valid
        if command not in api_commands:
            print '%s not recognized as <command>' % repr(command)
            return False

        # verify <endpoint>; prompt if none provided
        try:
            endpoint = argv[1]
        except IndexError:
            # accept <query> if specified
            argv.append(raw_input(
                'enter a %s endpoint (%s): ' % (
                    command, ', '.join(api_commands[command]))
            ).split())
        finally:
            endpoint = argv[1]

        # FAIL if $endpoint is not valid
        if endpoint not in api_commands[command]:
            print '%s not recognized as <endpoint> for %s' % (
                repr(endpoint), repr(command))
            return False
        
        # verify <query>; prompt if none provided and <query> required
        # NOTE: <param>, '=', and <value> can be separated by spaces now
        queries = argv[2:]
        queries = ' '.join(queries).replace('=', ' = ').split()
        queries = ' '.join(queries).replace(' = ', '=').split()
        queries = {param:val for [param,val] in [q.split('=') for q in queries]}

        # prompt for <value>s if no <query> provided
        if len(queries) == 0 and len(api_commands[command][endpoint]) != 0:
            for param in api_commands[command][endpoint]:
                queries[param] = raw_input(
                    'enter a %s value (%s): %s=' % (
                        param,
                        ', '.join(api_commands[command][endpoint]),
                        param) )

        # FAIL if a <value> is not valid, or wrong <param>s provided
        if queries.viewkeys() == api_commands[command][endpoint].viewkeys():
            for param in queries:
                if queries[param] not in api_commands[command][endpoint][param]:
                    print '%s not recognized as valid <value> for %s' % (
                        repr(queries[param]), repr(param))
                    return False
        else:
            print '%s not recognized as valid <query> for %s' % ( ', '.join([
                    '%s:%s' % (repr(param), repr(queries[param])) 
                    for param in queries] )
            return False
        
        # if no failure points reached
        argv[2:] = ['%s=%s' % query for query in queries.viewitems()]
        return True

    def do_command(self, argv):
        """Returns <requests> received from telling $agent to poll the API."""
        return self.active_agent.poll_api(
            api_url_for('%s/%s?' % tuple(argv[:2]), '&'.join(argv[2:]))
        )
        
    def run_custom_program(self, argstr):
        return None
    

class Agent:
    """Controls an agent in the copenhagent environment."""
    
    def __init__(self, agent_token):
        """Take control of the agent."""
        self.agent_token = agent_token
        self.header = {u'agentToken':agent_token}
            
        self.location = ''
        self.dis_credits = 0
        self.actions = 0

    def get_header(self):
        return self.header
    
    def init_control(self, msg=None):
        if msg == None:  msg = 'opening python session'
        return self.poll_api(api_url_for('agent/say', 'message=%s' % msg))

    def parse_response(self, resp):
        return None
    
    def poll_api(self, api_url):
        """Request $api_url with $self.agent_token specified in header."""
        return requests.get(api_url, headers=self.get_header())
        
    



##### STATE FUNCTIONS <START> #####

### internal state variables
LOCATION = ''
DIS_CREDITS = 0
AGENT_TOKEN = ''
HEADER = {}

### modify internal state
def set_loc(loc):
    global LOCATION
    LOCATION = loc

def incr_dis_credits(delta):
    global DIS_CREDITS
    DIS_CREDITS = delta + DIS_CREDITS

def set_agent(token):
    global AGENT_TOKEN
    AGENT_TOKEN = token
    global HEADER
    HEADER = {'agentToken':AGENT_TOKEN}

##### STATE FUNCTIONS <END> #####





### NAVIGATION

def ai_nav():
    debug=False
    #debug=True
    
    def print_timetable(text):
        print_flag = True
        if print_flag:  print text
    
    border = '%s:%s' % ('='*9, '='*19)

    print_timetable(border)
    start = time.clock()
    print_timetable('| %6.2f : nav ai %9s |' % (start, '<start>'))
    
    nav_inst = NavigationInstance(AGENT_TOKEN, debug=debug)
    nav_agent = NavigationAgent(nav_inst, debug=debug)
    
    data_struct = (Queue(), Stack())[1]
    nav_agent.nav_generic_first_by_struct(data_struct)

    end = time.clock()
    print_timetable('| %6.2f : nav ai %9s |' % (end, '<end>'))
    print_timetable(border)
    print_timetable('| %6.2f : nav ai %9s |' % (end-start, '<runtime>'))
    print_timetable(border)

    nav_agent.prompt_cmd_nav_leave()

##### AI FUNCTIONS <END> #####





##### HELPER FUNCTIONS <START> #####

def dump_json(json_obj, override=False):
    """Prints human-readable JSON from dict or <requests>."""
    # suppress output when SILENT==True
    if SILENT and not override: return
    try:    
        # type-check $json_obj
        if type(json_obj) is dict: 
            # check flags for specified behavior when dumping $json_obj
            if not dump_json_state and 'state' in json_obj.keys():
                json_obj.pop('state')
                print "popping .json()['state']"
            # dump $json_obj
            print json.dumps(json_obj, indent=4)
        # if $json_obj is a <requests> object, cast to json and dump
        elif type(json_obj) is requests.models.Response: dump_json(json_obj.json())
    except (TypeError, ValueError) as e:
        print e
        print json_obj


def api_url(tail):
    """Returns full concatenated API URL to poll from path and query."""
    # sanitize $tail before returning
    if (tail[0] != '/'): tail = '/' + tail
    return 'http://' + HOSTNAME + ':3000/api' + tail


def get_api(tail, h=None):
    """Returns <requests> obtained by polling the API."""
    if h is None: h = HEADER
    # construct url
    get_url = api_url(tail)
    # retrieve url
    r = requests.get(get_url, headers=h)
    # suppress output when SILENT==True
    if SILENT: return r
    print
    print '[polling API <START>]'
    print 'GET:', get_url
    print '  header:', str(h)
    print 'GET -> JSON:'
    dump_json(r)
    print '[polling API <END>]'
    return r


def list_opts(cmd, endpoint, param):
    """Returns list of options (opt1, opt2, ...) for $param in /$cmd/$endpoint."""
    return '(' + ', '.join([repr(opt) for opt in COMMANDS[cmd][endpoint][param]]) + ')'

##### HELPER FUNCTIONS <END> #####





##### WORKER FUNCTIONS <START> #####

def create_agent(name):
    """Creates new agent and returns the corresponding agentToken."""
    set_agent(get_api('/environment/connect?name=' + name).json()[u'agentToken'])
    return AGENT_TOKEN


def control_agent(agent_token):
    """Takes control of agent and spawns shell to issue commands for the agent."""
    # create header with $agentToken
    set_agent(agent_token)
    # verify $agentToken by sending a message
    r = get_api('/environment/agent/say?message=opening python session')

    # TODO: implement $SILENT flag
    # if connection successful
    if (200 == r.status_code):
        # acknowledge success and spawn shell
        print '\n+ opened connection successfully: {}\n'.format(AGENT_TOKEN)
        usi = ''
        # allow $usi=='exit' to terminate shell
        while(usi != 'exit'):
            usi = raw_input('disai> ') # unsafe input !!!!!!!!
            if (usi == 'exit'): continue
            try_command(usi)
        # announce shell is closed
        get_api('/environment/agent/say?message=closing python session')
        print '\n- closed connection successfully: {}\n'.format(AGENT_TOKEN)
    # if connecting with $sess_id fails, ignore and fail
    else:
        print 'failed to connect: status code {}'.format(r.status_code)


def try_command(usi):
    """Polls API according to custom commands, returns received <requests> object."""
    # ad hoc commands
    if usi == 'program': return program()
    if usi == 'papersoccer win': return ps_win()
    if usi == 'navigation ai': return ai_nav()
    
    # break up the command
    usi_split = usi.split()
    
    # repeat command n times
    if len(usi_split) > 0 and usi_split[0].isdigit():
        # TODO: terminate loop early if any command while looping fails
        usi = usi[len(usi_split[0])+1:]
        for i in range(int(usi_split[0])): 
            r = try_command(usi)   
        return
    
    # attempt command
    if len(usi_split) > 0: return run_command(usi_split)
    
# takes ['map', 'metro', 'direction=cw'] etc as $args
# refers to 'map metro direction=cw' as:
#     - command (map)
#     - endpoint (metro)
#     - parameter (direction=cw)
def run_command(args):
    """Parses command, polls API if sound, returns received <requests>."""
    # verify specified command
    cmd = args[0]
    if cmd in COMMANDS.keys():     args = args[1:]
    # FAIL OUT if command verification fails
    else:
        print 'command not recognized: {}'.format(args[0])
        return
    
    # if no endpoint given, prompt user for one
    if len(args) == 0: 
        args = raw_input( 'enter a {} endpoint ({}): '.format(
            cmd, ', '.join(COMMANDS[cmd].keys())) ).split()
    endpoint = args[0]
    
    # begin constructing 
    api_query = '/' + cmd + '/' + endpoint + '?'
    
    # parse params into a dict
    args = { p.split('=')[0]:p.split('=')[1] 
        for p in args[1:] 
        if len(p.split('=')) == 2 }

    # verify specified endpoint
    if endpoint in COMMANDS[cmd].keys():
        # if no parameters passed to endpoint which requires them,
        # prompt user for parameters
        if len(args) == 0 and len(COMMANDS[cmd][endpoint]) != 0 :
            for param in COMMANDS[cmd][endpoint]:
                args[param] = raw_input( 
                    'enter a value for {0} {1}: {0}='.format(
                    param, list_opts(cmd, endpoint, param)))

        # verify specified parameters
        if args.keys() == COMMANDS[cmd][endpoint].keys() :
            for param in args:
                # if illegal value passed as parameter, fail out
                if args[param] not in COMMANDS[cmd][endpoint][param]:
                    print 'ERROR:', repr(args[param]),
                    print 'not recognized as legal value for', repr(param),
                    print list_opts(cmd, endpoint, param)
                    return
        # FAIL OUT if parameter verification fails
        else:
            print 'endpoint', endpoint_url, 'requires params with legal values: '
            for k in COMMANDS[cmd][endpoint]:
                print '\t', k, list_opts(cmd, endpoint, k)
            print 'but received args:'
            for k in args: print '\t', k + '=' + args[k]
            return
    # FAIL OUT if endpoint verification fails
    else:
        print '{} endpoint not recognized: {}'.format(cmd, endpoint)
        return

    # if no problems encountered while parsing
    # construct api query and return requests object
    api_query += '&'.join(
        ['{}={}'.format(p, args[p]) for p in COMMANDS[cmd][endpoint]])
    r = get_api(api_query)
    return r

##### WORKER FUNCTIONS <END> #####










#### COMMAND LINE INTERPRETERS <START> #####

def help():
    print 
    print 'Bad arguments received. Script can be run with the following options: '

    print '\t--new arg\t:',
    print 'create an agent with name $arg and take control thereof'

    print '\t--agent arg\t:',
    print 'take control of agent with agentToken $arg'
    print

def main():
    if len(sys.argv) == 3:
        if sys.argv[1] == '--new': 
            control_agent(create_agent(sys.argv[2]))
            sys.exit(0)
        if sys.argv[1] == '--agent': 
            control_agent(sys.argv[2])
            return
    # print help message if bad arguments received
    help()

if __name__ == "__main__":
    main()

##### COMMAND LINE INTERPRETERS <END> #####
