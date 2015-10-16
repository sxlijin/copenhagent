#! /usr/bin/env python

import structs

class NavigationInstance:
    """immutable, saves a problem instance for a game of Navigation."""
    def __init__(self, shell, debug=False):
        """call nav/enter() and parse returned FullResponse"""
        
        self.debug = debug
        self.token = shell.active_agent.agent_token

        self.try_command = shell.try_command
        
        r = self.try_command('navigation enter')

        # begin parsing the FullResponse
        nav_setup = r.json()['state']['navigation'][self.token]
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
        print ' %7s; avg creds is %5.2f (%3d creds in %2d moves)' % (
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
        log_msg = '%s  [%s] <%s> ' % ('='*29, alg_name, msg)
        print log_msg + '='*(55 - len(log_msg))

    def cmd_nav_moves(self, moves):
        """Command agent to make a move in navigation."""
        # if passed a $direction
        if type(moves) in (str, unicode):
            return self.nav_inst.try_command(
                'navigation lane direction=%s' % moves)
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
        return self.nav_inst.try_command('navigation leave')
    
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
    #   don't add edges if current best avg impossble to beat
    #   try doing a custom version using a priority queue?
    #       python best bet is using a heapq
    def nav_generic_first_by_struct(self, data_struct):
        alg_names = {
            'Queue':'generic breadth first', 
            'Stack':'generic depth first'
        }
        alg_name = alg_names[data_struct.name()]
        self.log_alg_start(alg_name)
        
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
            s = frontier.rm()

            # is s.prev the most optimal path?
            # if not should discard

            #if s.get_weight() < seed:
            #    print "skip %s %s < %s" % (s.get_pos(), s.get_weight(), seed)
            #    continue
    
            # if current NavState has not yet been explored
            #       OR has been explored & NavEdge is better path
            # use s.get_pos() as key bc can have different $s at same vertex
            if (s.get_pos() not in explored 
                    or s.get_avg_creds() > explored[s.get_pos()]['avg']): 

                # overwrite or create item with NavEdge in value 
                explored[s.get_pos()] = {'avg':s.get_avg_creds()}

                # if current NavEdge is better than current best path
                if s.get_avg_creds() > best_end.get_avg_creds(): best_end = s
            else:
                continue
            # add a continue 

            #if self.debug: s.log()
            #if self.debug: print id(s)
            # add potential next moves to the frontier
            for result in s.get_results().viewvalues():
                # never add a vertex with weight < seed to the frontier
                if result.get_weight() >= seed:  frontier.add(result)
                elif self.debug:    print 'not adding %s' % result
        
        # log last edge in best path
        if self.debug: best_end.log()
        
        # regenerate best path from its terminal edge
        # work backwards until NavState.prev == (initial_state.prev = None)
        hist = structs.Stack()
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

        self.log_alg_end(alg_name)

    def nav_generic_breadth_first(self):
        """Runs a breadth first search using a generic search with a queue."""
        self.nav_generic_first_by_struct(Queue())

    def nav_generic_depth_first(self):
        """Runs a depth first search using a generic search with a stack."""
        self.nav_generic_first_by_struct(Stack())


