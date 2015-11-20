#! /usr/bin/env python

import time, random

import lib.papersoccer
from lib.logger import *

import shell

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
    """Prioritize by rightmost, then number of edges traversed by the move."""
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
        if ps.get_current().is_terminal or len(nexts) == 0: break
    
        # choose a successor state to move to
        # successor SearchNodeWrap discarded because it only records the state
        #   following agent's moves, not following agent's & computer's moves
        play_seq = choose_from_according_to(nexts, heuristic_crude).prev_plays

    return r


###############################################################################
#
#  Implemented for standalone execution.

ps_agent = None
def setup():
    import sys
    s = shell.Shell(token= sys.argv[1])
    s.try_command('papersoccer leave')
    r = s.active_agent.say('test %s' % time.strftime('%H:%M:%S', time.gmtime()))

    ps = lib.papersoccer.Instance(s)
    ps_agent = lib.papersoccer.Agent(instance=ps)

    return ps_agent


if __name__ == '__main__':
    hill_climb(setup())
