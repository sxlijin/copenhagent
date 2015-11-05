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
    
    def __init__(self, graph, ps_json_graph, key):
        """Construct the vertex corresponding to $key in $ps_graph."""
        self.graph = graph
        self.vertex_key = key
        ps_vertex = ps_json_graph['vertices'][self.vertex_key]
        self.ps_row = ps_vertex['row']
        self.ps_column = ps_vertex['column']

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
        return self.graph.get_nexts(self)

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

    dirs = { 'n':(-1,  0),   's':(1,  0),  'w':(0, -1),  'e':(0, 1),
            'nw':(-1, -1),  'sw':(1, -1), 'ne':(-1, 1), 'se':(1, 1) }

    def __init__(self, ps_json_graph):
        """Parse the JSON to save the graph of Papersoccer.Instance."""
        self.ps_json_graph = ps_json_graph
        self.vertex_table = {
            vertex_key:Vertex(self, ps_json_graph, vertex_key)
            for vertex_key in ps_json_graph['vertices'] 
        }

        edges_by_tail = ps_json_graph['edges']

#        edges = tuple(frozenset().union(
#            *(frozenset().union(
#                DirEdge(self.get_vertex(tail_key),
#                        self.get_vertex(edges_by_tail[tail_key][direction]),
#                        direction)
#                for direction in edges_by_tail[tail_key]
#              ) for tail_key in self.vertex_table if tail_key in edges_by_tail)
#            ))
#
#        def gen_edge_table_by(vertex_fxn, tup_edge_keys):
#            """
#            Generate a nested hashtable of edges:
#
#                edge_table[key1][key2]
#
#            where $key1 is a <Vertex> and $key2() in $tup_edge_keys.
#            """
#            # determine the different edges to key each <Vertex> to
#            edge_table = {
#                vertex:tuple(e for e in edges if vertex_fxn(e) == vertex)
#                for vertex in self.vertex_table.viewvalues()
#            }
#            # create keys in edge_table[<Vertex>] to look up the edges
#            for vertex in edge_table:
#                e_tuple = edge_table[vertex]
#                edge_table[vertex] = {'edges':e_tuple}
#                for e in e_tuple: 
#                    for key in tup_edge_keys: edge_table[vertex][key(e)] = e
#            return edge_table
#
#        self.edges_by_tail = gen_edge_table_by(
#            lambda e:e.get_tail(),
#            (lambda e:e.get_dir(), lambda e:e.get_head())
#        )
#
#        self.edges_by_head = gen_edge_table_by(
#            lambda e:e.get_head(),
#            (lambda e:e.get_dir(), lambda e:e.get_tail())
#        )
#
    def get_vertex(self, vertex_key):
        """Return the <Vertex> corresponding to $vertex_key."""
        return self.vertex_table[vertex_key]
#
#    def get_prevs(self, vertex):
#        """Return the tuple of direct predecessors of <Vertex> $vertex."""
#        try:
#            vertex = self.nav_vertices[vertex]
#        except KeyError:
#            pass
#        finally:
#            return tuple(
#                e.get_tail() for e in self.edges_by_head[vertex]['edges']
#            )
#
    def get_nexts(self, vertex):
        """Return the tuple of direct successors of <Vertex> $vertex."""
        # get the physically possible successor vertices
        nexts = tuple(self.get_next_via(vertex, d) for d in dirs)
        # filter out successor vertices which it is illegal to go to
        return tuple(n for n in nexts if (vertex, n) not in illegals)
#
#    def get_prev_via(self, vertex, direction):
#        """Return the <Vertex> $prev with DirEdge($prev, $vertex, $dir)."""
#        try: 
#            return self.edges_by_head[vertex][direction].get_prev()
#        except KeyError as e:
#            log_error(e, 'get_prev_via()')
#
#    def get_dir_from_prev(self, vertex, prev_vertex):
#        """Return the $dir in DirEdge($prev, $vertex, $dir)."""
#        try:
#            return self.edges_by_head[vertex][prev_vertex].get_dir()
#        except KeyError as e: 
#            log_error(e, 'get_dir_from_prev()')
#
    def get_next_via(self, vertex, d):
        """Return the <Vertex> $next with DirEdge($vertex, $next, $dir)."""
        try:
            return self.get_vertex(
                    '[{r},{c}]'.format( r = vertex.row + dirs[d][0],
                                        c = vertex.column + dirs[d][1])
                    )
        except KeyError as e: 
            # if retrieval attempt is for illegal or non-existent vertex
            return None
#
#    def get_dir_to_next(self, vertex, next_vertex):
#        """Return the $dir in DirEdge($vertex, $next, $dir)."""
#        try:
#            return self.edges_by_tail[vertex][next_vertex].get_dir()
#        except KeyError as e: 
#            log_error(e, 'get_dir_to_next()')


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
#    def get_weight(self):
#        """Returns weight of $self.vertex."""
#        return self.vertex.get_weight()
#
#    def get_nexts(self):
#        """Return the tuple of direct successors of <Vertex> $self.vertex."""
#        return self.vertex.get_nexts()
#    
#    def get_avg_creds(self):
#        """Returns average discredits earned per move."""
#        try: return 1.0*self.get_n_credits()/self.get_n_actions()
#        except ZeroDivisionError: return 0.0
#    
#    def get_prev_state(self):
#        """Return the ancestor <State>, None if none exists."""
#        return self.prev_state
#
#    def get_prev_vertex(self):
#        """Return the <Vertex> of the ancestor <State>, None if none exists."""
#        try:
#            return self.get_prev_state().get_vertex()
#        except AttributeError:
#            return None
#    
#    def get_dir_from_prev(self):
#        """Return the direction from self.get_prev() to $self."""
#        if self.dir_from_prev != None: return self.dir_from_prev
#        elif self.get_prev() != None:
#            return self.vertex.get_dir_from_prev(self.get_prev().vertex)
#
#    def get_next_state(self, direction=None, next_vertex=None):
#        """Return state resulting from move in $direction or to $next_vertex."""
#        if (direction, next_vertex).count(None) != 1:
#            raise ValueError(
#                'get_next_state() takes either $direction or $next_vertex'
#            )
#
#        # warning: hardcoded different navigation directions
#        if direction != None and direction not in ('left','stay','right'): 
#            raise ValueError('received invalid $direction: %s' % direction)
#
#        if direction == None:
#            direction = self.vertex.get_dir_to_next(next_vertex)
#        if next_vertex == None: 
#            next_vertex = self.vertex.get_next_via(direction)
#
#        return State(
#            self.instance, 
#            vertex = next_vertex,
#            count_credits = self.get_n_credits() + next_vertex.get_weight(),
#            count_actions = self.get_n_actions() + 1,
#            prev_state = self, dir_from_prev = direction)
#
#    def get_next_states(self):
#        """Return tuple of possible successor states of $self."""
#        return tuple(self.get_next_state(next_vertex=vertex) 
#                     for vertex in self.vertex.get_nexts())

    
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
