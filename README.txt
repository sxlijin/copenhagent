README.txt for copenhagent

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

copenhagent/                Top-level package
    __init__.py             Initialize the copenhagent package
    __main__.py             Mimic behavior of copenhagent.py

    agent.py                Binds to and controls agents in <copenhagent>.
    copenhagent.py          Top-level user interactive interface.
    shell.py                Creates a shell to allow users to control agents.

    README.txt              This file.
    
    ai/                     Subpackage for AI routines.
        __init__.py         
        auton.py            Autonomous routine for an agent in <copenhagent>.
        geography.py        Store state of a <copenhagent> instance and 
                                identify best options for moving around.
        navigation.py       Solves a <navigation> instance.
        papersoccer.py      Solves a <papersoccer> instance.
    
    lib/                    Subpackage for program resources.
        __init__.py 
        benchmark.py        Generate statistics about <copenhagent>.
        logger.py           Log information to STDOUT and parse logs.
        navigation.py       Store state of a <navigation> instance.
        papersoccer.py      Store state of a <papersoccer> instance.
        structs.py          Various data structures used in the program.

 * <USER>
 |
 |   +--[ copenhagent/ ] ----+              +--[ ai/ ]------------------+  
 |   |                       |              |                           |
 +------> * copenhagent.py   |    +------------> * auton.py             |
 |   |    |                  |    |         |                           | 
 |   |    v                  |    |       -----> * geography.py         |
 +------> * shell.py         |    |      /  |                           | 
     |    |                  |    +-----+------> * navigation.py * <--------+
     |    v                  |   /       \  |                           |   |
     |    * agent.py * <--------+         -----> * papersoccer.py * <----------+
     |                       |   \          |                           |   |  |
     +-----------------------+    \         +---------------------------+   |  |
                                   \                                        |  |
                                    \                                       |  |
                                     \      +--[ lib/ ]-----------------+   |  |
                                      \     |                           |   |  |
                                       \    |    * benchmark.py         |   |  |
                                        \   |                           |   |  |
                                         +-----> * navigation.py * <--------+  |
                                         |  |                           |      |
                                         +-----> * papersoccer.py * <----------+
                                            |                           |
                                            |    * logger.py            | 
                                            |                           | 
                                            |    * structs.py           | 
                                            |                           | 
                                            +---------------------------+ 
                                          
                                                                            
################################################################################

To spawn an interactive shell to control an agent from the command line:

    ### create and control a new agent named $arg
    $ python copenhagent.py --new arg

    ### control an existing agent with agentToken $arg
    $ python copenhagent.py --agent arg

To control the agent from within the spawned shell, use API commands, replacing
/'s and ?'s with spaces. (Do not add spaces around ='s, parser will not handle
those safely.) Example presented below:

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

Alternatively:

    $ python2 copenhagent.py --new agentName
    disai> map enter
    disai> map bike locationId=parken
    disai> papersoccer ai
    disai> map bike locationId=noerrebrogade
    disai> navigation ai
    disai> exit
