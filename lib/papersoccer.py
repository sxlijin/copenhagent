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
        self.move_again = ps_json_vertex.get('visited', False)
        self.is_terminal = ps_json_vertex['type'] == 'terminal'

        # store the neighbors as <dir>:<Vertex> pairs
        # initialize as <dir>:<key> pairs; Graph() finishes construction
        self.neighbors = {}
        for d in self.dirs:
            neighbor = {   'row'   :   self.get_row() + self.dirs[d][0],
                           'column':   self.get_column() + self.dirs[d][1] }
            self.neighbors[d] = '[{row},{column}]'.format(**neighbor)

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
        
        # store vertices of papersoccer graph
        self.vertex_table = {
            vertex_key:Vertex(self, ps_json_graph, vertex_key)
            for vertex_key in ps_json_graph['vertices'] 
        }
        
        # properly populate the $neighbors dicts with <Vertex>s as values
        for vertex in self.vertex_table.viewvalues():
            vertex.neighbors = {    item[0]:self.get_vertex(item[1])
                                    for item in vertex.neighbors.viewitems()
                                    if item[1] in self.vertex_table     }

        # record visited edges as nested dict
        # if x in edge_table[y], then y in edge_table[x] and x-y was visited
        edges = ps_json_graph['edges']
        self.edge_table = { self.get_vertex(tail)
                            :
                            { self.get_vertex(head) : edges[tail][head]
                              for head in edges[tail]
                            }
                            for tail in edges   }

          
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
        ps_field = ps_setup['soccerfield']
        self.graph = Graph(ps_field)
        
        # store $seed, which is the default weight for nav vertices
        self.seed = ps_config['seed']
        self.curr_vertex = self.graph.get_vertex(
            '[{row},{column}]'.format(**ps_setup['currentVertex']))
        self.curr_vertex.move_again = True
        self.n_moves = 0

        self.goal_vertex = self.graph.get_vertex(
            '[{row},{column}]'.format(  row = ps_field['height']/2,
                                        column = ps_field['width']-1   ))

    def get_current(self): 
        """Returns <Vertex> specified to be initial position."""
        return self.curr_vertex

    def get_seed(self):
        """Return the seed for the NavInst."""
        return self.seed

    def check_traversed(self, tail, head):
        """Return boolean corresp. to whether ($tail, $head) is "traversed"."""
        return head in self.graph.edge_table[tail]

    def check_visited(self, vertex):
        """Return boolean corresp. to whether $vertex has been "visited"."""
        return vertex.move_again

    def update_with_dir(self, direction):
        """Update the Instance and Graph by moving the ball in a given direction."""
        self.n_moves += 1
        dest_vertex = self.get_current().get_next_via(direction)
        if self.debug:
            print 'went %s from %s to %s' % (direction, self.get_current(), dest_vertex)
        self.graph.edge_table[self.curr_vertex][dest_vertex] = 'visited'
        self.graph.edge_table[dest_vertex][self.curr_vertex] = 'visited'
        self.curr_vertex = dest_vertex
        self.curr_vertex.move_again = True
        
class SearchNode:
    """The Nodes for search algorithms to use."""

    #def __init__(self, prev_node, curr_search, searched):
    def __init__(self, prev_node, curr_vertex, moves):
        self.prev_node = prev_node  # point to the preceding search node
        self.curr_vertex = curr_vertex
        self.moves = moves
        #self.curr_search = curr_search  # save the path of the current search
        #self.curr_vertex = self.curr_search[-1] # DANGEROUS: makes jumps possible

        prev_vertex = self.prev_node.get_current()
        self.visited = (    (prev_vertex, self.curr_vertex), 
                            (self.curr_vertex, prev_vertex)     )
        
        #searched[prev_vertex][self.curr_vertex] = self.curr_search
        #searched[self.curr_vertex][prev_vertex] = self.curr_search

        #try:
        #    self.curr_vertex = self.curr_vertex.get_next_via(dir_from_prev)
        #except KeyError:
        #    pass # if $dir_from_prev is None, for initial SearchNode

    def get_current(self):
        """Return the vertex corresponding to this node of the search."""
        return self.curr_vertex

    def check_traversed(self, tail, head):
        """Return boolean corresp. to whether (tail, head) edge traversed."""
        return ((tail, head) in self.visited or 
                self.prev_node.check_traversed(tail, head)
                )

    def check_visited(self, vertex=None):
        """Return boolean corresp. to whether $vertex has been visited."""
        if vertex == None: vertex = self.get_current()
        return (self.get_current() == vertex or 
                self.prev_node.check_visited(vertex)
                )

    def get_next(self, direction):
        """Return the successor SearchNode corresp. to $direction."""
        return SearchNode(  self, 
                            self.curr_vertex.get_next_via(direction), 
                            self.moves+1)

    def get_nexts(self):
        """Return the successor SearchNodes."""
        return tuple(   SearchNode(self, vertex, self.moves+1)
                        for vertex in self.curr_vertex.neighbors.viewvalues()
                        if not self.check_traversed(self.get_current(), vertex)
                        )

    def show_nexts(self):
        """Graphically show the grid from current to the successors."""
        
        nexts = [nx.get_current() for nx in self.get_nexts()]

        grid = list(self.get_current().neighbors.values())
        grid.append(self.get_current())
        grid = sorted(grid, key=str)
        grid = [pt if pt in nexts else '-'*5 for pt in grid]

        print '\n +-- nexts of %s are:\n |' % self.get_current()
        print ('\n | %5s   %5s   %5s\n |'*(len(grid)/3))[1:] % tuple(grid)

        
    
class Agent:
    """Agent to play a Instance."""
    
    def __init__(self, instance, state=None, debug=False):
        self.instance = instance
        #self.state = State(instance) if state == None else state
        self.debug = debug
    
    def __str__(self):
        return self.instance.get_current()
    
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
            if r.status_code == 200 and r.json()['action']['applicable']:
                print '\n(me)  %s ->  ' % moves,
                print '(cpu) ',
                for move in r.json()['action']['percepts']: print move, ' -> ',
                print '\n'
                for d in [moves] + r.json()['action']['percepts']:
                    self.instance.update_with_dir(d)
            return r

    def cmd_ps_leave(self):
        """Command agent to leave papersoccer."""
        return self.instance.try_command('papersoccer leave')
