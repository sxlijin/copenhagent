#! /usr/bin/env python

import sys
import bestpaths
try:
    import shell
except ImportError:
    sys.exit('\n%s\n\n\t%s\n' % (
        'ERROR: can only be invoked as script using the -m flag as follows:',
        'user@machine:.../copenhagent$ python -m ai.auton'
        ))

shell = shell.Shell(name='auton')
agent = shell.active_agent

r = shell.try_command('map enter')

best_path_from_to = bestpaths.best_paths(r)


def best_dest(r):
    locs = r.json()['state']['map']['locations']
    return max(
            (locs[loc]['activities']['navigation']['config']['seed'], loc) 
            for loc in locs if 'activities' in locs[loc] and
                                'navigation' in locs[loc]['activities'])

def simple_auton():
    while (agent.n_actions < 5000):
        for cmd in best_path_from_to[agent.location][best_dest(r)[-1]][-1]:
            shell.try_command(cmd)
        shell.try_command('navigation ai')
        r = shell.try_command('navigation leave')

def best_dest2(r):
    locs = r.json()['state']['map']['locations']
    navlocs =(locs[loc] for loc in locs if 'navigation' in locs[loc]['activities'])
    print navlocs
    seeds = (navlocs[loc]['navigation']['config']['seed'] for loc in navlocs) 
    print seeds
    factors= sum([locs['navigation']['config']['specials'][thing]['factor'] for thing in navlocs])
    print factors

best_dest2(r)
