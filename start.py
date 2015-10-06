#!/usr/bin/env python

import sys
import requests
import json

#def printjson(j, indent=4):
#	if (str(type(j)) == "<type 'dict'>"):
#		for key in j:
#			print u' '*indent + u'\'' + key + u'\':'
#			printjson(j[key], indent+4)
#	else: print u' '*indent + unicode(j)

def url(hostname='localhost'):
	return 'http://' + hostname + ':3000/api'

def init_agent(name):
	return requests.get(url() + '/environment/connect?name=' + name).json()[u'agentToken']

def open_sess(sess_id = ''):
	h = {u'agentToken':sess_id}
	# if connecting with $sess_id fails, ignore and fail
	r = requests.get(
            url() + '/environment/agent/say?message=Opening python session',
            headers = h)
	print json.dumps(r.json(), indent=4)

	if (200 == r.status_code):
		print 'successfully opened session: ' + sess_id
		usi = ''
		#usi = 'exit'
		while(usi != 'exit'):
			usi = raw_input('disai> ')
	else:
		print 'failed to connect, http response code: ' + str(r.status_code)

def main():
	if len(sys.argv) > 1:
		sess_id = init_agent(sys.argv[1])
		open_sess(sess_id)

if __name__ == "__main__":
	main()

