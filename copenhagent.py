#!/usr/bin/env python


import readline
import sys
import requests
import json
from random import randint

##### GLOBAL VARIABLES <START> #####

### NOTE: internal state variables are tracked in [AI FUNCTIONS]

### verbosity controls
QUIET = False
SILENT = True
dump_json_state = False

HOSTNAME='localhost'

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





##### AI FUNCTIONS <START> #####




def program():
    #this shit is to do the map enter, map metro, and map bike commands and update loc internally
    a= try_command('map enter').json()
    set_loc( a['state']['agents'][AGENT_TOKEN]['locationId'] )
    metroLine = a['state']['map']['metro']
    print ('Your starting location is ')+LOCATION 

    b= try_command('map metro').json()
    message =b['action']['message'].split();
    set_loc( message[4] )
    incr_dis_credits( -int(message[8]) )
    print ('Current discredits: ')+str(DIS_CREDITS)
    print ('Current location: ')+LOCATION

    c= try_command('map bike').json()
    message =c['action']['message'].split();
    set_loc( message[4] )
    incr_dis_credits( int(message[8]) )
    print ('Current location: ')+LOCATION
    print ('Current discredits: ')+str(DIS_CREDITS)


    #this guy is to find what's cheaper, to metro it or to bike
    dest=raw_input('tell me where u wanna go yo: ')
    while(dest not in metroLine.keys()):
        print('FOOL THAT\'S NOT A VALID LOCATION')
        print('Try that again. Here\'s your options cuz you can\'t remember probably.')
        print metroLine.keys()
        dest=raw_input('gimme that location: ')
    curLocation=LOCATION
    #clockwise:
    cwCost=0
    while(curLocation!=dest):
        tempLocation=metroLine[curLocation]['cw'].keys()[0]
        cwCost+=metroLine[curLocation]['cw'][tempLocation]
        curLocation=tempLocation
    print 'The cost to get from ' +LOCATION + ' to '+dest+ ' with the metro in cw order is '+ str(cwCost)+'.'
    #counterclockwise
    ccwCost=0
    curLocation=LOCATION
    while(curLocation!=dest):
        tempLocation=metroLine[curLocation]['ccw'].keys()[0]
        ccwCost+=metroLine[curLocation]['ccw'][tempLocation]
        curLocation=tempLocation
    print 'The cost to get from ' +LOCATION + ' to '+dest+' with the metro in ccw order is '+ str(ccwCost)+'.'
    cost=15
    cheapest='bike'
    print "cwcost is {}, ccwcost is {}".format(cwCost, ccwCost)
    if(cwCost<cost):
        cost=cwCost
        if(ccwCost<cost):
            cheapest='ccw metro'
        else:
            cheapest='cw metro'
    elif(ccwCost<cost):
        cheapest='ccw metro'
    print 'the cheapest way to get to ' + dest+ ' is to '+cheapest

def ai_nav():
    """Runs AI to play navigation."""
    
    debug = False

    # obtain FullResponse from /api/navigation/enter
    r = try_command('navigation enter')

    # filter navigation problem instance from FullResponse
    nav_setup = r.json()['state']['navigation'][AGENT_TOKEN]
    nav_config = nav_setup['config']
    nav_graph = nav_setup['graph']

    if debug:
	    print '=== dumping $nav_config ==='
	    dump_json(nav_config, override=True)
	    print
	    print '=== showing $nav_setup.keys() ==='
	    print nav_setup.keys()
	    print
	    print '=== showing $nav_setup[position] ==='
	    dump_json(nav_setup['position'], override=True)

    # create dicts $vertex_weight and $vertex_moves with keys $vertex
    # '[{row},{column}]' is the format of $vertex
    (vertex_weight, vertex_moves) = ({}, {})
    for vertex in nav_graph['vertices']:
        vertex_weight[vertex] = nav_graph['vertices'][vertex]['weight']
        vertex_moves[vertex] = {}
        if vertex in nav_graph['edges']: 
            vertex_moves[vertex] = nav_graph['edges'][vertex]
        
    # create internal state for navigation
    # ['pos'] -> current position, format is [{row},{column}]
    # ['creds'] -> credits earned whilst playing current instance
    # ['moves'] -> moves made whilst playing current instance
    nav_state = {}
    nav_state['pos'] = '[{},{}]'.format(
        nav_setup['position']['row'], nav_setup['position']['column'] )
    nav_state['creds'] = 0
    nav_state['moves'] = 0
    nav_state['creds_freqs'] = {}
    
    # methods to access the internal state and its characteristics
    def pos(): 
        """Returns current position of agent."""
        return nav_state['pos']
    def weight(vertex=None): 
        """Returns weight of $vertex; current pos is default vertex."""
        if vertex == None: vertex = pos()
        return vertex_weight[vertex]
    def n_creds():
        """Returns number of discredits earned insofar."""
        return nav_state['creds']
    def n_moves():
        """Returns number of moves earned insofar."""
        return nav_state['moves']
    def legal_moves(vertex=None): 
        """Returns dict of possible moves from $vertex
        where directions are keys and destinations are values;
        current pos is default vertex."""
        if vertex == None: vertex = pos()
        return vertex_moves[vertex]
    def dest(direction):  
        """Returns would-be destination of moving in 
        $direction from current pos."""
        return legal_moves()[direction]
    def avg_earned():
        """Returns average credits earned per action in navigation."""
        try: return 1.0*n_creds()/n_moves() 
        except ZeroDivisionError: return 0
    def real_avg_earned():
        """Returns avg_earned, except also counts nav/enter() and nav/leave() actions."""
        return 1.0*n_creds() / (n_moves()+2)

    # methods to modify internal state
    def set_pos(new_pos): 
        """Set the position of the agent."""
        nav_state['pos'] = new_pos
    def incr_creds(delta=None):
        """Increase earned credits by $delta."""
        if delta == None: delta = weight()
        if delta not in nav_state['creds_freqs']: nav_state['creds_freqs'][delta] = 0
        nav_state['creds_freqs'][delta] += 1
        nav_state['creds'] += delta
    def incr_moves(delta=None):
        """Increase number of moves made by $delta."""
        if delta == None: delta = 1
        nav_state['moves'] += delta
    def play_nav_dir(d): 
        """Update internal state and make a move in navigation."""
        set_pos( legal_moves()[d] )
        incr_creds()
        incr_moves()
        r = try_command('navigation lane direction=' + d)
        if debug:
            print 'moved to {}, available moves are {}'.format(pos(), legal_moves())
            print 'earned {} discredits in {} moves playing nav'.format(n_creds(), n_moves())
        return r
    
    # different methods to play navigation
    def random_walk():
        """Follow a path at random through the graph."""
        while legal_moves() != {} :
            #if 'break' == raw_input('press enter to continue navigation\n'): break
            # move in random direction
            direction = legal_moves().keys()[randint(0, len(legal_moves())-1)]
            play_nav_dir(direction)
    
    def nav_greedy_best_first():
        """implements greedy best first walk"""
        while legal_moves() != {}:
            direction = legal_moves().keys()[0]
            for d in legal_moves():
                if weight(legal_moves()[d]) > weight(legal_moves()[direction]): direction = d 
            if debug:
                print "will earn {} creds, options are {}".format(
                    weight(legal_moves()[direction]), 
                    tuple(weight(x) for x in legal_moves().values()))
            play_nav_dir(direction)

    # play navigation
    if debug:
        print 'starting at {}, available moves are {}'.format(pos(), legal_moves())
    nav_greedy_best_first()
    if debug:
        print('%.2f (really %.2f) credits earned on average %s' % 
            (avg_earned(), real_avg_earned(),
            tuple(sorted(nav_state['creds_freqs'].viewitems()))) )
    #if '' == raw_input('finished, press enter to leave\n'): 
    try_command('navigation leave')
    ret = (n_creds(), n_moves(), avg_earned(), real_avg_earned())
    print('%10d, %10d, %10.4f, %10.4f' % ret)
    return ret

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
        (n_creds, n_moves) = (0, 0)
        for i in range(int(usi_split[0])): 
            r = try_command(usi)   
            if usi == 'navigation ai':
                (n_creds, n_moves) = (n_creds + r[0], n_moves + r[1])
        print '='*43
        avg = 1.0*n_creds/n_moves if n_moves != 0 else 0
        print '%.4f avg creds over %d moves (total creds %d)' % (avg, n_moves, n_creds)
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
                    get_flag &= False
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





##### ACTION FUNCTIONS <START> #####
win_from = {
    'n': [    'papersoccer play direction=ne',
        'papersoccer play direction=s',
        'papersoccer play direction=ne',
        'papersoccer play direction=se',
        'papersoccer play direction=se' ] ,
    's': [    'papersoccer play direction=se',
        'papersoccer play direction=n',
        'papersoccer play direction=se',
        'papersoccer play direction=ne',
        'papersoccer play direction=ne' ]
}

def ps_force_win_from(side):
    for act in win_from[side]: r = try_command(act)
    # uncomment to pause before leaving the game
    # raw_input('press enter to leave papersoccer game ')
    try_command('papersoccer leave')
    return r
    
def ps_play_dir(direction):
    return try_command('papersoccer play direction=' + direction)

def ps_win():
    dirs = ['ne','se']
    rand2 = randint(0,1)

    r = try_command('papersoccer enter')
    r = ps_play_dir(dirs[rand2])
    # try a random direction
    if len(r.json()['action']['percepts']) == 2:
        rand2 -= 1
        for i in range(2): r = ps_play_dir(dirs[rand2])
        if len(r.json()['action']['percepts']) == 2:
            rand2 -= 1
            r = ps_play_dir(dirs[rand2])
            r = ps_play_dir('e')
            r = ps_force_win_from(
                r.json()['action']['percepts'][0][0])
    if r.json()['action']['percepts'] == ['w']:
        r = ps_force_win_from(dirs[rand2][0])
    if not SILENT: print '\n', r.json()['action']['message']

##### ACTION FUNCTIONS <END> #####





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
            return
        if sys.argv[1] == '--agent': 
            control_agent(sys.argv[2])
            return
    # print help message if bad arguments received
    help()

if __name__ == "__main__":
    main()

##### COMMAND LINE INTERPRETERS <END> #####
