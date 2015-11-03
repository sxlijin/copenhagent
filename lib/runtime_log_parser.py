#! /usr/bin/env python

# returns average nav_solve() runtime from generated logfile

import sys

runtime_sum = {}
runtime_count = {}

for fname in sys.argv[1:]:
    f = open(fname, 'rU')

    for line in f:
        if 'runtime' not in line: continue

        line = line.split(' : ')[1]
        line = line.split()

        (fxn, runtime) = (line[0], float(line[-1]))

        if fxn not in runtime_sum:
            runtime_sum[fxn] = 0.0
            runtime_count[fxn] = 0

        runtime_sum[fxn] += runtime
        runtime_count[fxn] += 1

    for fxn in runtime_sum: 
        print '%10.10s : %15.15s had average runtime %12.8f ms (%4d trials)' % (
            fname, fxn, runtime_sum[fxn]/runtime_count[fxn], runtime_count[fxn])
