#!/usr/bin/env python

import readline
import sys
import requests
import json
from random import randint

##### GLOBAL VARIABLES <START> #####

QUIET = False
SILENT = False
dump_json_state = True

HOSTNAME='localhost'

# set of all legal commands, endpoints, and parameters
COMMANDS = {
	'map': {
		'enter': {},
		'metro': {'direction':['cw', 'ccw']},
		'bike': {'locationId':
				['bryggen', 'folketinget', 'noerrebrogade', 
				'langelinie', 'dis', 'christianshavn', 
				'jaegersborggade', 'frederiksberg', 'louises', 
				'koedbyen', 'parken']
		},
		'leave': {}
	},
	'navigation': {
		'enter': {},
		'lane': {'direction':['left', 'stay', 'right']},
		'leave': {}
	},
	'papersoccer': {
		'enter': {},
		'play': {'direction':['n', 'ne', 'e', 'se', 's', 'sw', 'w', 'nw']},
		'leave': {}
	}
}

##### GLOBAL VARIABLES <END> #####





##### HELPER FUNCTIONS <START> #####

def dump_json(json_obj):
	"""Prints human-readable JSON from dict or <requests>."""
	# suppress output when SILENT==True
	if SILENT: return
	try:	
		# type-check $json_obj
		if type(json_obj) is dict: 
			# check flags for specified behavior when dumping $json_obj
			if not dump_json_state and 'state' in json_obj.keys():
				json_obj.pop('state')
				print "popping .json()['state']"
			# dump $json_obj
			print json.dumps(json_obj, indent=4)
		# if $json_obj is a <requests> object, cast to json and dump
		elif type(json_obj) is requests.models.Response: dump_json(json_obj.json())
	except (TypeError, ValueError) as e:
		print e
		print json_obj

def api_url(tail):
	"""Returns full concatenated API URL to poll from path and query."""
	# sanitize $tail before returning
	if (tail[0] != '/'): tail = '/' + tail
	return 'http://' + HOSTNAME + ':3000/api' + tail

def get_api(tail, headers={}):
	"""Returns <requests> obtained by polling the API."""
	# construct url
	get_url = api_url(tail)
	# retrieve url
	r = requests.get(get_url, headers=headers)
	# suppress output when SILENT==True
	if SILENT: return r
	print
	print '[polling API <START>]'
	print 'GET:', get_url
	print '  header:', str(headers)
	print 'GET -> JSON:'
	dump_json(r)
	print '[polling API <END>]'
	return r


def list_opts(cmd, endpoint, param):
	"""Returns list of options (opt1, opt2, ...) for $param in /$cmd/$endpoint."""
	return '(' + ', '.join([repr(opt) for opt in COMMANDS[cmd][endpoint][param]]) + ')'

##### HELPER FUNCTIONS <END> #####





##### WORKER FUNCTIONS <START> #####

def init_agent(name):
	"""Creates new agent and returns the corresponding agentToken."""
	return get_api('/environment/connect?name=' + name).json()[u'agentToken']

def open_sess(sess_id = ''):
	"""Takes control of agent and spawns shell to issue commands for the agent."""
	# create header with $agentToken
	h = {u'agentToken':sess_id}
	# verify $agentToken by sending a message
	r = get_api('/environment/agent/say?message=opening python session', headers=h)

	# TODO: implement $SILENT flag
	# if connection successful
	if (200 == r.status_code):
		# acknowledge success and spawn shell
		print 'successfully opened session: ' + sess_id
		usi = ''
		# allow $usi=='exit' to terminate shell
		while(usi != 'exit'):
			usi = raw_input('disai> ') # unsafe input !!!!!!!!
			if (usi == 'exit'): continue
			try_command(usi, h)
		# announce shell is closed
		r = get_api('/environment/agent/say?message=closing python session', headers=h)
	# if connecting with $sess_id fails, ignore and fail
	else:
		print 'failed to connect: status code {}'.format(r.status_code)



def try_command(usi, h):
	"""Polls API according to custom commands, returns received <requests> object."""
	# ad hoc commands
	if usi == 'papersoccer win': return ps_win(h)
	usi_split = usi.split()
	
	# repeat command n times
	if len(usi_split) > 0 and usi_split[0].isdigit():
		# TODO: terminate loop early if any command while looping fails
		for i in range(int(usi_split[0])): 
			try_command(usi[len(usi_split[0])+1:], h)
		return
	
	# attempt command
	#if ((len(usi_split) > 0) and (usi_split[0] in COMMANDS.keys())):
	#	return run_command(usi_split[0], usi_split, h=h)
	if len(usi_split) > 0: return run_command(usi_split, h=h)


	
# takes ['map', 'metro', 'direction=cw'] etc as $args
# refers to 'map metro direction=cw' as:
# 	- command (map)
# 	- endpoint (metro)
# 	- parameter (direction=cw)
def run_command(args, h={}):
	"""Parses command, polls API if sound, returns received <requests>."""
	# verify specified command
	if args[0] in COMMANDS.keys(): 	args = args[1:]
	# FAIL OUT if command verification fails
	else:
		print 'command not recognized: {}'.format(args[0])
		return
	
	# if no endpoint given, prompt user for one
	if len(args) == 0: 
		args = raw_input( 'enter a {} endpoint ({}): '.format(
			cmd, ', '.join(COMMANDS[cmd].keys())) ).split()
	endpoint = args[0]
	
	# begin constructing 
	api_query = '/' + cmd + '/' + endpoint + '?'
	
	# parse params into a dict
	args = { p.split('=')[0]:p.split('=')[1] 
		for p in args[1:] 
		if len(p.split('=')) == 2 }

	# verify specified endpoint
	if endpoint in COMMANDS[cmd].keys():
		# if no parameters passed to endpoint which requires them,
		# prompt user for parameters
		if len(args) == 0 and len(COMMANDS[cmd][endpoint]) != 0 :
			for reqd_param in COMMANDS[cmd][endpoint]:
				args[reqd_param] = raw_input( 
					'enter a value for {0} {1}: {0}='.format(
					param, list_opts(cmd, endpoint, param)))

		# verify specified parameters
		if args.keys() == COMMANDS[cmd][endpoint].keys() :
			for param in args:
				# if illegal value passed as parameter, fail out
				if args[param] not in COMMANDS[cmd][endpoint][param]:
					print 'ERROR:', repr(args[param]),
					print 'not recognized as legal value for', repr(param),
					print list_opts(cmd, endpoint, param)
					get_flag &= False
		# FAIL OUT if parameter verification fails
		else:
			print 'endpoint', endpoint_url, 'requires params with legal values: '
			for k in COMMANDS[cmd][endpoint]:
				print '\t', k, list_opts(cmd, endpoint, k)
			print 'but received args:'
			for k in args: print '\t', k + '=' + args[k]
			return
	# FAIL OUT if endpoint verification fails
	else:
		print '{} endpoint not recognized: {}'.format(cmd, endpoint)
		return

	# if no problems encountered while parsing
	# construct api query and return requests object
	api_query += '&'.join(
		['{}={}'.format(p, args[p]) for p in COMMANDS[cmd][endpoint]])
	r = get_api(api_path, headers=h)
	return r

##### WORKER FUNCTIONS <END> #####





##### ACTION FUNCTIONS <START> #####
win_from = {
	'n': [	'papersoccer play direction=ne',
		'papersoccer play direction=s',
		'papersoccer play direction=ne',
		'papersoccer play direction=se',
		'papersoccer play direction=se' ] ,
	's': [	'papersoccer play direction=se',
		'papersoccer play direction=n',
		'papersoccer play direction=se',
		'papersoccer play direction=ne',
		'papersoccer play direction=ne' ]
}

def ps_force_win_from(side, h):
	for act in win_from[side]: r = try_command(act, h)
	# uncomment to pause before leaving the game
	# raw_input('press enter to leave papersoccer game ')
	try_command('papersoccer leave', h)
	return r
	
def ps_play_dir(direction, h):
	return try_command('papersoccer play direction=' + direction, h)

def ps_win(h):
	dirs = ['ne','se']
	rand2 = randint(0,1)

	r = try_command('papersoccer enter', h)
	r = ps_play_dir(dirs[rand2], h)
	# try a random direction
	if len(r.json()['action']['percepts']) == 2:
		rand2 -= 1
		for i in range(2): r = ps_play_dir(dirs[rand2], h)
		if len(r.json()['action']['percepts']) == 2:
			rand2 -= 1
			r = ps_play_dir(dirs[rand2], h)
			r = ps_play_dir('e', h)
			r = ps_force_win_from(
				r.json()['action']['percepts'][0][0], h)
	if r.json()['action']['percepts'] == ['w']:
		r = ps_force_win_from(dirs[rand2][0], h)
	if not SILENT: print '\n', r.json()['action']['message']

##### ACTION FUNCTIONS <END> #####





#### COMMAND LINE INTERPRETERS <START> #####

def main():
	if len(sys.argv) == 3:
		if sys.argv[1] == '--new': open_sess(init_agent(sys.argv[2]))
		if sys.argv[1] == '--sess_id': open_sess(sys.argv[2])

if __name__ == "__main__":
	main()

##### COMMAND LINE INTERPRETERS <END> #####
