#! /usr/bin/env python

import shell
s = shell.Shell(token='9064de0e6893227b021144c7c4f26a00')
r = s.active_agent.say('testing')

import lib.papersoccer
ps = lib.papersoccer.Instance(s, r)
ps.get_initial().get_nexts()

ps_agent = lib.papersoccer.Agent(instance=ps)
