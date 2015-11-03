#! /usr/bin/env python

import readline, re

import agent
from logger import *

class CustomProgramError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class Shell:
    """Open a shell to control agents in the copenhagent environment."""

    api_commands = {
        'map': {    'enter': {}, 'leave': {},
                    'metro': { 'direction': ['cw', 'ccw'] },
                    'bike':  { 'locationId': [ 'dis', 'louises', 'langelinie', 
                                               'koedbyen', 'bryggen', 'parken',
                                               'frederiksberg', 'folkentinget', 
                                               'noerrebrogade','christianshavn',
                                               'jaegersborggade' ] }
        }, #--------------------------------------------------------------------
        'navigation': {     'enter': {}, 'leave': {},
                            'lane': { 'direction': ['left', 'stay', 'right'] }
        }, #--------------------------------------------------------------------
        'papersoccer': {    'enter': {}, 'leave': {}, 
                            'play': { 'direction': [  'n', 'ne', 'e', 'se', 
                                                      's', 'sw', 'w', 'nw'  ] }
        }
    }

    ############################################################################
    #
    #  Constructor & mutators.

    def __init__(self, token=None, name=None):
        """
        Initialize the shell using either the token of an existing agent or a 
        name for a new agent which the shell will create.

        If neither or both are provided, sys.exit(1).
        """
        if (token, name).count(None) != 1: 
            sys.exit('Agent to control not specified.')

        self.active_agent = None
        self.set_active_agent(token, name)

        # configure readline
        readline.parse_and_bind('set bell-style none')
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.autocomplete)

    def set_active_agent(self, token=None, name=None):
        """Change the agent which the shell is actively controlling."""
        try:
            if self.active_agent != None: self.active_agent.drop_control()
            self.active_agent = agent.Agent(token, name)
        except (AttributeError, ValueError) as e:
            log_error(e)
            
    ############################################################################
    #
    #  Controllers that handle shell operations.
 
    def run(self, cmd=None):
        """
        Opens the shell for interactive use.

        If $cmd specified, instead runs $cmd and returns the <requests>
        generated by the API request without opening for interactive use.
        """
        if cmd != None: return self.try_command(cmd)
        while True:
            usi = raw_input('disai> ')
            if usi == 'exit':  break
            try:
                self.try_command(usi)
            except (AttributeError, ValueError) as e:
                log_error(e)

    def run_custom_program(self, argstr):
        is_custom = True

        argv = argstr.split()
        if argv[0] == 'copenhagent':
            if len(argv[2:]) != 1: is_custom = False
            else:
                # 'copenhagent new _____'
                if argv[1] == 'new':  self.set_active_agent(name=argv[2])
                # 'copenhagent agent _____'
                elif argv[1] == 'agent':  self.set_active_agent(token=argv[2])
        if argstr == 'navigation ai':  navigation_ai(self)
        elif False: pass
        else: raise CustomProgramError('run_custom_program(): not a custom program')

    def autocomplete(arg, state):
        """
        A completer() function to be used by readline for the purposes of this
        interactive shell.
        """
        argstr = readline.get_line_buffer()[:-len(arg)]
        argv = re.split('[ =]', readline.get_line_buffer())
        n_args = len(argv)
    
        opt_set = api_commands
        for i_arg in range(n_args - 1):
            try:
                opt_set = opt_set[argv[i_arg]]
            except (IndexError, KeyError):
                opt_set = []
    
        fill_char = ' ' if n_args < 3 else ('', '=')[n_args == 3]
        opts = ['%s%s' % (opt, fill_char) 
                for opt in opt_set if opt.startswith(arg)]
    
        try:
            return opts[state]
        except IndexError:
            return None
    
    ############################################################################
    #
    #  Controllers, specifically those which access the API.

    def do_api_command(self, argv):
        """Returns <requests> received from telling $agent to poll the API."""
        if self.active_agent == None:
            raise ValueError('not currently controlling an agent')
        return self.active_agent.poll_api(
            api_url_for('%s/%s?' % tuple(argv[:2]), '&'.join(argv[2:]))
        )
        

    def try_command(self, argstr):
        """
        Return <requests> from executing shell command $argstr.
        If executing a repeated command, returns the last <requests>.
        """
        # assume $argstr is a <str> but allow it to be a <list> as well
        try:
            argv = argstr.split()
        except AttributeError:
            argv = argstr
            argstr = ' '.join(argv)

        try:
            # repeat command $argv[0] times if $argv[0] is a number
            # execute command if it passes verification
            #   verification fills in endpoints and params if none given
            #   also reformats $argv if necessary
            if argv[0].isdigit():
                n = int(argv.pop(0))
                # TODO: adjust so that it doesn't repeat a bad command n times
                #if self.verify_api_command(argv):
                #    for i in range(n): r = self.try_command(argv)
                #    return r
                #else: return None
                for i in range(n): r = self.try_command(argv)
                return r
            try:
                self.run_custom_program(argstr)
            except CustomProgramError:
                if self.verify_api_command(argv):  
                    return self.do_api_command(argv)
        except IndexError:
            return None

    def verify_api_command(self, argv):
        """
        Verify $argv is a sound shell command, i.e. has format

            <command> <endpoint> <query>

        where <query> takes form <param>=<value>.

        If <endpoint> or <query> are omitted, prompt user for
        <endpoint> or <value>s for each <param> as appropriate.
        """
        
        api_commands = self.api_commands

        def log_unk(msg): log_error(('unrecognized', msg))

        # verify <command>
        command = argv[0]

        # FAIL if $command is not valid
        if command not in api_commands:
            log_unk('%s not recognized as <command>' % repr(command))
            return False

        # verify <endpoint>; prompt if none provided
        try:
            endpoint = argv[1]
        except IndexError:
            # accept <query> if specified
            argv.extend(raw_input(
                'enter a %s endpoint (%s): ' % (
                    command, list_reprs(api_commands[command]))
            ).split())
        finally:
            endpoint = argv[1]

        # FAIL if $endpoint is not valid
        if endpoint not in api_commands[command]:
            log_unk('%s not recognized as <endpoint> for %s' % (
                repr(endpoint), repr(command)))
            return False
        
        # verify <query>; prompt if none provided and <query> required
        # NOTE: <param>, '=', and <value> can be separated by spaces now
        queries = argv[2:]
        queries = ' '.join(queries).replace('=', ' = ').split()
        queries = ' '.join(queries).replace(' = ', '=').split()
        try:
            # handle trailing '='s
            if queries[-1] == '=' and len(queries) > 1: 
                queries.pop(-1)
                queries[-1] += '='
        except IndexError: 
            pass

        queries = { param:val 
                    for [param,val] 
                    in [q.split('=') if q.count('=') == 1 else [q,'']
                        for q in queries ]}

        # prompt for <value>s if no <query> provided
        if len(queries) == 0 and len(api_commands[command][endpoint]) != 0:
            for param in api_commands[command][endpoint]:
                queries[param] = raw_input(
                    'enter a %s value (%s): %s=' % (
                        param,
                        list_reprs(api_commands[command][endpoint][param]),
                        param) )

        # FAIL if a <value> is not valid, or wrong <param>s provided
        if queries.viewkeys() == api_commands[command][endpoint].viewkeys():
            for param in queries:
                if queries[param] not in api_commands[command][endpoint][param]:
                    log_unk('%s not recognized as valid <value> for %s' % (
                        repr(queries[param]), repr(param)))
                    return False
        else:
            log_unk('%s not recognized as valid <query> for %s' % ( 
                ', '.join(('%s=%s' % (param, repr(queries[param])) 
                           for param in queries)),
                endpoint))
            return False
        
        # if no failure points reached
        argv[2:] = ['%s=%s' % query for query in queries.viewitems()]
        return True
