#! /usr/bin/env python

import math
import structs
from logger import *


dirs = {  'n':(-1,  0),   's':(1,  0),  'w':(0, -1),  'e':(0, 1),
         'nw':(-1, -1),  'sw':(1, -1), 'ne':(-1, 1), 'se':(1, 1)  }


class Vertex:
    """
    Builds an immutable representation of a vertex in a Papersoccer graph.
    """
    def __init__(self, graph, ps_json_graph, key):
        """Construct the vertex corresponding to $key in $ps_graph."""
        self.graph = graph
        self.vertex_key = key

        ps_json_vertex = ps_json_graph['vertices'][self.vertex_key]
        self.ps_row = ps_json_vertex['row']
        self.ps_column = ps_json_vertex['column']
        self.is_terminal = ps_json_vertex['type'] == 'terminal'
        self.move_again = ps_json_vertex.get('visited', False) and not self.is_terminal

        # store the successors as <dir>:<Vertex> pairs
        # initialize as <dir>:<key> pairs; Graph() finishes construction
        self.successors = {}
        if self.is_terminal: return
        for d in dirs:
            neighbor = {   'row'   :   self.get_row() + dirs[d][0],
                           'column':   self.get_column() + dirs[d][1]   }
            self.successors[d] = '[{row},{column}]'.format(**neighbor)

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

    def get_next_via(self, direction):
        """Return the successor by moving in $direction."""
        return self.successors[direction]

    def get_neighbors(self):
        return self.successors.viewitems()


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
        
        # finish populating the $successors dicts with <Vertex>s as values
        for vertex in self.vertex_table.viewvalues():
            vertex.successors = {   direction : self.get_vertex(key)
                                    for (direction, key)
                                    in vertex.successors.viewitems()
                                    if key in self.vertex_table     }

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

    def get_coords(self, row, column):
        """Return the <Vertex> at $row and $column."""
        return self.vertex_table['[{r},{c}]'.format(r=row, c=column)]


class Instance:
    """Builds an immutable representation of a Papersoccer problem instance."""

    def __init__(self, shell):
        """call nav/enter() and parse returned FullResponse"""
        
        self.shell = shell
        token = self.shell.active_agent.agent_token

        r = shell.try_command('papersoccer enter')

        # begin parsing the FullResponse
        ps_setup = r.json()['state']['papersoccer'][token]
        ps_config = ps_setup['config']
        ps_field = ps_setup['soccerfield']
        self.graph = Graph(ps_field)
        
        # store the following:
        #   $seed           the points multiplier
        #   $curr_vertex    the starting position
        #   $n_moves        total number of moves made
        #   $goal_vertex    the vertex at which the agent wins
        self.seed = ps_config['seed']
        self.curr_vertex = self.graph.get_coords(**ps_setup['currentVertex'])
        self.curr_vertex.move_again = True
        self.n_moves = ps_field['playsMade']
        self.goal_vertex = self.graph.get_coords(
                                row = ps_field['height'] / 2,
                                column = ps_field['width'] - 1
                                )

    def get_current(self): 
        """Returns <Vertex> specified to be initial position."""
        return self.curr_vertex

    def get_seed(self):
        """Return the seed for the NavInst."""
        return self.seed

    def check_traversed(self, tail, head):
        """Return boolean corresp. to whether edge has been searched."""
        return head in self.graph.edge_table[tail]

    def check_visited(self, vertex):
        """Return boolean corresp. to whether $vertex has been searched."""
        return vertex.move_again

    def update_with_dir(self, direction):
        """Update the Instance and Graph by moving the ball in a given dir."""
        self.n_moves += 1
        dest_vertex = self.get_current().get_next_via(direction)
        log('updating',
            '%2s from %6s to %6s' % (direction, self.get_current(), dest_vertex)
            )
        self.graph.edge_table[self.curr_vertex][dest_vertex] = 'visited'
        self.graph.edge_table[dest_vertex][self.curr_vertex] = 'visited'
        self.curr_vertex = dest_vertex
        self.curr_vertex.move_again = True


class SearchNodeAtom:
    """The atomic elements of the Nodes for search algorithms to use."""

    def __init__(self, curr_vertex, prev_node, prev_play=''):
        self.curr_vertex = curr_vertex
        self.prev_node = prev_node
        self.prev_play = prev_play
        self.nexts = None

        prev_vertex = self.prev_node.get_current()
        self.visited = (    (prev_vertex, self.curr_vertex), 
                            (self.curr_vertex, prev_vertex)     )

    def get_current(self):
        """Return the vertex corresponding to this node of the search."""
        return self.curr_vertex

    def get_n_moves(self):
        """Return the number of moves made so far."""
        return self.n_moves

    def check_traversed(self, tail, head):
        """Return boolean corresp. to whether edge has been searched."""
        return ((tail, head) in self.visited or 
                self.prev_node.check_traversed(tail, head)
                )

    def check_visited(self, vertex=None):
        """Return boolean corresp. to whether $vertex has been searched."""
        if vertex == None: vertex = self.get_current()
        try:    vertex = vertex.get_current()
        except AttributeError: pass
        return (self.get_current() == vertex or 
                self.prev_node.check_visited(vertex)
                )

    #def get_next(self, direction):
    #    """Return the successor SearchNodeAtom corresp. to $direction."""
    #    # does not check if moving in $direction is legal
    #    return self.nexts[direction]

    
    def get_nexts(self):
        """Return the successor SearchNodeAtoms."""
        if self.nexts == None:
            self.nexts = tuple( SearchNodeAtom(vertex, self, d)
                                for (d, vertex) in self.curr_vertex.successors.viewitems()
                                if not self.check_traversed(self.get_current(), vertex)
                                )
        return self.nexts

    def show_nexts(self):
        """Graphically show the grid from current to the successors."""

        # generate dict of all 8 successors
        neighbors = self.get_current().successors.copy()
        for d in dirs:
            if d not in neighbors:
                v = self.get_current()
                neighbor = {   'row'   :   v.get_row() + dirs[d][0],
                               'column':   v.get_column() + dirs[d][1] }
                neighbors[d] = '[{row},{column}]'.format(**neighbor)
        
        # generate list of successor vertices
        nexts = [nx.get_current() for nx in self.get_nexts()]

        # filter list of successor vertices/successors as follows:
        #   order it from top to down then left to right
        #   prepend + if vertex has been previously visited
        #   replace with ----- if vertex cannot be visited/does not exist
        #   replace $self with --O--
        def sort_key(v):    return tuple(str(v)[1:-1].split(','))
        grid = neighbors.values()
        grid.append(self.get_current().get_key())
        grid = sorted(grid, key=sort_key)
        grid = [('+%s' % pt if self.check_visited(pt) else pt)
                if pt in nexts else '-'*5 for pt in grid]
        grid[4] = '--O--'

        # convert list of vertices to a string
        grid_str = ' %6s ' * 3
        grid_str = ('\n |%s\n |' % grid_str) * 3
        grid_str = grid_str[1:]
        grid_str = grid_str % tuple(grid)

        # print it out
        print '\n +-- nexts of %s are:\n |' % self.get_current()
        print grid_str



###############################################################################
#
#   Ideas to try out:
#       - generate SearchNodeWraps in a tree/dict that gets saved, and as the
#         game progresses, iterate down the tree/dict, updating the history 
#         appropriately
#           > means you save the cost of generating new nodes
#           > all you have to do is expand the tree a bit more
#           > delete nodes corresponding to moves which were not made
#           > probably something to be handled in lib.papersoccer
#
###############################################################################

class SearchNodeWrap:
    """The Nodes for search algorithms to use."""

    def __init__(self, search_node_atom, prev_wrap=None, prev_plays=tuple()):
        self.search_node_atom = search_node_atom

        self.prev_wrap = prev_wrap
        self.prev_plays = prev_plays

        self.nexts = None

    def get_current(self):
        return self.search_node_atom.get_current()

    def check_traversed(self, tail, head):
        return self.search_node_atom.check_traversed(tail, head)

    def check_visited(self, vertex=None):
        return self.search_node_atom.check_visited(vertex)

    def get_next(self, move_seq):
        """
        Return the successor SearchNodeWrap corresponding to $move_seq.
        """
        return self.nexts[tuple(move_seq)]

    def get_nexts(self):
        """
        Returns a tuple of successor SearchNodeWraps.
        
        Does so via iterative graph search with a queue as the frontier.
        """
        if self.nexts != None:   return tuple(self.nexts.viewvalues())

        nexts = dict()
        repl_queue = structs.Queue()
        # queue up tuples (successor Atom, plays to get to $successor)

        def parse_nexts(curr_atom, prev_plays=tuple()):
            for atom in curr_atom.get_nexts():
                #atom.show_nexts()
                play_seq = prev_plays + (atom.prev_play,)
                if curr_atom.check_visited(atom):
#                    print 'move again at %s <- %s <- %s' % (
#                                atom.get_current(),
#                                curr_atom.get_current(), 
#                                prev_plays
#                                )
                    repl_queue.add((atom, play_seq))
                else:
                    nexts[play_seq] = SearchNodeWrap(atom, self, play_seq)

        parse_nexts(self.search_node_atom)

        while not repl_queue.is_empty():
            parse_nexts(*repl_queue.rm())

        self.nexts = nexts
        return self.get_nexts()


    """
    two strategies for get_nexts:

    1: add and replace successors where you move again
        nexts <- (atom -> nexts())
        repl_queue <- (nx in nexts w/ is-visited(nx))
        while not repl_queue -> empty
            expand <- (repl_queue -> rm)
            delete nexts -> expand
            extend nexts by expand -> nexts
            extend repl_queue by (nx in expand -> nexts w/ is-visited(nx))

    2: recurse down
        for (dir, nx) in atom -> nexts
            if not is-visited(nx)
                extend return by nx
            else
                extend return by nx -> nexts
        return

    """
    def get_nexts2(self, ancestor=None):
        """UNTESTED"""

        if self.nexts != None:  return self.nexts

        if ancestor == None: ancestor = self
        next_atoms = self.search_node_atom.get_nexts()
        next_wraps = list()

        for next_node in next_atoms:
            if self.check_visited(next_node):
                next_wraps.extend(
                    SearchNodeWrap( next_node,
                                    ancestor,
                                    self.prev_plays + (next_node.prev_play,)
                                    ).get_nexts(ancestor=ancestor)
                    )
            else:
                next_wraps.append(
                    SearchNodeWrap( next_node,
                                    ancestor,
                                    self.prev_plays + (next_node.prev_play,)
                                    )
                    )

        if ancestor == self:
            self.nexts = next_wraps

        return next_wraps


    def show_nexts(self):
        self.search_node_atom.show_nexts()
            
    
class Agent:
    """Agent to play a Instance."""
    
    def __init__(self, instance, state=None, debug=False):
        self.instance = instance
        self.try_command = self.instance.shell.try_command
        #self.state = State(instance) if state == None else state
        self.debug = debug

        self.curr_wrap = None

        # record move history since last play
        self.my_moves = list()
        self.cpu_moves = list()
    
    def __str__(self):
        return str(self.instance.get_current())

    def cmd_ps_move(self, move):
        """Command agent to make a move in papersoccer."""
        # if passed a $direction
        r = self.try_command('papersoccer play direction=%s' % move)
        if r.status_code == 200 and r.json()['action']['applicable']:
            # reset move history
            if len(self.cpu_moves) > 0: 
                (self.my_moves, self.cpu_moves) = ([], [])

            # record agent's move
            self.my_moves.append(move)
            self.cpu_moves = r.json()['action']['percepts']

            # update internal state
            for d in [move] + self.cpu_moves:
                self.instance.update_with_dir(d)

            # log sequence of consecutive moves
            if len(self.cpu_moves) > 0:
                log('ps_instance updated',
                    '(me) %s -> (cpu) %s' % (  ' -> '.join(self.my_moves), 
                                               ' -> '.join(self.cpu_moves)      )
                    )
        return r

    def cmd_ps_leave(self):
        """Command agent to leave papersoccer."""
        return self.try_command('papersoccer leave')

    def curr_vertex(self):
        """Return the <Vertex> corresp. to the agent's current location."""
        return self.instance.get_current()
    
    def curr_search_wrap(self):
        """Return the search node corresponding to the current state."""
        # generate search nodes if
        #   - no search nodes have yet been generated
        #   - oops
        if self.curr_wrap == None or self.curr_vertex().is_terminal:
            self.curr_wrap = self.generate_curr_search_wrap()

        # if current search node reflects current position, return it
        elif self.curr_wrap.get_current() == self.curr_vertex():
            pass

        # otherwise, current position must be a grandchild of current node
        else:
            try:
                print
                print 'curr_search_wrap() trying to walk down the tree:'
                print '\t', self.curr_wrap.get_current(),
    
                # walk down by my moves
                self.curr_wrap = self.curr_wrap.get_next(self.my_moves)
                print 'via %s to %s' % (self.curr_wrap.prev_plays, self.curr_wrap.get_current()),
    
                # walk down by cpu moves
                self.curr_wrap = self.curr_wrap.get_next(self.cpu_moves)
                print 'via %s to %s' % (self.curr_wrap.prev_plays, self.curr_wrap.get_current())
    
                # complain if something went wrong
                if self.curr_wrap.get_current() != self.curr_vertex():
                    for _ in range(100): print "PROBLEM"
            except TypeError:
                # TypeError: 'NoneType' object has no attribute '__getitem__'
                # is returned if depth 2 subtree of current search node has not
                # been generated, since the subtree is initialized as None
                print '\n\tERROR: walking down the tree failed'
                self.curr_wrap = None
                return self.curr_search_wrap()

        # force generation of depth 2 tree
        #for nx in self.curr_wrap.get_nexts(): nx.get_nexts()
        return self.curr_wrap
        

    def generate_curr_search_wrap(self):
        """Create a new search node wrap corresponding to the current state."""
        return SearchNodeWrap(  SearchNodeAtom( self.instance.get_current(),
                                                self.instance
                                                )
                                )
