#! /usr/bin/env python

# returns average nav_solve() runtime from generated logfile

import sys

for fname in sys.argv[1:]:
    f = open(fname, 'rU')
    l = [float(line.strip()[-10:]) for line in f if 'nav_solve() runtime' in line]
    print fname, str(1.0*sum(l)/len(l))
