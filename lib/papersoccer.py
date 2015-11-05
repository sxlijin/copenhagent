#! /usr/bin/env python

import structs
from logger import *

def win_k_is_0_papersoccer():
    win_from = {    'n': [  'papersoccer play direction=ne',
                            'papersoccer play direction=s',
                            'papersoccer play direction=ne',
                            'papersoccer play direction=se',
                            'papersoccer play direction=se' ] ,
                    's': [  'papersoccer play direction=se',
                            'papersoccer play direction=n',
                            'papersoccer play direction=se',
                            'papersoccer play direction=ne',
                            'papersoccer play direction=ne' ]       }
    
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

def win_k_is_0_papersoccer():
    win_from_1 = {  'n': [  'papersoccer play direction=ne',
                            'papersoccer play direction=se',
                            'papersoccer play direction=se' ] ,
                    's': [  'papersoccer play direction=se',
                            'papersoccer play direction=ne',
                            'papersoccer play direction=ne' ]       }
    
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


class Vertex:
    """
    Builds an immutable representation of a vertex in a Papersoccer graph.
    """
    
    dirs = {  'n':(-1,  0),   's':(1,  0),  'w':(0, -1),  'e':(0, 1),
             'nw':(-1, -1),  'sw':(1, -1), 'ne':(-1, 1), 'se':(1, 1)  }

    def __init__(self, graph, ps_json_graph, key):
        """Construct the vertex corresponding to $key in $ps_graph."""
        self.graph = graph
        self.vertex_key = key
        ps_vertices = ps_json_graph['vertices']
        ps_vertex = ps_vertices[self.vertex_key]
        self.ps_row = ps_vertex['row']
        self.ps_column = ps_vertex['column']

        self.next_vertices = {}
        for d in dirs:
            if d in ps_vertex: continue # skip if edge marked

            successor_key = '[{r},{c}]'.format( r = v.get_row() + dirs[d][0],
                                                c = v.get_column() + dirs[d][1])
            if successor_key in ps_vertices:
                self.next_vertices[successor_key] = d

        self.move_again = ps_vertex.get('visited', False)

    def __str__(self):
        return self.vertex_key

    def __hash__(self):
        """Use the string representation of the vertex as its identifier."""
        return hash(self.get_key())

    def __eq__(self, other):
        try:
            return self.get_key() == other.get_key()
        except AttributeError:
            return False

    def get_key(self):
        """Return the string repr of the vertex."""
        return self.vertex_key

    def get_row(self):
        """Return the row number of the vertex."""
        return self.ps_row

    def get_column(self):
        """Return the column number of the vertex."""
        return self.ps_column

    def get_nexts(self):
        """Return the tuple of direct successors of <Vertex> $self."""
        return self.next_vertices.keys()

    def get_next_via(self, direction):
        """Return the <Vertex> $next with DirEdge($self, $next, $dir)."""
        return self.graph.get_next_via(self, direction)

    def get_dir_to_next(self, next_vertex):
        """Return the $dir in DirEdge($self, $next, $dir)."""
        return self.graph.get_dir_to_next(self, next_vertex)

class DirEdge:
    """Builds an immutable representation of a directed edge."""

    def __init__(self, tail, head, direction):
        """Initialize the directed edge."""
        (self.tail, self.head) = (tail, head)
        self.direction = direction

    def __str__(self):
        return '%-7s - %5s - %+7s' % (
            self.get_tail(), self.get_dir(), self.get_head())

    def get_tail(self):
        """Return the tail of the directed edge."""
        return self.tail

    def get_head(self):
        """Return the head of the directed edge."""
        return self.head

    def get_dir(self):
        """Return the direction of the directed edge."""
        return self.direction


class Graph:
    """
    Builds an immutable representation of a Papersoccer graph.
    """

    def __init__(self, ps_json_graph):
        """Parse the JSON to save the graph of Papersoccer.Instance."""
        self.ps_json_graph = ps_json_graph
        
        self.vertex_table = {
            vertex_key:Vertex(self, ps_json_graph, vertex_key)
            for vertex_key in ps_json_graph['vertices'] 
        }

        self.next_vertices = {}
        for vertex in self.vertex_table.viewvalues():
            nexts = set()
            for d in dirs:
                successor = '[{r},{c}]'.format( r = v.row + dirs[d][0],
                                                c = v.column + dirs[d][1] )
                if successor in self.vertex_table:
                    nexts.add( tuple(d, self.vertex_table[successor]) )
            self.next_vertices[vertex] = nexts
           
    def get_vertex(self, vertex_key):
        """Return the <Vertex> corresponding to $vertex_key."""
        return self.vertex_table[vertex_key]


class Instance:
    """Builds an immutable representation of a Papersoccer problem instance."""

    def __init__(self, shell, debug=False):
        """call nav/enter() and parse returned FullResponse"""
        
        self.debug = debug
        self.shell = shell
        self.token = self.shell.active_agent.agent_token

        self.try_command = shell.try_command
        
        r = self.try_command('papersoccer enter')

        # begin parsing the FullResponse
        ps_setup = r.json()['state']['papersoccer'][self.token]
        ps_config = ps_setup['config']
        self.graph = Graph(ps_setup['soccerfield'])
        
        # store $seed, which is the default weight for nav vertices
        self.seed = ps_config['seed']
        self.init_vertex = self.graph.get_vertex(
            '[{row},{column}]'.format(**ps_setup['currentVertex']))

    def get_initial(self): 
        """Returns <Vertex> specified to be initial position."""
        return self.init_vertex

    def get_seed(self):
        """Return the seed for the NavInst."""
        return self.seed

#class State:
#    """An immutable State within an Instance. Tracks path to a <Vertex>."""
#    
#    def __init__(self, instance,
#            vertex=None, count_credits=None, count_actions=None,
#            prev_state=None, dir_from_prev=None):
#        """Contruct a NavState: track NavInst, pos, #credits, #moves, $prev."""
#        # NOTE: if NavState is made mutable, MUST implement deepcopy()
#        self.instance = instance
#        self.vertex = instance.get_initial() if vertex == None else vertex
#
#        if count_credits == None:
#            try:
#                self.count_credits = instance.shell.active_agent.n_credits
#            except AttributeError:
#                self.count_credits = 0
#        else:
#            self.count_credits = count_credits
#
#        if count_actions == None:
#            try:
#                self.count_actions = instance.shell.active_agent.n_actions
#            except AttributeError:
#                self.count_actions = 0
#        else:
#            self.count_actions = count_actions
#
##        try:
##            self.count_credits = instance.shell.active_agent.n_credits
##            self.count_actions = instance.shell.active_agent.n_actions
##        except AttributeError:
##            self.count_credits = 0 if count_credits == None else count_credits
##            self.count_actions = 0 if count_actions == None else count_actions
#        # save previous state
#        self.prev_state = prev_state
#        self.dir_from_prev = dir_from_prev
# 
#    def __str__(self):
#        return '%7s with avg of %5.2f (%3d creds in %2d moves)' % (
#            self.get_vertex(), self.get_avg_creds(), 
#            self.get_n_credits(), self.get_n_actions())
#
#    def __lt__(self, other): return self.get_avg_creds() < other.get_avg_creds()
#    def __le__(self, other): return self.get_avg_creds() <= other.get_avg_creds()
#    def __gt__(self, other): return self.get_avg_creds() > other.get_avg_creds()
#    def __ge__(self, other): return self.get_avg_creds() >= other.get_avg_creds()
#    # do not implement __eq__ or __ne__: want those two to default to using id()
#
#    #def get_deepcopy(self):
#    #    """Return deepcopy of internal state."""
#    #    # MUST implement if NavState is made mutable
#    #    return self
#    
#    def get_vertex(self):
#        """Returns current position."""
#        return self.vertex
#    
#    def get_n_credits(self):
#        """Returns number of earned discredits."""
#        return self.count_credits
#
#    def get_n_actions(self):
#        """Returns number of moves made."""
#        return self.count_actions
#    
class Agent:
    """Agent to play a Instance."""
    
    def __init__(self, instance, state=None, debug=False):
        self.instance = instance
        self.state = State(instance) if state == None else state
        self.debug = debug
    
    def __str__(self):
        return self.get_pos()
    
    def alg_log_start(self, alg_name):
        """Log the start of a papersoccer algorithm."""
        if self.debug: self.alg_log_msg(alg_name, 'START')

    def alg_log_end(self, alg_name):
        """Log the start of a papersoccer algorithm."""
        if self.debug: self.alg_log_msg(alg_name, 'END')

    def alg_log_msg(self, alg_name, msg):
        """Log a message for a papersoccer algorithm."""
        if self.debug: log(alg_name, msg)

    def cmd_ps_move(self, moves):
        """Command agent to make a move in papersoccer."""
        # if passed a $direction
        if type(moves) in (str, unicode):
            return self.instance.try_command(
                'papersoccer play direction=%s' % moves)
        # if passed list of moves
        elif type(moves) is list:
            # if moves are in the form of ($direction, $dest_vertex)
            if type(moves[0]) is tuple:
                # move in $direction
                for move in moves: self.cmd_ps_move(move[0])
            # if moves are in the form of $direction
            elif type(moves[0]) is str:
                # move in $direction
                for move in moves: self.cmd_ps_move(move)
    
    def cmd_ps_leave(self):
        """Command agent to leave papersoccer."""
        return self.instance.try_command('papersoccer leave')
