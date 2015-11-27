#! /usr/bin/env python

import time, sys
import shell
import lib.navigation

EXISTING_TOKEN = 'dabea8e1a3c64177e3a89c07f4bfd6bd'

def average(iterable):
    iterable = tuple(iterable)
    return 1.0 * sum(iterable) / len(iterable)

def setup():
    s = shell.Shell(token=EXISTING_TOKEN)
    s.try_command('map enter')
    r = s.active_agent.say('test %s' % time.strftime('%H:%M:%S', time.gmtime()))
    return (s, r)

def nav_branch_factor(shell):
    NAV_LOCS = ['dis', 'noerrebrogade', 'langelinie', 'bryggen']
    NUM_TRIALS = 1000
    LOG_FILENAME = 'nav_average_branching_factor.log'

    result = '%.10f was average branching factor in %d trials at %s.\n' 
    head_pad_len = sum( len(result)
                            - (5 + 2 + 2)
                            + (12 + len(str(NUM_TRIALS)) + len(nav_loc))
                        for nav_loc in NAV_LOCS)

    # open log file for writing
    f = open(LOG_FILENAME, 'w')
    
    tempstr = 'ERROR: average branching factors not calculated due to early exit.'
    f.write(tempstr)
    f.write('_'*(head_pad_len - len(tempstr)))
    f.write('\n')
    f.write('Trial data is included below; format is as follows:\n')
    f.write('avg_b_factor: (vertex, b_factor); (vertex, b_factor); ...)\n')

    f.close()

    overwrite_offset = 0
    for nav_loc in NAV_LOCS:
        # open log file to append
        f = open(LOG_FILENAME, 'a')
        f.write('\nResults for %s below:\n' % nav_loc)
        
        # move agent to $nav_loc
        shell.try_command('map bike locationId=%s' % nav_loc)
        avg_b_factors = []

        for _ in range(NUM_TRIALS):
            # enter navigation and parse FullResponse
            nav_inst = lib.navigation.Instance(shell)
            b_factors = tuple(  (str(v), len(v.get_nexts()))
                                for v in nav_inst.graph.vertex_table.viewvalues()
                                )
            avg_b_factor = average(f[1] for f in b_factors)
            avg_b_factors.append(avg_b_factor)
            f.write('%.6f: ' % avg_b_factor)
            for b_factor in b_factors: f.write(repr(b_factor) + '; ')
            f.write('\n')
            # leave navigation
            shell.try_command('navigation leave')

        f.close()

        # open log file to write at head
        f = open(LOG_FILENAME, 'r+b')
        f.seek(overwrite_offset)
        result_str = result % (average(f[1] for f in b_factors), NUM_TRIALS, nav_loc)
        f.write(result_str)
        overwrite_offset += len(result_str)
        f.close()



s = setup()[0]
nav_branch_factor(s)
s.try_command('map leave')
