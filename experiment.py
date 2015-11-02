#! /usr/bin/env python

import readline, re

api_commands = {
    'map': {
        'enter': {},
        'metro': {
            'direction': ['cw', 'ccw']
        },
        'bike': {
            'locationId':
            [   'dis', 'koedbyen', 'frederiksberg', 'louises',
                'noerrebrogade', 'jaegersborggade', 'parken', 
                'langelinie', 'christianshavn', 'bryggen', 'folkentinget' ]
        },
        'leave': {}
    },
    'm1': ['a', 'b'],
    'm2': ['c', 'd']
}

def completerA(text, state):
    argstr = readline.get_line_buffer()[:-len(text)]
    argv = re.split('[ =]', readline.get_line_buffer())
    n_args = len(argv)

    #if state == 0: print '\n@ n_args=%d ; argstr=%.20s ; text=%.20s' % (n_args, repr(argstr), repr(text))

    opt_set = api_commands
    for i_arg in range(n_args - 1):
    #    print 'from %.20s' % opt_set,
        try:
            opt_set = opt_set[argv[i_arg]]
        except (IndexError, KeyError):
            opt_set = []
    #    print '\tto %.20s' % opt_set

    fill_char = ' ' if n_args < 3 else ('', '=')[n_args == 3]
    opts = ['%s%s' % (opt, fill_char) for opt in opt_set if opt.startswith(text)]
    #if state == 0: print '@ %.20s -> %.20s' % (repr(text), repr(opts))

    try:
        return opts[state]
    except IndexError:
        return None
#readline.set_completer_delims('')
readline.parse_and_bind('set bell-style none')
readline.parse_and_bind("tab: complete")
readline.set_completer(completerA)

def read():
    i = None
    while i != 'exit': 
        i = raw_input('prompt> ')
    i = None

read()
