README for copenhagent

Fall 2015, DIS Artificial Intelligence, Samuel Lijin and Megan Wancura

This is the README for our work in developing a Python module to control an 
agent in the copenhagent environment. It applies rudimentary AI concepts
such as graph search algorithms (bfs, dfs, best-first, hill-climbing), 
adversarial search algorithms (minimax, alpha-beta), and so on.

################################################################################

$ python copenhagent.py --help
usage: copenhagent.py [-h] [--new <name>] [--agent <agentToken>]
                      [--command <command>]

Spawns an interactive shell with which you can control an agent in the
copenhagent environment. Must specify either --new or --agent when calling the
script; if neither or both are specified, program will immediately exit.

optional arguments:
  -h, --help            show this help message and exit
  --new <name>          create a new agent with <name> and control it
  --agent <agentToken>  control an existing agent with <agentToken>
  --command <command>   send command to shell and close immediately after
                        running

################################################################################

Program architecture is as follows:

lib/
    logger.py   Contains methods used to log messages and info to STDOUT.
    structs.py  Contains custom implementations of various data structures.
    runtime_log_parser.py
                Parses log of runtimes and generates summary.

<USER>      --->    copenhagent.py  --->    shell.py    ---> agent.py


agent.py
command.txt
copenhagent.py
shell.py

ai:
auton.py
bestpaths.py

lib:
logger.py
navigation.py
papersoccer.py
runtime_log_parser.py
structs.py

################################################################################

copenhagent.py is our working file for DIS-AI:


to spawn an interactive shell to control an agent from the command line:

	### create and control a new agent named $arg
	$ python copenhagent.py --new arg

	### control an existing agent with agentToken $arg
	$ python copenhagent.py --agent arg



to control the agent from within the spawned shell, use API commands
(note: do not mess with the spacing scheme, that will break the parser)
example presented below

	disai> map enter
	disai> map metro direction=cw
	disai> map bike locationId=parken
	disai> papersoccer enter
	disai> papersoccer
	enter a papersoccer endpoint (leave, play, enter): play
	enter a value for direction ('n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw'): direction=ne
	disai> papersoccer play direction=e
	disai> papersoccer leave
	disai> map leave
	disai> exit
	
	

THIS IS THE PART THAT MATTERS FOR ADDING WORK
to add commands to the disai> interactive shell
	
	find the method definition for try_command
		
	def try_command(usi):
		"""Polls API according to custom commands, returns received <requests> object."""
		# ad hoc commands
		if usi == 'program': return program()
		if usi == 'papersoccer win': return ps_win()
	
		# break up the command
		usi_split = usi.split()
	
	and if you want to make a command 'some_command' run a method some_method(), 
	add it to the #ad hoc commands section:
		
		# ad hoc commands
		if usi == 'some_command': return some_method()
	
	to execute commands from within the program, call them by try_command()
	if new global state variables are created, only modify them with mutator methods
