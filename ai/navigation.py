#! /usr/bin/env python

import random

import lib.structs, lib.navigation
from lib.logger import *
 

def random_walk(nav_agent):
    """Navigation algorithm: random walk."""
    nav_agent.alg_log_start('random walk')
    s = nav_agent.state
    while s.get_next_states() != () :
        s = random.choice(s.get_next_states())
        nav_agent.cmd_nav_move(s)
    nav_agent.alg_log_end('random walk')
#    return nav_agent.cmd_nav_leave()


def hill_climb(nav_agent):
    """Navigation search algorithm: hill climbing."""
    nav_agent.alg_log_start('hill climb')
    s = nav_agent.state
    while s.get_next_states() != () : 
        s = max(s.get_next_states())
        if s < s.get_prev_state(): break
        nav_agent.cmd_nav_move(s)
    nav_agent.alg_log_end('hill climb')
#    return nav_agent.cmd_nav_leave()


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
# extending this to a graph search for Navigation:
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
def generic_first_by_struct(nav_agent, data_struct):
    """
    Navigation search algorithm: generic form, whichever $data_struct it 
    uses for the frontier determines its efficiency.
    """

    alg_names = {
        'Queue':'gen. breadth first', 
        'Stack':'gen. depth first',
        'MinPriorityQueue':'gen. greedy best first'
    }
    alg_name = alg_names[data_struct.name()]
    nav_agent.alg_log_start(alg_name)
    
    # track explored vertices as { <Vertex> : <State> }
    #   overwriting a <State> if new <State> is better
    # track the best path according to its terminal node
    s = nav_agent.state
    frontier = data_struct
    frontier.add(s)
    explored = {}
    explored[None] = None

    # initialize best <State> found so far
    best_terminal_state = s

    seed = s.instance.get_seed()
    
    # note: Navigation is curious because there is no way to test if a
    #       specific <State> is a goal <State>, because the goal of
    #       <copenhnav_agent> is to maximize credits earned per move, so you
    #       can only find a goal state once the set of best terminal
    #       <State>s is generated, by choosing the best vertex to end at;
    #       this happens to mean that it is also possible to end at the
    #       initial vertex if the seed is well below the current average
    #
    # e.g., goal <State> might have successor <State>s
    #       because continuing to move would lower the average
    while not frontier.is_empty():
        # $curr is the current NavState being expanded
        curr = frontier.rm()

        # if current <State> better than recorded <State> for <Vertex>
        # note: the other way to process successor nodes is to add them to
        #       the frontier, then remove them and determine whether they 
        #       should be expanded; this is inefficient because of the
        #       read/write operations to $explored and $frontier
        for s in curr.get_next_states():
            # skip 
            if s.get_vertex() in explored and s <= explored[s.get_vertex()]:
                continue

            explored[s.get_vertex()] = s
            frontier.add(s)

            if s > best_terminal_state: best_terminal_state = s

    # best_terminal_state determined by a pseudo seq search in the loop,
    # since runtime testing shows that it has a 20ms advantage over using
    # max(explored.viewvalues()) after loop termination: presumably because
    # o(1) hashtable lookups and fewer compares occur during the loop
    
    # log last edge in best path
    best_terminal_state.count_actions += 1 # n_actions++ for nav/leave()
    if nav_agent.debug: log('found best end state', best_terminal_state)
    
    # regenerate best path from its terminal edge
    # work backwards until NavState.prev == (initial_state.prev = None)
    hist = lib.structs.Stack()
    s = best_terminal_state

    while None != s.get_prev_state():
        hist.push(s)
        s = s.get_prev_state()

    # follow the best path forward
    while not hist.is_empty():
        s = hist.pop()
        nav_agent.cmd_nav_move(s.get_dir_from_prev())
        if False and nav_agent.debug: 
            log('moving from', 
                  '%7s to %7s via %5s to earn %3d' % (
                    s.get_prev_vertex(),
                    s.get_vertex(),
                    s.get_dir_from_prev(),
                    s.get_weight()
                    )
                 )

    nav_agent.alg_log_end(alg_name)
#    return nav_agent.cmd_nav_leave()

def generic_breadth_first(nav_agent):
    """
    Navigation search algorithm: breadth first search.
    
    Uses generic search with a queue.
    """
    generic_first_by_struct(nav_agent, lib.structs.Queue())

def generic_depth_first(nav_agent):
    """
    Navigation search algorithm: depth first search.
    
    Uses generic search with a stack.

    Results of one trial at noerrebrogade:
    
    [ 0.28362500 ] gen. greedy best fir : START
    [ 277.21395900 ] found best end state :  [4,18] with avg of  4.34 (23562 creds in 5424 mov
    [ 277.25458000 ] gen. greedy best fir : END
    [ 277.25473800 ] nav_solve      <end> :
    [ 277.25477300 ] nav_solve  <runtime> :  nav_solve() runtime was 276.97124300
    """
    generic_first_by_struct(nav_agent, lib.structs.Stack())

def generic_greedy_best_first(nav_agent):
    """
    Navigation search algorithm: greedy best first search.
    
    Uses generic search with a PQ.
    
    Results of one trial at noerrebrogade:

    [ 0.33325400 ] nav_solve    <start> :
    [ 0.33337000 ]     gen. depth first : START
    [ 565.80734400 ] found best end state : [10,18] with avg of  4.35 (23703 creds in 5445 mov
    [ 565.84639700 ]     gen. depth first : END
    [ 565.84652300 ] nav_solve      <end> :
    [ 565.84654700 ] nav_solve  <runtime> :  nav_solve() runtime was 565.51326900
    """
    key = lambda x: -x.get_avg_creds()
    generic_first_by_struct( nav_agent, 
                                    lib.structs.MinPriorityQueue(key) )
