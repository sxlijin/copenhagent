#! /usr/bin/env python

import structs
from logger import *

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
        ps_json_vertex = ps_vertices[self.vertex_key]
        self.ps_row = ps_json_vertex['row']
        self.ps_column = ps_json_vertex['column']

        self.neighbors = {}
        for d in self.dirs:
            neighbor = {   'row'   :   self.get_row() + self.dirs[d][0],
                           'column':   self.get_column() + self.dirs[d][1] }
            self.neighbors[d] = '[{row},{column}]'.format(**neighbor)


#unk#        self.next_vertices = {}
#unk#        for d in self.dirs:
#unk#            if d in ps_json_vertex: continue # skip if edge marked
#unk#
#unk#            successor = {   'row'   :   self.get_row() + self.dirs[d][0],
#unk#                            'column':   self.get_column() + self.dirs[d][1] }
#unk#            successor_key = '[{row},{column}]'.format(**successor)
#unk#            if successor_key in ps_vertices:
#unk#                self.next_vertices[successor_key] = d

        self.move_again = ps_json_vertex.get('visited', False)

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
        return self.neighbors[direction]
#unk#
#unk#    def get_dir_to_next(self, next_vertex):
#unk#        """Return the $dir in DirEdge($self, $next, $dir)."""
#unk#        return self.graph.get_dir_to_next(self, next_vertex)


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

        for vertex in self.vertex_table.viewvalues():
            vertex.neighbors = {   self.vertex_table[key] 
                                        for key in vertex.neighbors 
                                        if key in self.vertex_table     }

        #self.visited_table = { vertex:{} for vertex in self.vertex_table }
        self.visited_table = ps_json_graph['edges']


          
    def get_vertex(self, vertex_key):
        """Return the <Vertex> corresponding to $vertex_key."""
        return self.vertex_table[vertex_key]

    def get_nexts(self, vertex):
        # $nexts should be a list of lists of moves
        nexts = []
        #neighbors = [   self.vertex_table[key]
        #                for key in vertex.neighbors.viewvalues()
        #                if key in self.vertex_table     ]
#
        frontier = structs.Queue()
        for key in vertex.neighbors.viewvalues():
            try:    frontier.add( [self.vertex_table[key]] )
            except KeyError: pass

        while not frontier.is_empty():
            next_seq = frontier.rm()
            if next_seq[-1].move_again:
                pass
                # ???
                # problem is same as below:
                # how do you consider moves that have been made earlier in the sequence?
                # maybe it would be better to adjust minimax so that it uses next.move_again
            else:
                nexts.append( next_seq )

        
        for key in vertex.neighbors.viewvalues():

            if key not in self.vertex_table: continue
            neighbor = self.vertex_table[key]
            if neighbor.move_again:
                ### below has infinite recursion problem
                #nexts.extend(   [neighbor].extend(next_seq) 
                #                for next_seq in self.get_nexts(neighbor)    )
            else:
                nexts.append( [neighbor] )
        return nexts       


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
        self.curr_vertex = self.graph.get_vertex(
            '[{row},{column}]'.format(**ps_setup['currentVertex']))

    def get_current(self): 
        """Returns <Vertex> specified to be initial position."""
        return self.curr_vertex

    def get_seed(self):
        """Return the seed for the NavInst."""
        return self.seed

    def update_with_dir(self, direction):
        """Update the Instance and Graph by moving the ball in a given direction."""
        dest_vertex = self.get_current().get_next_via(direction)
        graph.visited_table[curr_vertex][dest_vertex] = 'visited'
        graph.visited_table[dest_vertex][curr_vertex] = 'visited'
        self.curr_vertex = dest_vertex
        
    
class Agent:
    """Agent to play a Instance."""
    
    def __init__(self, instance, state=None, debug=False):
        self.instance = instance
        #self.state = State(instance) if state == None else state
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
            r = self.instance.try_command(
                'papersoccer play direction=%s' % moves)
            if r.status_code == 200:
                for d in [moves].extend(r.json()['percepts']):
                    self.instance.update_with_dir(d)
            return r
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

    def stupid(self):
        """Stupid try e then ne then se."""
