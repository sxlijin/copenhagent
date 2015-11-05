#! /usr/bin/env python

import sys, time
import bestpaths
try:
    import shell
except ImportError:
    sys.exit('\n%s\n\n\t%s\n' % (
        'ERROR: can only be invoked as script using the -m flag as follows:',
        'user@machine:.../copenhagent$ python -m ai.auton'
        ))

HOSTNAME = 'localhost'

shell = shell.Shell(name='auton', hostname=HOSTNAME)
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
    global r
    while (agent.n_actions < 5000):
        while True:
            b = best_dest(r)
            if b[0] > agent.get_avg_creds(): break
            time.sleep(.1)

        for cmd in best_path_from_to[agent.location][best_dest(r)[-1]][-1]:
            shell.try_command(cmd)
        r = shell.try_command('navigation ai')

# simple_auton()
