README for copenhagent.py

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
