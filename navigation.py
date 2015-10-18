#! /usr/bin/env python

import structs

from copenhagent import Logger
l = Logger()
log = l.log

def log_error(event, e):
    log(event, '%s, %s' % (type(e).__name__, e.message))

class Vertex:
    """
    Builds an immutable representation of a vertex in a Navigation graph.
    """
    
    def __init__(self, graph, nav_json_graph, key):
        """Construct the vertex corresponding to $key in $nav_graph."""
        self.graph = graph
        self.vertex_key = key
        nav_vertex = nav_json_graph['vertices'][self.vertex_key]
        self.nav_row = nav_vertex['row']
        self.nav_column = nav_vertex['column']
        self.nav_weight = nav_vertex['weight']

    def __str__(self):
        return self.vertex_key

    def __lt__(self, that):
        if self.get_column() == that.get_column():  
            # if in the same column, whichever one is above the other
            return self.get_row() < that.get_row()
        else:
            # if not in the same column, the leftmost one
            return self.get_column() < that.get_column()

    def __hash__(self):
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
        return self.nav_row

    def get_column(self):
        """Return the column number of the vertex."""
        return self.nav_column

    def get_weight(self):
        """Return the weight of the vertex."""
        return self.nav_weight

    def get_nexts(self):
        """Return the tuple of direct successors of <Vertex> $self."""
        return self.graph.get_nexts(self)

    def get_prev_via(self, direction):
        """Return the <Vertex> $prev with DirEdge($prev, $self, $dir)."""
        return self.graph.get_prev_via(self, direction)

    def get_dir_from_prev(self, prev_vertex):
        """Return the $dir in DirEdge($prev, $self, $dir)."""
        return self.graph.get_dir_from_prev(self, prev_vertex)

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
    Builds an immutable representation of a Navigation graph.
    """

    def __init__(self, nav_json_graph):
        """Parse the JSON to save the graph of Navigation.Instance."""
        self.nav_json_graph = nav_json_graph
        self.vertex_table = {
            vertex_key:Vertex(self, nav_json_graph, vertex_key)
            for vertex_key in nav_json_graph['vertices'] 
        }

        edges_by_tail = nav_json_graph['edges']
        edges = tuple(frozenset().union(
            *(frozenset().union(
                DirEdge(self.get_vertex(tail_key),
                        self.get_vertex(edges_by_tail[tail_key][direction]),
                        direction)
                for direction in edges_by_tail[tail_key]
              ) for tail_key in self.vertex_table if tail_key in edges_by_tail)
            ))

        def gen_edge_table_by(vertex_fxn, tup_edge_keys):
            edge_table = {
                vertex:tuple(e for e in edges if vertex_fxn(e) == vertex)
                for vertex in self.vertex_table.viewvalues()
            }
            for vertex in edge_table:
                e_tuple = edge_table[vertex]
                edge_table[vertex] = {'edges':e_tuple}
                for e in e_tuple: 
                    for key in tup_edge_keys: edge_table[vertex][key(e)] = e
            return edge_table

        self.edges_by_tail = gen_edge_table_by(
            lambda e:e.get_tail(),
            (lambda e:e.get_dir(), lambda e:e.get_head())
        )

        self.edges_by_head = gen_edge_table_by(
            lambda e:e.get_head(),
            (lambda e:e.get_dir(), lambda e:e.get_tail())
        )

        #self.edges_by_tail = {
        #    vertex:tuple(e for e in edges if e.get_tail() == vertex)
        #    for vertex in self.vertex_table.viewvalues()
        #}

        #self.edges_by_head = {
        #    vertex:tuple(e for e in edges if e.get_head() == vertex)
        #    for vertex in self.vertex_table.viewvalues()
        #}

    def get_vertex(self, vertex_key):
        """Return the <Vertex> corresponding to $vertex_key."""
        return self.vertex_table[vertex_key]

    def get_prevs(self, vertex):
        """Return the tuple of direct predecessors of <Vertex> $vertex."""
        try:
            vertex = self.nav_vertices[vertex]
        except KeyError:
            pass
        finally:
            return tuple(
                e.get_tail() for e in self.edges_by_head[vertex]['edges']
            )

    def get_nexts(self, vertex):
        """Return the tuple of direct successors of <Vertex> $vertex."""
        try:
            vertex = self.nav_vertices[vertex]
        except KeyError:
            pass
        finally:
            return tuple(
                e.get_head() for e in self.edges_by_tail[vertex]['edges']
            )

    def get_prev_via(self, vertex, direction):
        """Return the <Vertex> $prev with DirEdge($prev, $vertex, $dir)."""
        try: 
            return self.edges_by_head[vertex][direction].get_prev()
        except KeyError as e:
            log_error('get_prev_via()', e)

    def get_dir_from_prev(self, vertex, prev_vertex):
        """Return the $dir in DirEdge($prev, $vertex, $dir)."""
        try:
            return self.edges_by_head[vertex][prev_vertex].get_dir()
        except KeyError as e: 
            log_error('get_dir_from_prev()', e)

    def get_next_via(self, vertex, direction):
        """Return the <Vertex> $next with DirEdge($vertex, $next, $dir)."""
        try:
            return self.edges_by_tail[vertex][direction].get_head()
        except KeyError as e: 
            log_error('get_next_via()', e)

    def get_dir_to_next(self, vertex, next_vertex):
        """Return the $dir in DirEdge($vertex, $next, $dir)."""
        try:
            return self.edges_by_tail[vertex][next_vertex].get_dir()
        except KeyError as e: 
            log_error('get_dir_to_next()', e)


class Instance:
    """Builds an immutable representation of a Navigation problem instance."""

    def __init__(self, shell, debug=False):
        """call nav/enter() and parse returned FullResponse"""
        
        self.debug = debug
        self.token = shell.active_agent.agent_token

        self.try_command = shell.try_command
        
        r = self.try_command('navigation enter')

        # begin parsing the FullResponse
        nav_setup = r.json()['state']['navigation'][self.token]
        nav_config = nav_setup['config']
        self.graph = Graph(nav_setup['graph'])
        
        # store $seed, which is the default weight for nav vertices
        self.seed = nav_config['seed']
        self.init_vertex = self.graph.get_vertex(
            '[{row},{column}]'.format(**nav_setup['position']))

    # methods to access the internal state and its characteristics
    def get_initial(self): 
        """Returns <Vertex> specified to be initial position."""
        return self.init_vertex

    def get_seed(self):
        """Return the seed for the NavInst."""
        return self.seed

#del#    def get_weight(self, vertex): 
#del#        """Returns weight of $vertex."""
#del#        return vertex.get_weight()
#del#        return self.vertex_weight[vertex]
#del#        # post-restructure: unnecessary (Vertex.get_weight())

#del#    def get_nexts_from(self, vertex): 
#del#        """Return dict of possible moves from $vertex
#del#        where directions are keys and destinations are values;
#del#        current pos is default vertex."""
#del#        return vertex.get_nexts()
#del#        return self.vertex_nexts[vertex]
#del#        # post-restructure: unnecessary (Vertex.get_nexts(), graph.get_nexts())

#del#    def get_dest_from_via(self, vertex, direction):
#del#        """Returns would-be dest of moving in $direction from $vertex."""
#del#        return vertex.get_dest_via(direction)
#del#        return self.get_nexts_from(vertex)[direction]
#del#        # post-restructure: unnecessary (Vertex.get_next_via(), graph.get_next_via())
    
#del#    def get_dir_to_dest(self, vertex, destination):
#del#        """Returns direction to get from $vertex to $destination."""
#del#        nexts = self.get_nexts_from(vertex)
#del#        if destination in nexts.viewvalues():
#del#            # iterate through: no worry about cost because len(nexts[dir]) <= 3
#del#            for direction in nexts: 
#del#                if destination == nexts[direction]: return direction
#del#        # post-restructure: unnecessary (Vertex.get_dir_to_next(), graph.get_dir_to_next())

class State:
    """An immutable State within an Instance."""
    
    def __init__(self, instance,
            vertex=None, count_credits=None, count_moves=None,
            prev_state=None, dir_from_prev=None):
        #    pos=None, creds=None, moves=None, 
        #    prev=None, prev_dir=None):
        """Contruct a NavState: track NavInst, pos, #credits, #moves, $prev."""
        # NOTE: must implement deepcopy() to make NavState mutable
        # adding $nav_inst to NavState does not add significant overhead
        # because $self.nav_inst binds to an existing NavInst
        self.instance = instance
        self.vertex = instance.get_initial() if vertex == None else vertex
        self.count_credits = 0 if count_credits == None else count_credits
        self.count_moves = 0 if count_moves == None else count_moves
        # save previous state
        self.prev_state = prev_state
        self.dir_from_prev = dir_from_prev
 
    def __str__(self):
        return ' %7s; avg is %5.2f (%3d creds in %2d moves)' % (
            self.get_vertex(), self.get_avg_creds(), 
            self.get_n_creds(), self.get_n_moves())

    #def get_deepcopy(self):
    #    """Return deepcopy of internal state."""
    #    # MUST implement if NavState is made mutable
    #    return self
    
    def get_vertex(self):
        """Returns current position."""
        return self.vertex
    
    def get_n_creds(self):
        """Returns number of earned discredits."""
        return self.count_credits

    def get_n_moves(self):
        """Returns number of moves made."""
        return self.count_moves
    
    def get_weight(self):
        """Returns weight of $self.vertex."""
        return self.vertex.get_weight()

    def get_nexts(self):
        """Return the tuple of direct successors of <Vertex> $self.vertex."""
        return self.vertex.get_nexts()
    
#    def get_dest_via(self, direction):
#        """Return would-be dest of moving in $direction from $self.pos"""
#        return self.vertex.get_next_via(direction)

#    def get_dir_to(self, destination):
#        """Return direction to get from $self.pos to $destination."""
#        return self.vertex.get_dir_to_next(destination)
    
    def get_avg_creds(self):
        """Returns average discredits earned per move."""
        try: return 1.0*self.get_n_creds()/self.get_n_moves()
        except ZeroDivisionError: return 0.0
    
    def get_prev_state(self):
        """Return the ancestor NavState (returns None if none exists)."""
        return self.prev_state
    
    def get_dir_from_prev(self):
        """Return the direction from self.get_prev() to $self."""
        if self.dir_from_prev != None: return self.dir_from_prev
        elif self.get_prev() != None:
            return self.vertex.get_dir_from_prev(self.get_prev().vertex)

    def get_next_state(self, direction=None, next_vertex=None):
        """Return state resulting from move in $direction or to $next_vertex."""
        if (direction, next_vertex).count(None) != 1:
            raise ValueError(
                'get_next_state() takes either $direction or $next_vertex'
            )

        # warning: hardcoded different navigation directions
        if direction != None and direction not in ('left','stay','right'): 
            raise ValueError('received invalid $direction: %s' % direction)

        if direction == None:
            direction = self.vertex.get_dir_to_next(next_vertex)
        if next_vertex == None: 
            next_vertex = self.vertex.get_next_via(direction)

        return State(
            self.instance, 
            vertex = next_vertex,
            count_credits = self.get_n_creds() + next_vertex.get_weight(),
            count_moves = self.get_n_moves() + 1,
            prev_state = self, dir_from_prev = direction)

    def get_next_states(self):
        """Return tuple of possible successor states of $self."""
        return tuple(self.get_next_state(next_vertex=vertex) 
                     for vertex in self.vertex.get_nexts())

    
class Agent:
    """Agent to play a Instance."""
    
    def __init__(self, nav_inst, nav_state=None, debug=False):
        self.nav_inst = nav_inst
        self.nav_state = State(nav_inst) if nav_state == None else nav_state
        self.debug = debug
    
    def __str__(self):
        return self.get_pos()
    
    def alg_log_start(self, alg_name):
        """Log the start of a navigation algorithm."""
        if self.debug: self.alg_log_msg(alg_name, 'START')

    def alg_log_end(self, alg_name):
        """Log the start of a navigation algorithm."""
        if self.debug: self.alg_log_msg(alg_name, 'END')

    def alg_log_msg(self, alg_name, msg):
        """Log a message for a navigation algorithm."""
        if self.debug: log(alg_name, msg)

    def cmd_nav_move(self, moves):
        """Command agent to make a move in navigation."""
        # if passed a $direction
        if type(moves) in (str, unicode):
            #l.log('sending command', 'navigation lane direction=%s' % moves)
            return self.nav_inst.try_command(
                'navigation lane direction=%s' % moves)
        # if passed list of moves
        elif type(moves) is list:
            # if moves are in the form of ($direction, $dest_vertex)
            if type(moves[0]) is tuple:
                # move in $direction
                for move in moves: self.cmd_nav_move(move[0])
            # if moves are in the form of $direction
            elif type(moves[0]) is str:
                # move in $direction
                for move in moves: self.cmd_nav_move(move)
    
    def cmd_nav_leave(self):
        """Command agent to leave navigation."""
        return self.nav_inst.try_command('navigation leave')
    
    def prompt_cmd_nav_leave(self):
        """Command agent to leave navigation, pause for user acknowledgment."""
        #if self.debug: raw_input('press enter to leave')
        self.cmd_nav_leave()
    
    def nav_random(self):
        self.alg_log_start('random walk')
        # NOTE: warning, this binds $s to $self.nav_state
        # if State is changed to be mutable, $s must be a deepcopy()
        s = self.nav_state
        moves = []
        while s.get_nexts() != {} : 
            if self.debug: s.log()
            successors = s.get_nexts()
            s = sucessors[randint(0, len(successors)-1)]
#del#            direction = next_dirs.keys()[randint(0, len(next_dirs)-1)]
#del#            # bind $s to a new NavState
#del#            s = s.get_next_state(direction)
#del#            moves.append((direction, s))
#del#        self.cmd_nav_move(moves)
        self.alg_log_end('random walk')
        self.prompt_cmd_nav_leave()
    
    # this is a hill-climber, not a greedy-best-first
    def nav_greedy_best_first(self):
        self.alg_log_start('greedy best first')
        # NOTE: warning, this binds $s to $self.nav_state
        # if State is changed to be mutable, $s must be a deepcopy()
        s = self.nav_state
        moves = []
        while s.get_nexts() != {} : 
            if self.debug: s.log()
            nexts = s.get_nexts()
            # sorted() sorts in ascending order, so grab last element
            direction = sorted(nexts.viewkeys(), key=s.get_avg_if_move)[-1]
            # binds $s to a new NavState
            s = s.get_next_state(direction)
            moves.append((direction, s))
        self.cmd_nav_move(moves)
        self.alg_log_end('greedy best first')
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
    #   don't add edges if current best avg impossble to beat
    #   try doing a custom version using a priority queue?
    #       python best bet is using a heapq
    def nav_generic_first_by_struct(self, data_struct):
        alg_names = {
            'Queue':'gen. breadth first', 
            'Stack':'gen. depth first'
        }
        alg_name = alg_names[data_struct.name()]
        self.alg_log_start(alg_name)
        
        # NavState currently points to its ancestor
        # maybe a more efficient way to represent the directed edges?
        
        # track explored vertices as { $vertex : ($avg_creds, NavEdge) }
        # track explored vertices as { $vertex : $vertex -> best NavState }
        # track the best path according to its terminal node
        s = self.nav_state
        frontier = data_struct
        frontier.add(s)
        explored = {}
        best_end = s

        seed = s.instance.get_seed()
        
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
            s = frontier.rm()

            # is s.prev the most optimal path?
            # if not should discard

            # if current NavState has not yet been explored
            #       OR has been explored & NavEdge is better path
            # use s.get_pos() as key bc can have different $s at same vertex
            if (s.get_vertex() not in explored 
                    or s.get_avg_creds() > explored[s.get_vertex()]['avg']): 

                # overwrite or create item with NavEdge in value 
                explored[s.get_vertex()] = {'avg':s.get_avg_creds()}

                # if current NavEdge is better than current best path
                if s.get_avg_creds() > best_end.get_avg_creds(): best_end = s
            else:
                continue
            # add a continue 

            #if self.debug: log('', s)
            # add potential next moves to the frontier
            for result in s.get_next_states():
                # never add a vertex with weight < seed to the frontier
                if result.get_weight() >= seed:  frontier.add(result)
                elif self.debug: l.log('searching', 'discarding %s' % result)
        
        # log last edge in best path
        if self.debug: log('found best end state', best_end)
        
        # regenerate best path from its terminal edge
        # work backwards until NavState.prev == (initial_state.prev = None)
        hist = structs.Stack()
        s = best_end
        while None != s.get_prev_state():
            hist.push(s)
            s = s.get_prev_state()

        # follow the best path forward
        while not hist.is_empty():
            s = hist.pop()
            self.cmd_nav_move(s.get_dir_from_prev())
            if self.debug: 
                log('moving from', 
                      '%7s to %7s via %5s' % (
                        s.get_prev_state().get_vertex(),
                        s.get_vertex(),
                        s.get_dir_from_prev()
                        )
                     )

        self.alg_log_end(alg_name)

    def nav_generic_breadth_first(self):
        """Runs a breadth first search using a generic search with a queue."""
        self.nav_generic_first_by_struct(Queue())

    def nav_generic_depth_first(self):
        """Runs a depth first search using a generic search with a stack."""
        self.nav_generic_first_by_struct(Stack())


