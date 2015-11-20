#! /usr/bin/env python

import time, sys
import shell
import lib.papersoccer
reload(lib.papersoccer)

s = r = ps = ps_agent = None

dirs = lib.papersoccer.dirs
order = ['e', 'ne', 'se', 'n', 's']#, 'nw', 'sw', 'w']

def setup():
    global s, r, ps, ps_agent
    s = shell.Shell(token='13c7b63dbe96a076988f2f28824ce366')
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

def choose_next(items):
    #return random.choice(items)
    def sum_dirs(items): return (   sum(dirs[x][0] for x in items[0]), 
                                    sum(dirs[x][1] for x in items[0])    )
    items = sorted(items, key=sum_dirs, reverse=True)
    print ' | first 3 options: %s\n' % [item[0] for item in items][:3]
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
        (play_seq, walk) = choose_next(nexts.items())

        raw_input()



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


def alphabeta(node, alpha, beta, is_my_turn):
    if is_terminal(node):   return utility(node, is_my_turn)
    if is_my_turn:
        v = float('-inf')
        for next_node in node.get_nexts():
            v = max(v, alphabeta(   next_node, alpha, beta,
                                    is_my_turn == next_node.check_visited() ))
            alpha = max(alpha, v)
            if beta <= alpha: break
        return v
    else:
        v = float('inf')
        for next_node in node.get_nexts():
            v = min(v, alphabeta(   next_node, alpha, beta,
                                    is_my_turn == next_node.check_visited() ))
            beta = min(beta, v)
            if beta <= alpha: break
        return v


def dlminimax(node, is_my_turn, depth):
    if is_terminal(node) or depth > 1:
        #return utility(node, is_my_turn)
#    if depth > 3: 
#        print 'depth limited at %s' % node
        return (node.get_current().get_column(), node.seq_from_prev)
    if is_my_turn:
        return max( (dlminimax(next_node, False, depth + 1)[0], node.seq_from_prev)
                    for next_node in node.get_nexts()  )
        
    else:
        return min( (dlminimax(next_node, True, depth + 1)[0], node.seq_from_prev)
                    for next_node in node.get_nexts()  )


setup()
#random_wraps()

move_seq = tuple()
while True:
    for move in move_seq:   ps_agent.cmd_ps_move(move)

    walk = curr_search_wrap()
    (heur, move_seq) = dlminimax(walk, True, 0)

    print heur, move_seq

