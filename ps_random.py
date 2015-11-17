#! /usr/bin/env python

import time, sys, random
import shell
import lib.papersoccer
reload(lib.papersoccer)

s = r = ps = ps_agent = None

def setup():
    global s, r, ps, ps_agent
    s = shell.Shell(token='8eb8153d4399c87e256cd9ac55b7ff24')
    s.try_command('papersoccer leave')
    r = s.active_agent.say('test %s' % time.strftime('%H:%M:%S', time.gmtime()))
    ps = lib.papersoccer.Instance(s)
    ps_agent = lib.papersoccer.Agent(instance=ps)

def v(r, c): return ps.graph.get_vertex('[%d,%d]' % (r, c))
def move(direction):    ps_agent.cmd_ps_move(direction)
def show_current():     print 'current is', ps.get_current()
def curr_search_node(): return lib.papersoccer.SearchNode(ps, ps.get_current(), 0)

def show_edges_for(r, c):
    g = ps.graph
    vertex = v(r, c)
    print vertex, 'has edges:'
    for item in g.edge_table[vertex].viewitems(): print '  +--', item[0], item[1]


setup()

order = ['e', 'ne', 'se', 'n', 's', 'nw', 'sw', 'w']

while True:
    curr = curr_search_node()
    nexts = [node.get_current() for node in curr.get_nexts()]
    # game is over
    if ps.get_current().is_terminal or nexts == []: break

    # choose a successor state to move to
    successor = None
    for direction in order:
        try:    successor = curr.get_next(direction)
        except KeyError:    continue
        if successor.get_current() in nexts: break

    ps_agent.cmd_ps_move(direction)

    curr_search_node().show_nexts()
    raw_input()

