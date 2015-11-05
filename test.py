#! /usr/bin/env python

import shell
s = shell.Shell(token='9064de0e6893227b021144c7c4f26a00')
r = s.run('papersoccer enter')

import lib.papersoccer
ps = lib.papersoccer.Instance(s, r)
