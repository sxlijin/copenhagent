#! /usr/bin/env python

import time, sys, random
import shell
import lib.papersoccer
reload(lib.papersoccer)

s = r = ps = ps_agent = None

def setup():
    global s, r, ps, ps_agent
    s = shell.Shell(token='933c97c35d6c81db2f25feb5ab2b3c7a')
    s.try_command('papersoccer leave')
    r = s.active_agent.say('test %s' % time.strftime('%H:%M:%S', time.gmtime()))
    ps = lib.papersoccer.Instance(s)
    ps_agent = lib.papersoccer.Agent(instance=ps)

def v(r, c): return ps.graph.get_vertex('[%d,%d]' % (r, c))
def move(direction):    ps_agent.cmd_ps_move(direction)
def show_current():     print 'current is', ps.get_current()
def curr_search_node(): return lib.papersoccer.SearchNode(ps, ps.get_current(), 0)
def curr_search_wrap(): return lib.papersoccer.SearchNodeWrap(curr_search_node())

def show_edges_for(r, c):
    g = ps.graph
    vertex = v(r, c)
    print vertex, 'has edges:'
    for item in g.edge_table[vertex].viewitems(): print '  +--', item[0], item[1]


setup()

order = ['e', 'ne', 'se', 'n', 's', 'nw', 'sw', 'w']

def random_nodes():
    while True:
        walk = curr_search_node()
        nexts = walk.get_nexts()

        # game is over
        if ps.get_current().is_terminal or len(nexts) == 0: break
    
        # choose a successor state to move to
        (play_seq, walk) = random.choice(nexts.items())

        ps_agent.cmd_ps_move(play_seq)
    
        curr_search_node().show_nexts()
        raw_input()

def random_wraps():
    while True:
        walk = curr_search_wrap()
        nexts = walk.get_nexts()

        # game is over
        if ps.get_current().is_terminal or len(nexts) == 0: break
    
        # choose a successor state to move to
        (play_seq, walk) = random.choice(nexts.items())

        for play in play_seq: ps_agent.cmd_ps_move(play)
    
        curr_search_node().show_nexts()
        raw_input()


random_wraps()
