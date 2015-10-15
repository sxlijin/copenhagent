#!/usr/bin/env python


import readline
import sys
import requests
import json
import time
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





##### DATA STRUCTURES <START> #####

class Queue:
    """Implements a standard FIFO queue."""

    def __init__(self):
        """Initialize the queue."""
        self.queue = []

    def enqueue(self, item, extend=None):
        """Enqueue $item; if $item is iterable and $extend True, instead,
        iterate through $item and add all items to $self.queue."""
        if extend == None: self.queue.append(item)
        elif extend == True: self.enqueue_extend(item)
    
    def enqueue_extend(self, item):
        """Iterate through $item and enqueue all."""
        try:
            self.queue.extend(item)
        except TypeError:
            print "Queue.enqueue_extend() called on non-iterable."
    
    def dequeue(self):
        """Dequeue and return; raises IndexError if queue is empty."""
        if self.is_empty():
            raise IndexError('queue is empty')
        else:   
            return self.queue.pop(0)

    def is_empty(self):
        """Returns True if queue is empty."""
        return len(self.queue) == 0

class Stack:
    """Implements a standard LIFO stack."""

    def __init__(self):
        """Initialize the stack."""
        self.stack = []

    def push(self, item, extend=None):
        """Push $item; if $item is iterable and $extend True, instead,
        iterate through $item and add all items to $self.stack."""
        if extend == None: self.stack.append(item)
        elif extend == True: self.push_extend(item)
    
    def push_extend(self, item):
        """Iterate through $item and enstack all."""
        try:
            self.stack.extend(item)
        except TypeError:
            print "Queue.enstack_extend() called on non-iterable."
    
    def pop(self):
        """Destack and return; raises IndexError if stack is empty."""
        if self.is_empty():
            raise IndexError('stack is empty')
        else:   
            return self.stack.pop()

    def is_empty(self):
        """Returns True if stack is empty."""
        return len(self.stack) == 0


##### DATA STRUCTURES <END> #####





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
    nav_agent.nav_breadth_first()

    end = time.clock()
    print_timetable('| %6.2f : nav ai %9s |' % (end, '<end>'))
    print_timetable(border)
    print_timetable('| %6.2f : nav ai %9s |' % (end-start, '<runtime>'))
    print_timetable(border)


class NavigationInstance:
    """immutable, saves a problem instance for a game of Navigation."""
    def __init__(self, agent_token, debug=False):
        """call nav/enter() and parse returned FullResponse"""
        
        self.debug = debug
        
        # TODO: convert this entire thing to a class
        # store the agent token and header
        self.h = {'agentToken':agent_token}
        r = try_command('navigation enter')#, h=self.h)

        # begin parsing the FullResponse
        nav_setup = r.json()['state']['navigation'][AGENT_TOKEN]
        nav_config = nav_setup['config']
        nav_graph = nav_setup['graph']
        
        # store $seed, which is the default weight for nav vertices
        self.seed = nav_config['seed']

        if debug and False:
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
        self.vertex_weight = {}
        self.vertex_nexts = {}
        for vertex in nav_graph['vertices']:
            self.vertex_weight[vertex] = nav_graph['vertices'][vertex]['weight']
            self.vertex_nexts[vertex] = {}
            if vertex in nav_graph['edges']: 
                self.vertex_nexts[vertex] = nav_graph['edges'][vertex]

        self.init_vertex = '[{row},{column}]'.format(**nav_setup['position'])
    
    # methods to access the internal state and its characteristics
    def get_init_pos(self): 
        """Returns initial position of agent as '[r, c]'."""
        return self.init_vertex

    def get_seed(self):
        """Return the seed for the NavInst."""
        return self.seed

    def get_weight(self, vertex): 
        """Returns weight of $vertex."""
        return self.vertex_weight[vertex]

    def get_nexts_from(self, vertex): 
        """Return dict of possible moves from $vertex
        where directions are keys and destinations are values;
        current pos is default vertex."""
        return self.vertex_nexts[vertex]

    def get_dest_from_via(self, vertex, direction):
        """Returns would-be dest of moving in $direction from $vertex."""
        return self.get_nexts_from(vertex)[direction]
    
    def get_dir_to_dest(self, vertex, destination):
        """Returns direction to get from $vertex to $destination."""
        nexts = self.get_nexts_from(vertex)
        if destination in nexts.viewvalues():
            # iterate through: no worry about cost because len(nexts[dir]) <= 3
            for direction in nexts: 
                if destination == nexts[direction]: return direction

class NavigationState:
    """An immutable NavigationState for a NavigationInstance."""
    
    def __init__(self, nav_inst, 
            pos=None, creds=None, moves=None, 
            prev=None, prev_dir=None):
        """Contruct a NavState: track NavInst, pos, #credits, #moves, $prev."""
        # NOTE: must implement deepcopy() to make NavState mutable
        # adding $nav_inst to NavState does not add significant overhead
        # because $self.nav_inst binds to an existing NavInst
        self.nav_inst = nav_inst
        self.pos = self.nav_inst.get_init_pos() if pos == None else pos
        self.creds = 0 if creds == None else creds
        self.moves = 0 if moves == None else moves
        # save previous state
        self.prev = prev
        self.prev_dir = prev_dir
 
    def __str__(self):
        return self.get_pos()

    #def get_deepcopy(self):
    #    """Return deepcopy of internal state."""
    #    # MUST implement if NavState is made mutable
    #    return self
    
    def get_pos(self):
        """Returns current position."""
        return self.pos
    
    def get_n_creds(self):
        """Returns number of earned discredits."""
        return self.creds

    def get_n_moves(self):
        """Returns number of moves made."""
        return self.moves
    
    def get_weight(self, vertex=None):
        """Returns weight of $vertex if specified, else $self.pos."""
        if vertex == None: return self.nav_inst.get_weight(self.pos)
        else: return self.nav_inst.get_weight(vertex)

    def get_nexts(self):
        """Return dict of possible moves from $self.pos
        where directions are keys and destinations are values."""
        return self.nav_inst.get_nexts_from(self.pos)
 
    def get_edge_to(self):
        """Return directed edge to $self.pos with dir as 3-tuple."""
        return tuple(s.get_prev(), s, s.get_prev_dir())
    
    def get_dest_via(self, direction):
        """Return would-be dest of moving in $direction from $self.pos"""
        return self.nav_inst.get_dest_from_via(self.pos, direction)

    def get_dir_to(self, destination):
        """Return direction to get from $self.pos to $destination."""
        return self.nav_inst.get_dir_to_dest(self.pos, destination)
    
    def get_avg_creds(self):
        """Returns average discredits earned per move."""
        try: return 1.0*self.get_n_creds()/self.get_n_moves()
        except ZeroDivisionError: return 0.0
    
    def get_avg_if_move(self, direction):
        """Returns what get_avg_creds() would if agent moves in $direction."""
        return self.get_result(direction).get_avg_creds()
    
    def get_prev(self):
        """Return the ancestor NavState (returns None if none exists)."""
        return self.prev
    
    def get_prev_dir(self):
        """Return the direction from self.get_prev() to $self."""
        if self.prev_dir != None: return self.prev_dir
        elif self.get_prev() != None: return self.get_prev().get_dir_to(self)

    def get_result(self, direction):
        """Return state resulting from moving in $direction."""
        dest = self.get_nexts()[direction]
        return NavigationState(
            self.nav_inst, 
            pos=dest,
            creds = self.get_n_creds() + self.nav_inst.get_weight(dest),
            moves = self.get_n_moves() + 1,
            prev = self, prev_dir = direction)

    def get_results(self):
        """Return dict of possible resulting states from $self.pos
        where directions are keys and destinations are values."""
        return {d:self.get_result(d) for d in self.get_nexts()}

    def log(self):
        """Log $self (55 chars long)."""
        #print '='*55
        print 'pos %7s; avg creds is %5.2f (%3d creds in %2d moves)' % (
            self.get_pos(), self.get_avg_creds(), 
            self.get_n_creds(), self.get_n_moves())

class NavigationAgent:
    """NavigationAgent to play a NavigationInstance."""
    
    def __init__(self, nav_inst, nav_state=None, debug=False):
        self.nav_inst = nav_inst
        self.nav_state = NavigationState(nav_inst) if nav_state == None else nav_state
        self.debug = debug
    
    def __str__(self):
        return self.get_pos()
    
    def log_alg_start(self, alg_name):
        """Log the start of a navigation algorithm."""
        if self.debug: self.log_alg_msg(alg_name, 'START')

    def log_alg_end(self, alg_name):
        """Log the start of a navigation algorithm."""
        if self.debug: self.log_alg_msg(alg_name, 'END')

    def log_alg_msg(self, alg_name, msg):
        """Log a message for a navigation algorithm."""
        if not self.debug: return
        log_msg = '[%s] <%s> ' % (alg_name, msg)
        print log_msg + '='*(55 - len(log_msg))

    def cmd_nav_moves(self, moves):
        """Command agent to make a move in navigation."""
        # if passed a $direction
        if type(moves) in (str, unicode):
            return try_command('navigation lane direction=%s' % moves)
        # if passed list of moves
        elif type(moves) is list:
            # if moves are in the form of ($direction, $dest_vertex)
            if type(moves[0]) is tuple:
                # move in $direction
                for move in moves: self.cmd_nav_moves(move[0])
            # if moves are in the form of $direction
            elif type(moves[0]) is str:
                # move in $direction
                for move in moves: self.cmd_nav_moves(move)
    
    def cmd_nav_leave(self):
        """Command agent to leave navigation."""
        return try_command('navigation leave')
    
    def prompt_cmd_nav_leave(self):
        """Command agent to leave navigation, pause for user acknowledgment."""
        if self.debug: raw_input('press enter to leave')
        self.cmd_nav_leave()
    
    def nav_random(self):
        self.log_alg_start('random walk')
        # NOTE: warning, this binds $s to $self.nav_state
        # if NavigationState is changed to be mutable, $s must be a deepcopy()
        s = self.nav_state
        moves = []
        while s.get_nexts() != {} : 
            if self.debug: s.log()
            next_dirs = s.get_nexts()
            direction = next_dirs.keys()[randint(0, len(next_dirs)-1)]
            # bind $s to a new NavState
            s = s.get_result(direction)
            moves.append((direction, s))
        self.cmd_nav_moves(moves)
        self.log_alg_end('random walk')
        self.prompt_cmd_nav_leave()
    
    def nav_greedy_best_first(self):
        self.log_alg_start('greedy best first')
        # NOTE: warning, this binds $s to $self.nav_state
        # if NavigationState is changed to be mutable, $s must be a deepcopy()
        s = self.nav_state
        moves = []
        while s.get_nexts() != {} : 
            if self.debug: s.log()
            nexts = s.get_nexts()
            # sorted() sorts in ascending order, so grab last element
            direction = sorted(nexts.viewkeys(), key=s.get_avg_if_move)[-1]
            # binds $s to a new NavState
            s = s.get_result(direction)
            moves.append((direction, s))
        self.cmd_nav_moves(moves)
        self.log_alg_end('greedy best first')
        self.prompt_cmd_nav_leave()

    # generic tree search algorithm:
    # 
    # walk = initial_state
    # frontier = some_data_struct //queue, stack, priority queue, heap
    # 
    # while (goal not met) or (frontier not empty):
    #   frontier.insertset(walk.nexts)
    #   walk <- frontier.next
    # 
    # if (goal met)
    #   return goal met
    # 
    # =================================================================
    # 
    # // maybe explored should be a 3-tuple? directed edges and avg creds by following thru
    # explored = {} 
    # // keys   : explored $vertex
    # // values : ($avg, $path) where $avg is avg creds earned on $path to get to $vertex
    # // unique (key, value) pairs because you overwrite value if new $avg is better
    # 
    # paths = [] ## want each path to be ($avg_creds, $moves) where $moves is list of dirs
    # // is this one even necessary?
    #
    # walk = initial_state
    # frontier_edges = some_data_struct (queue, stack, priority queue)
    # frontier_edges.insertset(initial_state.next_edges)
    # 
    # while frontier not empty:
    #   walk <- frontier_edges.next.tail
    #   frontier_edges.insertset(walk.next_edges)
    #
    #   // if $walk has already been explored:
    #   if walk is in explored:
    #       //overwrite path to walk if new path has better $avg creds
    #       if new_path_to_walk better than explored_path_to_walk:
    #           explored_path_to_walk <- new_path_to_walk
    #       else:
    #           discard new_path_to_walk
    #   // if $walk hasn't been explored:
    #   else:
    #       //mark walk as explored
    #       explored.insert(path_to_walk)
    #

    # NEEDS OPTIMIZATION
    # hits segfaults on any NavInst's outside of dis
    # potential optimizations:
    #   don't enqueue edges if current best avg impossble to beat
    def nav_breadth_first(self):
        self.log_alg_start('breadth first')
        
        # NavState currently tracks its ancestor
        # maybe a more efficient way to represent the directed edges?
        
        # track the current state
        # track explored vertices as { $vertex : ($avg_creds, NavEdge) }
        # track the best path as ($avg_creds, NavEdge)
        s = self.nav_state
        frontier = Queue()
        #frontier.enqueue((None, s, None))
        frontier.enqueue(s)
        explored = {}
        #best_path = (0.0, (None, s, None))
        best_end = s

        seed = s.nav_inst.get_seed()
        
        # standard searches will use while not goal_reached()
        # not possible here: there is no goal test for NavStates; you can only
        #   choose the best of the many NavStates that are generated
        #   e.g., goal NavState might have nonempty set of available moves
        #           because continuing to move would lower the average
        #
        # -> optimize by determining when an average cannot be beat
        # ====> use NavState.get_n_moves()
        #
        # keep going if you can find a better average
        #   use unexplored paths as a proxy therefor
        while not frontier.is_empty():
            # $s is the current NavState being expanded
            s = frontier.dequeue()

            #if s.get_weight() < seed:
            #    print "skip %s %s < %s" % (s.get_pos(), s.get_weight(), seed)
            #    continue

            #if self.debug: s.log()
            #if self.debug: print id(s)
            # add potential next moves to the frontier
            for result in s.get_results().viewvalues():
                if result.get_weight() >= seed:  frontier.enqueue(result)
                elif self.debug:    print 'not enqueueing %s' % result
    
            # if current NavState has not yet been explored
            #       OR has been explored & NavEdge is better path
            # use s.get_pos() as key bc can have different $s at same vertex
            if (s.get_pos() not in explored() 
                    or s.get_avg_creds() > explored[s.get_pos()]['avg']): 

                # overwrite or create item with NavEdge in value 
                explored[s.get_pos()] = {'avg':s.get_avg_creds()}

                # if current NavEdge is better than current best path
                if s.get_avg_creds() > best_end.get_avg_creds(): best_end = s
        
        # log last edge in best path
        if self.debug: best_end.log()
        
        # regenerate best path from its terminal edge
        # work backwards until NavState.prev == (initial_state.prev = None)
        hist = Stack()
        s = best_end
        while None != s.get_prev():
            hist.push(s)
            s = s.get_prev()

        # follow the best path forward
        while not hist.is_empty():
            s = hist.pop()
            #if self.debug: print s.get_prev_dir()
            self.cmd_nav_moves(s.get_prev_dir())
            #if self.debug: print '>>> %7s >>> %7s via %5s' % (s.get_edge_to())

        self.log_alg_end('breadth first')
        self.prompt_cmd_nav_leave()


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
