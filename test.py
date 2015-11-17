#! /usr/bin/env python

import time, sys
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

def move(direction):    ps_agent.cmd_ps_move(direction)
def show_current(): print 'current is', ps.get_current()
def curr_search_node(): return lib.papersoccer.SearchNode(ps, ps.get_current(), 0)

def v(r, c): return ps.graph.get_vertex('[%d,%d]' % (r, c))

def show_edges_for(r, c):
    g = ps.graph
    vertex = v(r, c)
    print vertex, 'has edges:'
    for item in g.edge_table[vertex].viewitems(): print '  +--', item[0], item[1]

def is_terminal(node):
    return node.get_current().is_terminal or node.get_nexts() == tuple()

def utility(node, is_my_turn):
    multiplier = 1 if ( (node.get_current() == ps.goal_vertex) or
                        (node.get_nexts() == tuple() and not is_my_turn) ) else -1
    return node.moves*multiplier 

def minimax(node, is_my_turn):
    if is_terminal(node):   return utility(node, is_my_turn)
    if is_my_turn:
        return max( minimax(next_node, is_my_turn == next_node.check_visited())
                    for next_node in node.get_nexts())
    else:
        return min( minimax(next_node, is_my_turn == next_node.check_visited())
                    for next_node in node.get_nexts())

setup()
show_current()
curr_search_node().show_nexts()

for next_node in curr_search_node().get_nexts():
    print minimax(next_node, True)

# calling reload(test) runs __init__() again which populates w/ agent & opponent
# to avoid this, write method in test to do stuff that doesn't get called when reload(test)
