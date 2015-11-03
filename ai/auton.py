#! /usr/bin/env python

import sys
import bestpaths
import shell

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

while (agent.n_actions < 5000):
    for cmd in best_path_from_to[agent.location][best_dest(r)[-1]][-1]:
        shell.try_command(cmd)
    shell.try_command('navigation ai')
    r = shell.try_command('navigation leave')
