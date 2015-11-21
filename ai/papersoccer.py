#! /usr/bin/env python

import time, random

import lib.papersoccer
from lib.logger import *

import shell

dirs = lib.papersoccer.dirs

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


###############################################################################
#
#  Heuristic functions that assess the desirability of a given game board.

def choose_from_according_to(wraps, heuristic, mode=1):
    """Prioritize nodes according to heuristic and return highest-scoring."""
    if mode == -1:  # introduce a option for random
        wraps = random.shuffle(wraps)
    elif mode == 0:
        wraps = sorted(wraps, key=heuristic)
    elif mode == 1:
        wraps = list(reversed(sorted(wraps, key=heuristic, reverse=True)))

    DEBUG = True
    if DEBUG:
        n = 20
        print ' | %d most preferred options are (from least to most):' % n
        for wrap in wraps[-n:]: 
            print ' | %s via %s ' % (wrap.get_current(), wrap.prev_plays)
        print ' | %s' % ('='*(80-3))
        print ' | %s via %s ' % (wrap.get_current(), wrap.prev_plays),
        print 'was chosen from %d options' % len(wraps)
    return wraps[-1]


def heuristic_crude(wrap):
    """Heuristic: score by rightmost, then number of edges traversed by the move."""
    return (    wrap.get_current().get_column(), 
                len(wrap.prev_plays)
                )


def hill_climb(ps_agent):
    """Navigation search algorithm: hill climbing."""
    r = None
    ps = ps_agent.instance

    play_seq = tuple()
    while True:
        for play in play_seq: r = ps_agent.cmd_ps_move(play)

        walk = ps_agent.curr_search_wrap()
        walk.show_nexts()
        nexts = walk.get_nexts()

        # game is over
        if walk.get_current().is_terminal or len(nexts) == 0: break
    
        # choose a successor state to move to
        # successor SearchNodeWrap discarded because it only records the state
        #   following agent's moves, not following agent's & computer's moves
        play_seq = choose_from_according_to(nexts, heuristic_crude).prev_plays

    return r


###############################################################################
#
#  Game-solving algorithms (minimax and alpha-beta) and their helpers

def is_terminal(node):
    return node.get_current().is_terminal or len(node.get_nexts()) == 0


def utility(node, is_my_turn):
    multiplier = 1 if ( (node.get_current() == ps.goal_vertex) or
                        (node.get_nexts() == tuple() and not is_my_turn) ) else -1
    utility = node.n_moves*multiplier 
    #print '  utility is %d for %s' % (utility, node)
    return utility


def minimax(node, is_my_turn):
    if is_terminal(node):   return utility(node, is_my_turn)
    if is_my_turn:
        return max( minimax(next_node, False)
                    for next_node in node.get_nexts().viewvalues())
    else:
        return min( minimax(next_node, True)
                    for next_node in node.get_nexts().viewvalues())


def alphabeta(node, is_my_turn, alpha, beta):
    if is_terminal(node):   return utility(node, is_my_turn)
    if is_my_turn:
        v = float('-inf')
        for next_node in node.get_nexts():
            v = max(v, alphabeta(next_node, False, alpha, beta))
            alpha = max(alpha, v)
            if beta <= alpha: break
        return v
    else:
        v = float('inf')
        for next_node in node.get_nexts():
            v = min(v, alphabeta(next_node, True, alpha, beta))
            beta = min(beta, v)
            if beta <= alpha: break
        return v


def dlminimax(node, is_my_turn, depth):
    print '.',
    #print node.get_current(), is_my_turn, depth
    #print '\t', [str(n.get_current()) for n in node.get_nexts()]
    #print
    if is_terminal(node) or depth > 1:
        #return utility(node, is_my_turn)
#    if depth > 3: 
#        print 'depth limited at %s' % node
        return (heuristic_crude(node), node.prev_plays)
    if is_my_turn:
        return max( (dlminimax(next_node, False, depth + 1)[0], next_node.prev_plays)
                    for next_node in node.get_nexts()  )
        
    else:
        return min( (dlminimax(next_node, True, depth + 1)[0], next_node.prev_plays)
                    for next_node in node.get_nexts()  )

NEGATIVE_INFINITY = (float('-inf'), None)
POSITIVE_INFINITY = (float('inf'), None)

def dlalphabeta(node, is_my_turn, 
                alpha = NEGATIVE_INFINITY,
                beta  = POSITIVE_INFINITY,
                depth = 0):
    print '.',

    if is_terminal(node) or depth == 2:
        return (node.get_current().get_column(), node)

    nexts = node.get_nexts()
    if is_my_turn:
        value = NEGATIVE_INFINITY
        for next_node in sorted(nexts, key=heuristic_crude, reverse=True):
            value = max(value, 
                        (dlalphabeta(next_node, False, alpha, beta, depth + 1)[0], next_node)
                        )
            alpha = max(alpha, value)
            if beta <= alpha: break
        return value

    else:
        value = POSITIVE_INFINITY
        for next_node in sorted(nexts, key=heuristic_crude):
            value = min(value, 
                        (dlalphabeta(next_node, False, alpha, beta, depth + 1)[0], next_node)
                        )
            beta = min(beta, value)
            if beta <= alpha: break
        return value


def play_game(ps_agent):
    move_seq = tuple()
    while True:
        for move in move_seq:   ps_agent.cmd_ps_move(move)

    
        walk = ps_agent.curr_search_wrap()
        if is_terminal(walk): break
        #(heur, move_seq) = dlminimax(walk, True, 0)
        #(heur, move_seq) = dlalphabeta(walk, True)
        (heur, node) = dlalphabeta(walk, True)
        move_seq = node.prev_plays
    
        print
        print heur, move_seq
        raw_input('press enter to execute moves')
    


###############################################################################
#
#  Implemented for standalone execution.

def setup():
    import sys
    s = shell.Shell(token= sys.argv[1])
    s.try_command('papersoccer leave')
    r = s.active_agent.say('test %s' % time.strftime('%H:%M:%S', time.gmtime()))

    ps = lib.papersoccer.Instance(s)
    ps_agent = lib.papersoccer.Agent(instance=ps)

    return ps_agent


if __name__ == '__main__':
    ps_agent = setup()
    #hill_climb(ps_agent)
    play_game(ps_agent)
    raw_input()
    ps_agent.cmd_ps_leave()
