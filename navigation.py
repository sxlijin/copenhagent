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
            """
            Generate a nested hashtable of edges:

                edge_table[key1][key2]

            where $key1 is a <Vertex> and $key2() in $tup_edge_keys.
            """
            # determine the different edges to key each <Vertex> to
            edge_table = {
                vertex:tuple(e for e in edges if vertex_fxn(e) == vertex)
                for vertex in self.vertex_table.viewvalues()
            }
            # create keys in edge_table[<Vertex>] to look up the edges
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
        self.shell = shell
        self.token = self.shell.active_agent.agent_token

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

    def get_initial(self): 
        """Returns <Vertex> specified to be initial position."""
        return self.init_vertex

    def get_seed(self):
        """Return the seed for the NavInst."""
        return self.seed

class State:
    """An immutable State within an Instance."""
    
    def __init__(self, instance,
            vertex=None, count_credits=None, count_actions=None,
            prev_state=None, dir_from_prev=None):
        """Contruct a NavState: track NavInst, pos, #credits, #moves, $prev."""
        # NOTE: if NavState is made mutable, MUST implement deepcopy()
        self.instance = instance
        self.vertex = instance.get_initial() if vertex == None else vertex

        if count_credits == None:
            try:
                self.count_credits = instance.shell.active_agent.n_credits
            except AttributeError:
                self.count_credits = 0
        else:
            self.count_credits = count_credits

        if count_actions == None:
            try:
                self.count_actions = instance.shell.active_agent.n_actions
            except AttributeError:
                self.count_actions = 0
        else:
            self.count_actions = count_actions

#        try:
#            self.count_credits = instance.shell.active_agent.n_credits
#            self.count_actions = instance.shell.active_agent.n_actions
#        except AttributeError:
#            self.count_credits = 0 if count_credits == None else count_credits
#            self.count_actions = 0 if count_actions == None else count_actions
        # save previous state
        self.prev_state = prev_state
        self.dir_from_prev = dir_from_prev
 
    def __str__(self):
        return '%7s with avg of %5.2f (%3d creds in %2d moves)' % (
            self.get_vertex(), self.get_avg_creds(), 
            self.get_n_credits(), self.get_n_actions())

    def __lt__(self, other): return self.get_avg_creds() < other.get_avg_creds()
    def __le__(self, other): return self.get_avg_creds() <= other.get_avg_creds()
    def __gt__(self, other): return self.get_avg_creds() > other.get_avg_creds()
    def __ge__(self, other): return self.get_avg_creds() >= other.get_avg_creds()
    # do not implement __eq__ or __ne__: want those two to default to using id()

    #def get_deepcopy(self):
    #    """Return deepcopy of internal state."""
    #    # MUST implement if NavState is made mutable
    #    return self
    
    def get_vertex(self):
        """Returns current position."""
        return self.vertex
    
    def get_n_credits(self):
        """Returns number of earned discredits."""
        return self.count_credits

    def get_n_actions(self):
        """Returns number of moves made."""
        return self.count_actions
    
    def get_weight(self):
        """Returns weight of $self.vertex."""
        return self.vertex.get_weight()

    def get_nexts(self):
        """Return the tuple of direct successors of <Vertex> $self.vertex."""
        return self.vertex.get_nexts()
    
    def get_avg_creds(self):
        """Returns average discredits earned per move."""
        try: return 1.0*self.get_n_credits()/self.get_n_actions()
        except ZeroDivisionError: return 0.0
    
    def get_prev_state(self):
        """Return the ancestor <State>, None if none exists."""
        return self.prev_state

    def get_prev_vertex(self):
        """Return the <Vertex> of the ancestor <State>, None if none exists."""
        return self.get_prev_state().get_vertex()
    
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
            count_credits = self.get_n_credits() + next_vertex.get_weight(),
            count_actions = self.get_n_actions() + 1,
            prev_state = self, dir_from_prev = direction)

    def get_next_states(self):
        """Return tuple of possible successor states of $self."""
        return tuple(self.get_next_state(next_vertex=vertex) 
                     for vertex in self.vertex.get_nexts())

    
class Agent:
    """Agent to play a Instance."""
    
    def __init__(self, instance, state=None, debug=False):
        self.instance = instance
        self.state = State(instance) if state == None else state
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
            #log('sending command', 'navigation lane direction=%s' % moves)
            return self.instance.try_command(
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
        return self.instance.try_command('navigation leave')
    
    def nav_random(self):
        self.alg_log_start('random walk')
        # NOTE: warning, this binds $s to $self.state
        # if State is changed to be mutable, $s must be a deepcopy()
        s = self.state
        moves = []
        while s.get_nexts() != {} : 
            if self.debug: s.log()
            successors = s.get_nexts()
            s = sucessors[randint(0, len(successors)-1)]
        self.alg_log_end('random walk')
        self.prompt_cmd_nav_leave()
    
    # this is a hill-climber, not a greedy-best-first
    def nav_greedy_best_first(self):
        self.alg_log_start('greedy best first')
        # NOTE: warning, this binds $s to $self.state
        # if State is changed to be mutable, $s must be a deepcopy()
        s = self.state
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
    # frontier = DataStructure()
    # frontier.add(walk)
    # 
    # while (goal not met) or (frontier not empty):
    #   frontier.insertset(walk.nexts)
    #   walk <- frontier.next
    # 
    # if (goal met): return goal state
    # 
    # =========================================================================
    #
    # extending this to a graph search:
    #
    # explored = {} 
    # // keys   : <Vertex>
    # // values : <State>
    # // unique (key, value) pairs because you overwrite with better <State>s
    # // do not need to record paths if <State> points to best predecessor
    # 
    # walk_state = initial_state
    # frontier = DataStructure()
    # frontier.add(walk_state)
    # 
    # while frontier not empty:
    #   walk_state <- frontier.rm()
    #
    #   // if current <Vertex> has been explored
    #   if walk_state.get_vertex() is in explored:
    #       // and path corresp. to current <State> is better than recorded <State>
    #       if current average > recorded average:
    #           explored[<Vertex>] <- walk_state
    #       // but if not, do not continue expanding $walk_state
    #       else:
    #           continue
    #   // if current <Vertex> unexplored, record current <State>
    #   else:
    #       explored[<Vertex>] <- walk_state
    #
    # <State> records best path from predecessor
    # this *must* be the case:
    #   say $stateA and $stateB are <State>s at the same <Vertex>
    #       and followed different paths to <Vertex>, so $stateA is better
    #   then $stateB will *not* be expanded because $explored dictates thus
    #   
    #   if $stateB found first, and its successors are added to the frontier
    #       before $stateA is found, then if $stateB successors are expanded,
    #       they will always be overwritten by the corresp. $stateA successor
    #
    # potential optimizations:
    #   do not expand successors if their $prev_state has been overwritten
    #   don't add edges if current best avg impossble to beat
    #   try doing a custom version using a priority queue? (use heapq)
    def nav_generic_first_by_struct(self, data_struct):
        alg_names = {
            'Queue':'gen. breadth first', 
            'Stack':'gen. depth first',
            'PriorityQueue':'gen. greedy best first'
        }
        alg_name = alg_names[data_struct.name()]
        self.alg_log_start(alg_name)
        
        # track explored vertices as { <Vertex> : <State> }
        #   overwriting a <State> if new <State> is better
        # track the best path according to its terminal node
        s = self.state
        frontier = data_struct
        frontier.add(s)
        explored = {}

        # initialize best <State> found so far
        best_terminal_state = s

        seed = s.instance.get_seed()
        
        # note: Navigation is curious because there is no way to test if a
        #       specific <State> is a goal <State>, because the goal of
        #       <copenhagent> is to maximize credits earned per move, so you
        #       can only find a goal state once the set of best terminal
        #       <State>s is generated (by finding the best of the set)
        #
        # e.g., goal <State> might have successor <State>s
        #       because continuing to move would lower the average
        #
        # NOTE: what if even the best Navigation solution would lower
        #       the agent's current average credits?
        while not frontier.is_empty():
            # $s is the current NavState being expanded
            s = frontier.rm()

            # if current <State> better than recorded <State> for <Vertex>
            if (s.get_vertex() not in explored 
                    or s.get_prev_state() == explored.get(s.get_prev_vertex(), 
                                                          None)
                    or s > explored[s.get_vertex()]):

                # overwrite or create entry corresponding to <Vertex>
                explored[s.get_vertex()] = s #{'avg':s.get_avg_creds()}

                # record best <State> to end at if discovered
                if s > best_terminal_state: best_terminal_state = s
                
            # otherwise, skip to next item in frontier
            else:
                continue

            #if self.debug: log('current <State>', s)
            # add potential next moves to the frontier
            for result in s.get_next_states():
                # never add a vertex with weight < seed to the frontier
                if result.get_weight() >= seed:  frontier.add(result)
                elif False and self.debug: log('searching', 'discarding %s' % result)
        
        # more efficient to ~seq search in the loop, presumably becaues of
        # o(1) hashtable lookups and compares that mean you check less states
        # so this is actually *less* efficient:
        # single trial of 100 runs gives 0.2109698s average below,
        # versus 0.19308929 average for checking in the loop
        #best_terminal_state = max(explored.viewvalues())

        # log last edge in best path
        best_terminal_state.count_actions += 1 # n_actions++ for nav/leave()
        if self.debug: log('found best end state', best_terminal_state)
        
        # regenerate best path from its terminal edge
        # work backwards until NavState.prev == (initial_state.prev = None)
        hist = structs.Stack()
        s = best_terminal_state

        if s > self.state:
            while None != s.get_prev_state():
                hist.push(s)
                s = s.get_prev_state()
    
            # follow the best path forward
            while not hist.is_empty():
                s = hist.pop()
                self.cmd_nav_move(s.get_dir_from_prev())
                if False and self.debug: 
                    log('moving from', 
                          '%7s to %7s via %5s to earn %3d' % (
                            s.get_prev_vertex(),
                            s.get_vertex(),
                            s.get_dir_from_prev(),
                            s.get_weight()
                            )
                         )
        else:
            log('not moving', 's is worse than current state')
            log('current state', s)

        self.alg_log_end(alg_name)

    def nav_generic_breadth_first(self):
        """Runs a breadth first search using a generic search with a queue."""
        self.nav_generic_first_by_struct(structs.Queue())

    def nav_generic_depth_first(self):
        """Runs a depth first search using a generic search with a stack."""
        self.nav_generic_first_by_struct(structs.Stack())

    def nav_generic_greedy_best_first(self):
        """Runs a greedy best first search using a generic search with a PQ."""
        key = lambda x: -x.get_avg_creds()
        self.nav_generic_first_by_struct(structs.PriorityQueue(key))
