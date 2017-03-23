import traceback
import os
import json
import sys
from datetime import datetime
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import requests

persistentFileName = 'persistent.json'
hostUrl = os.getenv('HOST_URL', 'http://localhost:5000')
rulesUrl = hostUrl + '/rules'
chainsUrl = hostUrl + '/chains'
starLogsUrl = hostUrl + '/star-logs'

difficultyFudge = None
difficultyInterval = None
difficultyDuration = None
difficultyStart = None
shipReward = None
util = None
persistentData = None

def getGenesis():
	return {
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

def loadPersistent():
	if os.path.isfile(persistentFileName):
		with open(persistentFileName) as persistentFile:
			return json.load(persistentFile)
	return None

def savePersistent(serialized):
	persistentFile = open(persistentFileName, 'w')
	persistentFile.write(prettyJson(serialized))
	persistentFile.close()

def generatePersistent():
	return {
		'current_account': 'default',
		'accounts': { 'default': generateAccount() }
	}

def generateAccount():
	privateKey = rsa.generate_private_key(
		public_exponent=65537,
		key_size=2048,
		backend=default_backend()
	)
	privateSerialized = privateKey.private_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PrivateFormat.PKCS8,
		encryption_algorithm=serialization.BestAvailableEncryption(b'mypassword')
	)
	publicSerialized = privateKey.public_key().public_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PublicFormat.SubjectPublicKeyInfo
	)
	privateLines = privateSerialized.splitlines()
	privateShrunk = ''
	for line in range(1, len(privateLines) - 1):
		privateShrunk += privateLines[line].strip('\n')
	publicLines = publicSerialized.splitlines()
	publicShrunk = ''
	for line in range(1, len(publicLines) - 1):
		publicShrunk += publicLines[line].strip('\n')
	
	return {
		'private_key': privateShrunk,
		'public_key': publicShrunk
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
	helpMessage = '%sThis help message'
	exitMessage = '%sEnds this process'
	if params:
		if 0 < len(params):
			queriedCommandName = params[0]
			selection = commands.get(queriedCommandName, None)
			if selection:
				print '%s' % selection['description']
				details = selection['details']
				if details:
					for detail in selection['details']:
						print '\t - %s' % detail
				return
			elif queriedCommandName == 'help':
				print helpMessage % ''
				return
			elif queriedCommandName == 'exit':
				print exitMessage % ''
				return
			print 'Command "%s" is not recognized, try typing "help" for a list of all commands'
			return

	print helpMessage % 'help\t - '
	for curr in commands:
		print '%s\t - %s' % (curr, commands[curr]['description'])
	print exitMessage % 'exit\t - '

def getAccount(name=None):
	if persistentData:
		accountName = name if name else persistentData['current_account']
		if accountName:
			accounts = persistentData['accounts']
			if accounts:
				currentAccount = accounts.get(accountName, None)
				if currentAccount:
					return (accountName, currentAccount)
	return None

def account(params=None):
	if params:
		paramCount = len(params)
		if paramCount == 1:
			primaryParam = params[0]
			if primaryParam == 'all':
				accountAll()
				return
			if primaryParam == 'clear':
				accountClear()
				return
		elif paramCount == 2:
			primaryParam = params[0]
			secondaryParam = params[1]
			if primaryParam == 'set':
				accountSet(secondaryParam)
				return
		allParams = ''
		for param in params:
			allParams += ' %s' % param
		print 'Unrecognized parameters "%s"' % allParams
	else:
		result = getAccount()
		if result:
			accountName = result[0]
			currentAccount = result[1]
			print 'Using account "%s"' % accountName
			print '\tPrivate Key: %s...' % currentAccount['private_key'][:16]
			print '\tPublic Key:  %s...' % currentAccount['public_key'][:16]
		else:
			print 'No active account'

def accountAll():
	message = 'No account information stored in %s' % persistentFileName
	if persistentData and persistentData['accounts']:
		currentAccount = persistentData['current_account']
		keys = persistentData['accounts'].keys()
		if 0 < len(keys):
			message = 'Persistent data contains the following account entries'
			entryMessage = '\n%s\t- %s\n\t\tPrivate Key: %s...\n\t\tPublic Key:  %s...'
			for key in keys:
				currentEntry = persistentData['accounts'][key]
				activeFlag = '[CURR] ' if currentAccount == key else ''
				message += entryMessage % (activeFlag, key, currentEntry['private_key'][:16], currentEntry['public_key'][:16])
	print message

def accountClear():
	if persistentData:
		persistentData['current_account'] = None
		savePersistent(persistentData)
		print 'Current account is now disabled'
	else:
		print 'No account information stored in %s' % persistentFileName

def accountSet(name):
	if not name:
		print 'Account can not be set to None, try "account clear"'
	if persistentData and persistentData['accounts']:
		if name in persistentData['accounts'].keys():
			persistentData['current_account'] = name
			savePersistent(persistentData)
			print 'Current account is now "%s"' % name
			return
		else:
			print 'Account "%s" cannot be found' % name
			return
	print 'No account information stored in %s' % persistentFileName

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
	starLog = getGenesis()
	if height:
		if height < -1:
			raise ValueError('Paremeter "height" is out of range')
		if height != -1:
			result = getRequest(chainsUrl, {'height': height})
			if result:
				starLog = result[0]
			else:
				raise ValueError('No starlog at specified height could be retrieved')
	if not height:
		result = getRequest(chainsUrl, {'height': height})
		if result:
			starLog = result[0]
	currentAccount = getAccount()
	
	lastFleet = starLog['state']['fleet']

	# util.va
	
	starLog['state'] = {
		'fleet': util.sha256(currentAccount[1]['public_key']) if currentAccount else None,
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
	shipReward = rules['ship_reward']

	os.environ['DIFFICULTY_FUDGE'] = str(difficultyFudge)
	os.environ['DIFFICULTY_INTERVAL'] = str(difficultyInterval)
	os.environ['DIFFICULTY_DURATION'] = str(difficultyDuration)
	os.environ['DIFFICULTY_START'] = str(difficultyStart)
	os.environ['SHIP_REWARD'] = str(shipReward)

	import util as util

	print 'Connected to %s\n\t - Fudge: %s\n\t - Interval: %s\n\t - Duration: %s\n\t - Starting Difficulty: %s\n\t - Ship Reward: %s' % (hostUrl, difficultyFudge, difficultyInterval, difficultyDuration, difficultyStart, shipReward)
	
	allCommands = {
		'info': createCommand(
			info, 
			'Displays information about the connected server'
		),
		'chain': createCommand(
			chain, 
			'Retrieves the latest starlog'
		),
		'probe': createCommand(
			probe, 
			'Probes the starlog in the chain', 
			[
				'Passing no arguments probes for a new starlog ontop of the highest chain member', 
				'Passing "-1" probes for a new genesis starlog', 
				'Passing a valid starlog height probes for starlogs on top of that memeber of the chain'
			]
		),
		'account': createCommand(
			account,
			'Information about the current account',
			[
				'Passing no arguments gets the current account information',
				'Passing "all" lists all accounts stored in persistent data',
				'Passing "set" followed by an account name changes the current account to the specified one',
				'Passing "clear" disables any active accounts'
			]
		)
	}
	
	exited = False
	
	persistentData = loadPersistent()

	if not persistentData:
		print 'A persistent data file must be created in this directory to continue, would you like to do that now?'
		command = raw_input('(y / n) > ')
		if command == 'y' or command == 'yes':
			persistentData = generatePersistent()
			savePersistent(persistentData)
			print 'Generated a new %s file with a new RSA key'
		else:
			exited = True
	
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
	print 'Exiting...'