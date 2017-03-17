import traceback
import os
import json
import time
import copy
import sys
from datetime import datetime
import requests

hostUrl = os.getenv('HOST_URL', 'http://localhost:5000')
rulesUrl = hostUrl + '/rules'
chainsUrl = hostUrl + '/chains'
starLogsUrl = hostUrl + '/star-logs'

difficultyFudge = None
difficultyInterval = None
difficultyDuration = None
util = None

def prettyJson(serialized):
	return json.dumps(serialized, sort_keys=True, indent=4, separators=(',', ': '))

def getRequest(url, payload=None):
	try:
		return requests.get(url, payload).json()
	except:
		traceback.print_exc()
		print 'error on get request '+url

def postRequest(url, payload=None):
	try:
		serialized = json.dumps(payload)
		return requests.post(url, data=serialized, headers={ 'content-type': 'application/json', 'cache-control': 'no-cache', }).json()
	except:
		traceback.print_exc()
		print 'error on post request '+url

def createCommand(function, description):
	return {
		'function': function,
		'description': description
	}

def info():
	print 'Connected to %s with fudge %s, interval %s, duration %s' % (hostUrl, difficultyFudge, difficultyInterval, difficultyDuration) 

def chain():
	print prettyJson(getRequest(starLogsUrl))

def probe(height=None):
	generated = generateNextStarLog(height)
	print 'Probed new starlog'
	print prettyJson(generated)
	try:
		postResult = postRequest(starLogsUrl, generated)
		print 'Posted starlog with response %s' % postResult
	except:
		traceback.print_exc()
		print 'Something went wrong when trying to post the generated starlog'

def generateNextStarLog(height=None):
	result = getRequest(chainsUrl, {'height': height})
	if not result:
		print 'Latest starlog request returned null or empty'
		return
	starLog = result[0]
	starLog['state'] = {
		'fleet': None,
		'jumps': [],
		'star_systems': []
	}
	starLog['previous_hash'] = starLog['hash']
	starLog['time'] = util.getTime()
	starLog['nonce'] = 0
	starLog['log_header'] = util.concatStarLogHeader(starLog)
	found = False
	tries = 0
	started = datetime.now()
	lastCheckin = started

	while not found and tries < sys.maxint:
		starLog['nonce'] += 1
		starLog = util.hashStarLog(starLog)
		found = util.verifyDifficulty(int(starLog['difficulty']), starLog['hash'])
		now = datetime.now()
		if 1 < (now - lastCheckin).total_seconds():
			lastCheckin = now
			elapsedSeconds = (now - started).total_seconds()
			hashesPerSecond = tries / elapsedSeconds
			elapsedMinutes = elapsedSeconds / 60
			print 'Probing at %.0f hashes per second, %.1f minutes elapsed...' % (hashesPerSecond, elapsedMinutes)
		tries += 1
	
	if not found:
		print 'Unable to probe a new starlog'
		return None
	return starLog

if __name__ == '__main__':
	print 'Starting probe...'
	rules = getRequest(rulesUrl)
	if not rules:
		raise ValueError('null rules')
	difficultyFudge = rules['difficulty_fudge']
	difficultyInterval = rules['difficulty_interval']
	difficultyDuration = rules['difficulty_duration']

	os.environ["DIFFICULTY_FUDGE"] = str(difficultyFudge)
	os.environ["DIFFICULTY_INTERVAL"] = str(difficultyInterval)
	os.environ["DIFFICULTY_DURATION"] = str(difficultyDuration)
	
	import util as util

	print 'Connected to %s with fudge %s, interval %s, duration %s' % (hostUrl, difficultyFudge, difficultyInterval, difficultyDuration)
	
	commands = {
		'info': createCommand(info, 'displays information about the connected server'),
		'chain': createCommand(chain, 'retrieves the latest starlog'),
		'probe': createCommand(probe, 'probes the next entry in the chain')
	}

	exited = False
	while not exited:
		command = raw_input('> ')
		if not command:
			print 'Type help for more commands'
			continue
		args = command.split(' ')
		selection = commands.get(args[0], None)
		if not selection:
			if command == 'help':
				print 'help\tthis help message'
				for curr in commands:
					print '%s\t%s' % (curr, commands[curr]['description'])
				print 'exit\tends this process'
			elif command == 'exit':
				print 'Exiting...'
				exited = True
			else:
				print 'No command "%s" found, try typing help for more commands' % command
		else:
			try:
				params = args[1:]
				if not params:
					selection['function']()
				else:
					selection['function'](params)
			except:
				traceback.print_exc()
				print 'Error with your last command'