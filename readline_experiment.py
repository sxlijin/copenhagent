#! /usr/bin/env python

import readline

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
    'navigation': {
        'enter': {},
        'lane': {
            'direction':['left', 'stay', 'right']
        },
        'leave': {}
    },
    'papersoccer': {
        'enter': {},
        'play': {
            'direction': ['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']
        },
        'leave': {}
    }
}

def completerA(text, state):
    # https://pymotw.com/2/readline/
    # http://stackoverflow.com/questions/187621/how-to-make-a-python-command-line-program-autocomplete-arbitrary-things-not-int
    # http://stackoverflow.com/questions/20691102/readline-autocomplete-and-whitespace
    # 
    #print readline.get_line_buffer()
    t = text.split()
    options = []
    if len(t) == 0:
        return None
    if len(t) == 1:
        print t
        return api_commands[t[0]].keys()[state]
    #options = [i for i in commands if i.startswith(text)]
    return None
    if state < len(options):
        return options[state]
    else:
        return None

#readline.set_completer_delims('')
readline.parse_and_bind('set bell-style none')
readline.parse_and_bind("tab: complete")
readline.set_completer(completerA)

def read():
    i = None
    while i != 'exit': 
        i = raw_input('prompt> ')
        print repr(i)
    i = None

if __name__ == '__main__': read()
