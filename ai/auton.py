#! /usr/bin/env python

import sys, time, argparse
import ai.environment
try:
    import shell
except ImportError:
    sys.exit('\n%s\n\n\t%s\n' % (
        'ERROR: can only be invoked as script using the -m flag as follows:',
        'user@machine:.../copenhagent$ python -m ai.auton'
        ))

best_path_from_to = None

def best_dest(r):
    locs = r.json()['state']['map']['locations']
    return max(
            (locs[loc]['activities']['navigation']['config']['seed'], loc) 
            for loc in locs if 'activities' in locs[loc] and
                                'navigation' in locs[loc]['activities'])

MULTIPLIERS = {'navigation':1, 'papersoccer':1}

def simple_auton(shell, r, m):
    # hops around navigation activities to win
    agent = shell.active_agent
    while (agent.n_actions < 5000):
        while True:
            m.update_seeds(r)
            ((dest, activity), seed) = m.get_best_dest()
            if seed * MULTIPLIERS[activity] > agent.get_avg_creds(): break
            time.sleep(.03)
            r = agent.say('waiting')

        for cmd in m.get_path_from_to(agent.location, dest):
            print cmd
            shell.try_command(cmd)
        r = shell.try_command('%s ai' % activity)
        #for cmd in best_path_from_to[agent.location][best_dest(r)[-1]][-1]:
        #    shell.try_command(cmd)
        #r = shell.try_command('navigation ai')

def main():
    parser = argparse.ArgumentParser(
        description = ' '.join((
            'Initializes an autonomous agent in the copenhagent environment.',
            ''
        ))
    )

    parser.add_argument(
        '-hostname',
        metavar='<hostname>',
        required=True,
        help='hostname of the copenhagent server to connect to')
    
    hostname = parser.parse_args().hostname

    s = shell.Shell(name='auton', hostname=hostname)
    agent = s.active_agent
    
    r = s.try_command('map enter')
    
    #global best_path_from_to
    #best_path_from_to = bestpaths.best_paths(r)
    simple_auton(s, r, ai.environment.Map(r))
    
    sys.exit(0)

if __name__ == '__main__':
    main()
