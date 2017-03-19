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
difficultyStart = None
util = None

def getGenesis():
	return {
		'log_header': None,
		'nonce': 0,
		'hash': util.emptyTarget,
		'difficulty': difficultyStart,
		'state': {
			'fleet': None,
			'jumps': [],
			'star_systems': []
		},
		'version': 0,
		'time': 0,
		'previous_hash': util.emptyTarget,
		'state_hash': None
	}

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

def createCommand(function, description, details=None):
	return {
		'function': function,
		'description': description,
		'details': details
	}

def commandHelp(commands, params=None):
	helpMessage = 'help\tThis help message'
	exitMessage = 'exit\tEnds this process'
	if params:
		if 0 < len(params):
			queriedCommandName = params[0]
			selection = commands.get(queriedCommandName, None)
			if selection:
				print '%s\t%s' % (queriedCommandName, selection['description'])
				details = selection['details']
				if details:
					for detail in selection['details']:
						print '\t * %s' % detail
				return
			elif queriedCommandName == 'help':
				print helpMessage
				return
			elif queriedCommandName == 'exit':
				print exitMessage
				return
			print 'Command "%s" is not recognized, try typing "help" for a list of all commands'
			return

	print helpMessage
	for curr in commands:
		print '%s\t%s' % (curr, commands[curr]['description'])
	print exitMessage

def info():
	print 'Connected to %s with fudge %s, interval %s, duration %s' % (hostUrl, difficultyFudge, difficultyInterval, difficultyDuration) 

def chain():
	print prettyJson(getRequest(starLogsUrl))

def probe(params=None):
	height = None
	if params:
		if 0 < len(params):
			height = int(params[0])
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
	result = None
	if height == -1:
		result = [getGenesis()]
	else:
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
	difficultyStart = rules['difficulty_start']

	os.environ['DIFFICULTY_FUDGE'] = str(difficultyFudge)
	os.environ['DIFFICULTY_INTERVAL'] = str(difficultyInterval)
	os.environ['DIFFICULTY_DURATION'] = str(difficultyDuration)
	os.environ['DIFFICULTY_START'] = str(difficultyStart)

	import util as util

	print 'Connected to %s with fudge %s, interval %s, duration %s, starting difficulty %s' % (hostUrl, difficultyFudge, difficultyInterval, difficultyDuration, difficultyStart)
	
	allCommands = {
		'info': createCommand(info, 'Displays information about the connected server'),
		'chain': createCommand(chain, 'Retrieves the latest starlog'),
		'probe': createCommand(probe, 'Probes the starlog in the chain', ['Passing no arguments probes for a new starlog ontop of the highest chain member', 'Passing -1 probes for a new genesis starlog', 'Passing a valid starlog height probes for starlogs on top of that memeber of the chain'])
	}

	exited = False
	while not exited:
		command = raw_input('> ')
		try:
			if not command:
				print 'Type help for more commands'
				continue
			args = command.split(' ')
			commandName = args[0]
			commandArgs = args[1:]
			selectedCommand = allCommands.get(commandName, None)
			if not selectedCommand:
				if commandName == 'help':
					commandHelp(allCommands, commandArgs)
				elif commandName == 'exit':
					print 'Exiting...'
					exited = True
				else:
					print 'No command "%s" found, try typing help for more commands' % command
			else:
				if not commandArgs:
					selectedCommand['function']()
				else:
					selectedCommand['function'](commandArgs)
		except:
			traceback.print_exc()
			print 'Error with your last command'	