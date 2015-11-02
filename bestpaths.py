#! /usr/bin/env python

import sys

def parse_metro(metro): 
    """
    Convert r.json()['state']['map']['metro'] to a more usable format.

    parsed_metro: {   locations:  {directions:    (cost, destination)}}
    """
    parsed = {}
    for loc in metro:
        parsed[loc] = {}
        parsed[loc]['cw'] = (    min(metro[loc]['cw'].viewvalues()), 
                                    min(metro[loc]['cw'].viewkeys())    )
        parsed[loc]['ccw'] = (   min(metro[loc]['ccw'].viewvalues()), 
                                    min(metro[loc]['ccw'].viewkeys())   )
    return parsed

def metro_cost(metro, curr, dest, d):
    """
    Takes a $parsed_metro, $curr <loc>, $dest <loc>, and $d <direction>.
    Determines the cost of taking the <metro> in $d from $curr to $loc.
    Returns a tuple (<cost>, <num actions>, <shell commands>).

    Raises ValueError() if somehow goes around full circle or $cost passes 100.
    """
    walk = curr
    cost = 0
    count = 0
    while walk != dest:
        count += 1
        cost += metro[walk][d][0]
        walk = metro[walk][d][1]
        if walk == curr: raise ValueError('smth went wrong: went full circle')
        if cost > 100:   raise ValueError('smth went wrong: cost of %d' % cost)
    return (cost, count, ['map metro direction=%s' % d for i in range(count)])

def best_method(metro, curr, dest):
    """
    Takes a $parsed_metro, $curr <loc>, $dest <loc>, and returns the best path.
    Returns a tuple (<cost>, <num actions>, <shell commands>).
    """
    return min( metro_cost(metro, curr, dest, 'cw'),
                metro_cost(metro, curr, dest, 'ccw'),
                (15, 1, ['map bike locationId=%s' % dest]) )

def best_paths(r):
    """
    Takes a <requests> containing a FullResponse from copenhagent and returns
    a dict with the best ways to get from place to place.

    Returns bests {} as bests['from']['to'] == (<cost>, <num actions>, <shell commands>)
    """
    metro = parse_metro(r.json()['state']['map']['metro'])
    bests = {}

    for curr in metro.viewkeys():
        bests[curr] = {}
        for dest in metro.viewkeys():
            bests[curr][dest] = best_method(metro, curr, dest)

    return bests
