#! /usr/bin/env python

import sys, time, argparse
import ai.geography
try:
    import shell
except ImportError:
    sys.exit('\n%s\n\n\t%s\n' % (
        'ERROR: can only be invoked as script using the -m flag as follows:',
        'user@machine:.../copenhagent$ python -m ai.auton'
        ))


# 1.5, 1.5 also good
MULTIPLIERS = {'navigation':1.56, 'papersoccer':1.45}


def simple_auton(shell, r, m):
    # hops around navigation activities to win
    agent = shell.active_agent
    while (agent.n_actions < 5000):
        # wait for an activity to become desirable
        while True:
            m.update_seeds(r)
            ((dest, activity), seed) = m.get_best_dest()
            if seed * MULTIPLIERS[activity] > agent.get_avg_creds(): break
            time.sleep(.03)
            r = agent.say('waiting')

        for cmd in m.get_path_from_to(agent.location, dest):
            shell.try_command(cmd)
        r = shell.try_command('%s ai' % activity)


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

    s = shell.Shell(name='højskolers', hostname=hostname)
    agent = s.active_agent
    
    r = s.try_command('map enter')
    
    simple_auton(s, r, ai.geography.Map(r))
    
    sys.exit(0)

if __name__ == '__main__':
    main()
