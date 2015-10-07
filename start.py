#!/usr/bin/env python

import readline
import sys
import requests
import json

##### GLOBAL VARIABLES <START> #####

hostname='localhost'

commands = {
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
	try:	
		if type(json_obj) is dict: print json.dumps(json_obj, indent=4)
		elif type(json_obj) is requests.models.Response: dump_json(json_obj.json())
	except TypeError as e:
		print e
		print json_obj

def api_url(tail):
	if (tail[0] != '/'): tail = '/' + tail
	return 'http://' + hostname + ':3000/api' + tail

def get_api(tail, headers={}):
	print
	print '[poll API <START>]'
	print 'GET:', api_url(tail)
	print '  header:', str(headers)
	print 'GET -> JSON:'
	r = requests.get(api_url(tail), headers=headers)
	dump_json(r)
	print '[poll API <END>]'
	return r


def list_opts(section, endpoint, param):
    return '(' + ', '.join([repr(opt) for opt in commands[section][endpoint][param]]) + ')'

##### HELPER FUNCTIONS <END> #####





##### WORKER FUNCTIONS <START> #####

def init_agent(name):
	return get_api('/environment/connect?name=' + name).json()[u'agentToken']

def open_sess(sess_id = ''):
	h = {u'agentToken':sess_id}
	r = get_api('/environment/agent/say?message=opening python session', headers=h)

	if (200 == r.status_code):
	# if connection successful
		print 'successfully opened session: ' + sess_id
		usi = ''
		#usi = 'exit' #DEBUG
		# create cli
		while(usi != 'exit'):
			usi = raw_input('disai> ') # unsafe input !!!!!!!!
			try_command(usi, h)
			#if usi == '': continue #handle empty case
			#usi_split = usi.split()
			#if (usi_split[0] in commands.keys()):
			#	 do_section(usi_split[0], usi_split, h=h)
			#else: 
			#	if (usi != 'exit'):
			#		 print 'command unrecognized, please try again'
	else:
	# if connecting with $sess_id fails, ignore and fail
		print 'failed to connect, status code ' + str(r.status_code)

def try_command(usi, h):
	if usi == 'papersoccer win': return papersoccer_win(h)
	usi_split = usi.split()
	if ((len(usi_split) > 0) and (usi_split[0] in commands.keys())):
		return do_section(usi_split[0], usi_split, h=h)
	else: 
		if (usi != 'exit'):
			 print 'command unrecognized, please try again'
	

def do_section(section, params, h={}):
    #bool determines whether or not generated url is sound
    get_flag = True
    if (params[0] == section): params = params[1:]
    if (len(params) == 0):
        params = raw_input(
            'enter a ' + section + ' command (' + ', '.join(commands[section].keys()) + '): '
            ).split()
    endpoint = params[0]
    endpoint_url = '/' + section + '/' + endpoint + '?'
    params = {p.split('=')[0]:p.split('=')[1] for p in params[1:] if (len(p.split('=')) == 2)}
    #print params #DEBUG
    if endpoint in commands[section].keys():
        if ( (len(params) == 0) and (len(commands[section][endpoint]) != 0)):
        # if no parameters passed to endpoint which requires them
            for reqd_param in commands[section][endpoint]:
                params[reqd_param] = raw_input(
                    'enter a value for ' + reqd_param +
                    ' ' + list_opts(section, endpoint, reqd_param) + ': ')
        if ( (len(params) == len(commands[section][endpoint])) and
             params.keys() == commands[section][endpoint].keys() ):
            endpoint_url += '&'.join([p + '=' + params[p] for p in commands[section][endpoint]])
            for param in params:
                # if illegal value passed as parameter, fail out
                if params[param] not in commands[section][endpoint][param]:
                    print 'ERROR:', repr(params[param]),
                    print 'not recognized as legal value for', repr(param),
                    print list_opts(section, endpoint, param)
                    get_flag &= False
        else:
            print 'endpoint', endpoint_url, 'requires params: '
            for k in commands[section][endpoint]:
                print '\t', k,
                print list_opts(section, endpoint, k)
            print 'but received params:'
            for k in params: print '\t', k + '=' + params[k]
    else:
        print section, 'command not recognized:', endpoint
	get_flag &= False

    if get_flag:
        r = get_api(endpoint_url, headers=h)
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

def papersoccer_win_from(side, h):
	for act in win_from[side]: try_command(act, h)
	return try_command('papersoccer leave', h)
	
def papersoccer_win(h):
	r = try_command('papersoccer enter', h)
	r = try_command('papersoccer play direction=ne', h)
	# start by trying the s side
	if r.json()['action']['percepts'] == ['nw','sw']:
	# if computer responds with >nw >sw
		r = try_command('papersoccer play direction=se', h)
		#go back to the center
		r = try_command('papersoccer play direction=se', h)
		#try the other side, the n side

		if r.json()['action']['percepts'] == ['sw','nw']:
		# if computer responds with >sw >nw
			r = try_command('papersoccer play direction=ne', h)
			#go back to the center
			r = try_command('papersoccer play direction=e', h)
			#go east
			
			if r.json()['action']['percepts'] == ['nw']:
			# if computer responds with >nw
				return papersoccer_win_from('n', h)
			elif r.json()['action']['percepts'] == ['sw']:
			# if computer responds with >sw
				return papersoccer_win_from('s', h)
		elif r.json()['action']['percepts'] == ['w']:
			return papersoccer_win_from('s',h)
	elif r.json()['action']['percepts'] == ['w']:
	# if computer responds with >w
		return papersoccer_win_from('n', h)

	#return try_command('papersoccer leave', h)
#
#	if r.json()['action']['message'] == 'Opponent made 2 plays':
#	# if computer responds with > sw > nw
#		r = try_command('papersoccer play direction=ne', h)
#		r = try_command('papersoccer play direction=ne', h)
#		
#		if r.json()['action']['message'] == 'Opponent made 2 plays':
#			r = try_command('papersoccer play direction=se', h)
#			r = try_command('papersoccer play direction=e', h)
#	elif r.json()['action']['message'] == 'Opponent made 1 plays':
#	# if computer responds with > w
#
#	return try_command('papersoccer leave', h)

##### ACTION FUNCTIONS <END> #####





#### COMMAND LINE INTERPRETERS <START> #####

def main():
	if len(sys.argv) == 3:
		if sys.argv[1] == '--new': open_sess(init_agent(sys.argv[2]))
		if sys.argv[1] == '--sess_id': open_sess(sys.argv[2])

if __name__ == "__main__":
	main()

##### COMMAND LINE INTERPRETERS <END> #####
