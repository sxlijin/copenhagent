#! /usr/bin/env python

import time, sys, random
import shell
import lib.papersoccer
reload(lib.papersoccer)

s = r = ps = ps_agent = None

def setup():
    global s, r, ps, ps_agent
    s = shell.Shell(token='03c3609504fab47ff35db13e18973971')
    s.try_command('papersoccer leave')
    r = s.active_agent.say('test %s' % time.strftime('%H:%M:%S', time.gmtime()))
    ps = lib.papersoccer.Instance(s)
    ps_agent = lib.papersoccer.Agent(instance=ps)

def v(r, c): return ps.graph.get_vertex('[%d,%d]' % (r, c))
def move(direction):    ps_agent.cmd_ps_move(direction)
def show_current():     print 'current is', ps.get_current()
def curr_search_node(): return lib.papersoccer.SearchNodeAtom(ps.get_current(), ps)
def curr_search_wrap(): return lib.papersoccer.SearchNodeWrap(curr_search_node())

def show_edges_for(r, c):
    g = ps.graph
    vertex = v(r, c)
    print vertex, 'has edges:'
    for item in g.edge_table[vertex].viewitems(): print '  +--', item[0], item[1]


setup()

def choose_next(items):
    # items is a list of successors
    # choose_next() sorts them by preference then chooses first
    #return random.choice(items)
    def sum_dirs(item): return (item.get_current().get_column(), len(item.prev_plays))
    items = sorted(items, key=sum_dirs, reverse=True)
    print ' | options are: '
    for item in items:
        print ' | %s by %s' % (item.get_current(), item.prev_plays)
    return items[0]


def random_wraps():
    play_seq = tuple()
    while True:
        for play in play_seq: ps_agent.cmd_ps_move(play)

        walk = curr_search_wrap()
        walk.show_nexts()
        nexts = walk.get_nexts()

        # game is over
        if ps.get_current().is_terminal or len(nexts) == 0: break
    
        # choose a successor state to move to
        walk = choose_next(nexts)
        play_seq = walk.prev_plays

        print 'want to mv to %s via %s' % (walk.get_current(), play_seq)

        raw_input()

random_wraps()
