import traceback
import os
import json
import sys
from ete3 import Tree
from datetime import datetime
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import requests

autoRebuild = int(os.getenv('AUTO_REBUILD', '0')) == 1
persistentFileName = 'persistent.json'
hostUrl = os.getenv('HOST_URL', 'http://localhost:5000')
rulesUrl = hostUrl + '/rules'
chainsUrl = hostUrl + '/chains'
starLogsUrl = hostUrl + '/star-logs'
eventsUrl = hostUrl + '/events'

difficultyFudge = None
difficultyInterval = None
difficultyDuration = None
difficultyStart = None
shipReward = None
starLogsMaxLimit = None
eventsMaxLimit = None
chainsMaxLimit = None
persistentData = None

def getGenesis():
	return {
		'nonce': 0,
		'height': 0,
		'hash': util.emptyTarget,
		'difficulty': difficultyStart,
		'events': [],
		'version': 0,
		'time': 0,
		'previous_hash': util.emptyTarget,
		'events_hash': None
	}

def getEventInput(index, key):
	return {
		'index': index,
		'key': key
	}

def getEventOutput(index, count, fleetHash, key, starSystem, typeName):
	return {
		'index': index,
		'count': count,
		'fleet_hash': fleetHash,
		'key': key,
		'star_system': starSystem,
		'type': typeName
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
		encryption_algorithm=serialization.NoEncryption()
	)
	publicSerialized = privateKey.public_key().public_bytes(
		encoding=serialization.Encoding.PEM,
		format=serialization.PublicFormat.SubjectPublicKeyInfo
	)
	# privateLines = privateSerialized.splitlines()
	# privateShrunk = ''
	# for line in range(0, len(privateLines)):
	# 	privateShrunk += privateLines[line].strip('\n')
	publicLines = publicSerialized.splitlines()
	publicShrunk = ''
	for line in range(1, len(publicLines) - 1):
		publicShrunk += publicLines[line].strip('\n')
	
	return {
		'private_key': privateSerialized,
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

def starLog(params=None):
	targetHash = None
	if putil.hasAny(params):
		if putil.hasSingle(params):
			targetHash = putil.singleStr(params)
	# TODO: Actually support targetHash.
	print prettyJson(getRequest(starLogsUrl))

def probe(params=None):
	# TODO: Sync first...
	height = None
	post = True
	verbose = False
	silent = False
	allowDuplicateEvents = False
	fromStarLog = None
	if params:
		height = putil.retrieve(params, '-g', -1, height)
		post = putil.retrieve(params, '-a', False, post)
		verbose = putil.retrieve(params, '-v', True, verbose)
		silent = putil.retrieve(params, '-s', True, silent)
		allowDuplicateEvents = putil.retrieve(params, '-d', True, allowDuplicateEvents)
		fromStarLog = putil.retrieveValue(params, '-f', fromStarLog)
	if fromStarLog is not None:
		fromStarLog = putil.naturalMatch(fromStarLog, database.getStarLogHashes())
	generated = generateNextStarLog(fromStarLog, height, allowDuplicateEvents)
	if not silent:
		print 'Probed new starlog %s' % generated['hash'][:6]
		if verbose:
			print prettyJson(generated)
	if not post:
		return
	try:
		postResult = postRequest(starLogsUrl, generated)
		if postResult == 200:
			database.addStarLog(generated)
		if not silent:
			print 'Posted starlog with response %s' % postResult
	except:
		traceback.print_exc()
		print 'Something went wrong when trying to post the generated starlog'

def generateNextStarLog(fromStarLog=None, height=None, allowDuplicateEvents=False):
	nextStarLog = getGenesis()
	if fromStarLog:
		nextStarLog = database.getStarLog(fromStarLog)
	elif height:
		if height < -1:
			raise ValueError('Paremeter "height" is out of range')
		if height != -1:
			# TODO: Change this to get from the local database
			result = getRequest(chainsUrl, {'height': height})
			if result:
				nextStarLog = result[0]
			else:
				raise ValueError('No starlog at specified height could be retrieved')
	else:
		# TODO: Change this to get from the local database
		result = getRequest(chainsUrl, {'height': height})
		if result:
			nextStarLog = result[0]
			height = nextStarLog['height']
	isGenesis = util.isGenesisStarLog(nextStarLog['hash'])
	accountInfo = getAccount()[1]
	nextStarLog['events'] = []

	if not isGenesis:
		eventResults = getRequest(eventsUrl, {'limit': eventsMaxLimit})
		if eventResults:
			usedInputs = []
			usedOutputs = []
			events = []
			for event in eventResults:
				validate.event(event, requireIndex=False, requireStarSystem=True, rewardAllowed=False)
				conflict = False
				currentUsedInputs = []
				for currentInput in event['inputs']:
					conflict = currentInput['key'] in usedInputs + currentUsedInputs
					if conflict:
						break
					currentUsedInputs.append(currentInput['key'])
				if conflict:
					continue
				currentUsedOutputs = []
				for currentOutput in event['outputs']:
					outputKey = currentOutput['key']
					conflict = outputKey in usedInputs + usedOutputs + currentUsedInputs + currentUsedOutputs
					if conflict:
						break
					currentUsedOutputs.append(outputKey)
				if conflict:
					continue
				if not allowDuplicateEvents:
					if database.anyEventsUsed(currentUsedInputs, nextStarLog['hash']) or database.anyEventsExist(currentUsedOutputs, nextStarLog['hash']):
						continue
				
				usedInputs += currentUsedInputs
				usedOutputs += currentUsedOutputs
				event['index'] = len(events)
				events.append(event)
			
			nextStarLog['events'] += events

	rewardOutput = {
		'index': 0,
		'type': 'reward',
		'fleet_hash': util.sha256(accountInfo['public_key']),
		'key': util.sha256('%s%s' % (util.getTime(), accountInfo['public_key'])),
		'star_system': None,
		'count': util.shipReward,
	}

	rewardEvent = {
		'index': len(nextStarLog['events']),
		'hash': None,
		'type': 'reward',
		'fleet_hash': util.sha256(accountInfo['public_key']),
		'fleet_key': accountInfo['public_key'],
		'inputs': [],
		'outputs': [
			rewardOutput
		],
		'signature': None
	}

	if not isGenesis:
		# TODO: This won't work correctly if there are multiple genesis blocks!
		# TODO: Change this to get from the local database
		firstStarLog = getRequest(chainsUrl, {'height': 0})
		# Until we have a way to select where to send your reward ships, just send them to the genesis block.
		rewardOutput['star_system'] = firstStarLog[0]['hash']

	rewardEvent['hash'] = util.hashEvent(rewardEvent)
	rewardEvent['signature'] = util.rsaSign(accountInfo['private_key'], rewardEvent['hash'])

	nextStarLog['events'].append(rewardEvent)
	nextStarLog['previous_hash'] = nextStarLog['hash']
	nextStarLog['time'] = util.getTime()
	nextStarLog['nonce'] = 0
	nextStarLog['events_hash'] = util.hashEvents(nextStarLog['events'])
	nextStarLog['log_header'] = util.concatStarLogHeader(nextStarLog)
	nextStarLog['height'] = 0 if height is None else height + 1
	found = False
	tries = 0
	started = datetime.now()
	lastCheckin = started

	while not found and tries < sys.maxint:
		nextStarLog['nonce'] += 1
		nextStarLog = util.hashStarLog(nextStarLog)
		found = False
		try:
			validate.difficulty(int(nextStarLog['difficulty']), nextStarLog['hash'])
			found = True
		except:
			pass
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
	return nextStarLog

def sync(params=None):
	silent = putil.retrieve(params, '-s', True, False)
	latest = database.getStarLogLatest()
	latestTime = 0 if latest is None else latest['time']
	allResults = []
	lastCount = starLogsMaxLimit
	offset = 0
	while starLogsMaxLimit == lastCount:
		results = getRequest(starLogsUrl, { 'since_time': latestTime, 'limit': starLogsMaxLimit, 'offset': offset })
		lastCount = len(results)
		offset += lastCount
		allResults += results

	for result in allResults:
		database.addStarLog(result)

	if not silent:
		print 'Syncronized %s starlogs' % len(allResults)
	
def renderChain(params=None):
	# TODO: Fix bug that causes rendering to mess up after probing.
	limit = 6
	height = None
	# TODO: Actually get height from parameters.
	if putil.hasAny(params):
		if putil.hasSingle(params):
			limit = putil.singleInt(params)
		else:
			print 'unsupported parameters'
			return

	highest = database.getStarLogHighest()
	if highest is None:
		print 'No starlogs to render, try "sync"'
		return
	height = highest['height'] if height is None else height
	results = database.getStarLogsAtHight(height, limit)
	strata = [(height, list(results))]
	remaining = limit - len(results)
	while 0 < height and remaining != 0:
		height -= 1
		ancestorResults = database.getStarLogsAtHight(height, remaining)
		currentResults = []
		for ancestor in ancestorResults:
			hasChildren = False
			for result in results:
				hasChildren = result['previous_hash'] == ancestor['hash']
				if hasChildren:
					break
			results.append(ancestor)
			if not hasChildren:
				currentResults.append(ancestor)
		if currentResults:
			strata.append((height, currentResults))
			remaining = limit - len(currentResults)
	
	tree = Tree()
	lastNode = tree
	count = len(strata)
	for i in reversed(range(0, count)):
		stratum = strata[i]
		if i == 0:
			for orphan in stratum[1]:
				lastNode.add_child(name=orphan['hash'][:6])
		else:
			lastNode = lastNode.add_child()
			for orphan in stratum[1]:
				lastNode.add_sister(name=orphan['hash'][:6])
		
	print tree

def listDeployments(params=None):
	hashQuery = None
	verbose = False
	if putil.hasAny(params):
		hashQuery = putil.singleStr(params)
		verbose = putil.retrieve(params, '-v', True, False)
	else:
		print 'Specify a system hash to list the deployments in that system'
		return
	selectedHash = putil.naturalMatch(hashQuery, database.getStarLogHashes())
	if selectedHash is None:
		print 'Unable to find a system hash containing %s' % hashQuery
		return
	deployments = database.getUnusedEvents(systemHash=selectedHash)
	if verbose:
		print prettyJson(deployments)
		return
	fleets = {}
	for deployment in deployments:
		fleet = deployment['fleet_hash']
		count = deployment['count']
		if fleet in fleets:
			fleets[fleet] += count
		else:
			fleets[fleet] = count
	result = 'No deployments in system %s' % selectedHash
	if fleets:
		result = 'Deployments in star system %s' % selectedHash
		fleetKeys = fleets.keys()
		for i in range(0, len(fleets)):
			currFleet = fleetKeys[i]
			result += '\n - [%s] : %s' % (currFleet[:6], fleets[currFleet])
		
	print result

def jump(params=None):
	originFragment = None
	destinationFragment = None
	count = None
	if putil.hasAny(params):
		if len(params) < 2:
			print 'An origin and destination system must be specified'
			return
		originFragment = params[0]
		destinationFragment = params[1]
		if len(params) == 3:
			count = int(params[2])
	else:
		print 'Specify an origin and destination system'
		return
	hashes = database.getStarLogHashes()
	originHash = putil.naturalMatch(originFragment, hashes)
	destinationHash = putil.naturalMatch(destinationFragment, hashes)
	if originHash is None:
		print 'Unable to find an origin system containing %s' % originFragment
		return
	if destinationHash is None:
		print 'Unable to find a destination system containing %s' % destinationFragment
		return
	accountInfo = getAccount()[1]
	fleetHash = util.sha256(accountInfo['public_key'])
	deployments = database.getUnusedEvents(systemHash=originHash, fleetHash=fleetHash)
	totalShips = 0
	for deployment in deployments:
		totalShips += deployment['count']
	if count is None:
		count = totalShips
	elif totalShips < count:
		print 'Not enough ships to jump from the origin system'
		return
	if count <= 0:
		print 'A number of ships greater than zero must be specified for a jump'
		return

	jumpEvent = {
		'fleet_hash': fleetHash,
		'fleet_key': accountInfo['public_key'],
		'hash': None,
		'inputs': [],
		'outputs': [],
		'signature': None,
		'type': 'jump'
	}

	inputs = []
	inputIndex = 0
	totalInputCount = 0
	for deployment in deployments:
		totalInputCount += deployment['count']
		inputs.append(getEventInput(inputIndex, deployment['key']))
		inputIndex += 1
		if count <= totalInputCount:
			break
	extraShips = totalInputCount - count
	outputs = []
	index = 0
	jumpKey = util.sha256('%s%s%s%s' % (util.getTime(), fleetHash, originHash, destinationHash))
	if 0 < extraShips:
		outputs.append(getEventOutput(index, extraShips, fleetHash, util.sha256('%s%s' % (jumpKey, jumpKey)), originHash, 'jump'))
		index += 1
	outputs.append(getEventOutput(index, count, fleetHash, jumpKey, destinationHash, 'jump'))

	jumpEvent['inputs'] = inputs
	jumpEvent['outputs'] = outputs
	jumpEvent['hash'] = util.hashEvent(jumpEvent)
	jumpEvent['signature'] = util.rsaSign(accountInfo['private_key'], jumpEvent['hash'])

	print prettyJson(jumpEvent)
	result = postRequest(eventsUrl, jumpEvent)
	print 'Posted jump event with response %s' % result

def systemPosition(params=None):
	if not putil.hasSingle(params):
		print 'An origin system must be specified'
		return
	originFragment = putil.singleStr(params)
	originHash = putil.naturalMatch(originFragment, database.getStarLogHashes())
	if originHash is None:
		print 'Unable to find an origin system containing %s' % originFragment
		return
	print '[%s] system is at %s' % (originHash[:6], util.getCartesian(originHash))

def systemDistance(params=None):
	if not putil.hasCount(params, 2):
		print 'An origin and destination system must be specified'
		return
	originFragment = params[0]
	destinationFragment = params[1]
	hashes = database.getStarLogHashes()
	originHash = putil.naturalMatch(originFragment, hashes)
	destinationHash = putil.naturalMatch(destinationFragment, hashes)
	if originHash is None:
		print 'Unable to find an origin system containing %s' % originFragment
		return
	if destinationHash is None:
		print 'Unable to find a destination system containing %s' % destinationFragment
		return
	print 'Distance between [%s] and [%s] is %s' % (originHash[:6], destinationHash[:6], util.getDistance(originHash, destinationHash))

def systemAverageDistances(params=None):
	originHash = None
	hashes = database.getStarLogHashes()
	if putil.hasSingle(params):
		originFragment = params[0]
		originHash = putil.naturalMatch(originFragment, hashes)
		if originHash is None:
			print 'Unable to find an origin system containing %s' % originFragment
			return
	total = 0
	count = 0
	if originHash:
		for currentHash in hashes:
			if currentHash == originHash:
				continue
			total += util.getDistance(currentHash, originHash)
			count += 1
	else:
		for currentHash in hashes:
			hashes = hashes[1:]
			for targetHash in hashes:
				total += util.getDistance(currentHash, targetHash)
				count += 1
	if count == 0:
		print 'No systems to get the average distances of'
	else:
		average = total / count
		if originHash is None:
			print 'Average distance between all systems is %s' % average
		else:
			print 'Average distance to system [%s] is %s' % (originHash[:6], average)

def systemMaximumDistance(params=None):
	systemMinMaxDistance(params)

def systemMinimumDistance(params=None):
	systemMinMaxDistance(params, False)

def systemMinMaxDistance(params=None, calculatingMax=True):
	modifier = 'Farthest' if calculatingMax else 'Nearest'
	hashes = database.getStarLogHashes()
	if hashes is None or len(hashes) == 1:
		print 'Not enough systems to get the max distances of'
		return
	originHash = None
	if putil.hasSingle(params):
		originFragment = params[0]
		originHash = putil.naturalMatch(originFragment, hashes)
		if originHash is None:
			print 'Unable to find an origin system containing %s' % originFragment
			return
	if originHash:
		bestSystem = None
		bestDistance = 0 if calculatingMax else 999999999
		for currentHash in hashes:
			if currentHash == originHash:
				continue
			dist = util.getDistance(originHash, currentHash)
			if (calculatingMax and bestDistance < dist) or (not calculatingMax and dist < bestDistance):
				bestSystem = currentHash
				bestDistance = dist
		print '%s system from [%s] is [%s], with a distance of %s' % (modifier, originHash[:6], bestSystem[:6], bestDistance)
	else:
		bestSystemOrigin = None
		bestSystemDestination = None
		bestDistance = 0 if calculatingMax else 999999999
		for currentHash in hashes:
			hashes = hashes[1:]
			for targetHash in hashes:
				dist = util.getDistance(currentHash, targetHash)
				if (calculatingMax and bestDistance < dist) or (not calculatingMax and dist < bestDistance):
					bestSystemOrigin = currentHash
					bestSystemDestination = targetHash
					bestDistance = dist
		print '%s systems are [%s] and [%s], with a distance of %s' % (modifier, bestSystemOrigin[:6], bestSystemDestination[:6], bestDistance)

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
	starLogsMaxLimit = rules['star_logs_max_limit']
	eventsMaxLimit = rules['events_max_limit']
	chainsMaxLimit = rules['chains_max_limit']

	os.environ['DIFFICULTY_FUDGE'] = str(difficultyFudge)
	os.environ['DIFFICULTY_INTERVAL'] = str(difficultyInterval)
	os.environ['DIFFICULTY_DURATION'] = str(difficultyDuration)
	os.environ['DIFFICULTY_START'] = str(difficultyStart)
	os.environ['SHIP_REWARD'] = str(shipReward)

	import util
	import validate
	import database
	import parameterUtil as putil

	print 'Connected to %s\n\t - Fudge: %s\n\t - Interval: %s\n\t - Duration: %s\n\t - Starting Difficulty: %s\n\t - Ship Reward: %s' % (hostUrl, difficultyFudge, difficultyInterval, difficultyDuration, difficultyStart, shipReward)
	
	if autoRebuild:
		print 'Automatically rebuilding database...'

	database.initialize(autoRebuild)

	sync()

	allCommands = {
		'info': createCommand(
			info, 
			'Displays information about the connected server'
		),
		'slog': createCommand(
			starLog, 
			'Retrieves the latest starlog'
		),
		'probe': createCommand(
			probe, 
			'Probes the starlog in the chain', 
			[
				'Passing no arguments probes for a new starlog ontop of the highest chain member', 
				'"-g" probes for a new genesis starlog', 
				'"-v" prints the probed starlog to the console',
				'"-s" silently executes the command',
				'"-a" aborts without posting starlog to the server'
				'"-d" allow duplicate events'
				'"-f" probes for a starlog ontop of the best matching system'
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
		),
		'rchain': createCommand(
			renderChain,
			'Render starlog chain information to the command line',
			[
				'Passing no arguments renders the highest chains and their siblings',
				'Passing an integer greater than zero renders that many chains'
			]
		),
		'ldeploy': createCommand(
			listDeployments,
			'List deployments in the specified system',
			[
				'Passing a partial hash will list deployments in the best matching system'	
			]
		),
		'jump': createCommand(
			jump,
			'Jump ships from one system to another',
			[
				'Passing partial origin and destination hashes will jump all ships from the origin system',
				'Passing partial origin and destination hashes along with a valid number of ships will jump that many from the origin system'
			]
		),
		'pos': createCommand(
			systemPosition,
			'Calculates the coordinates of the specified system',
			[
				'Passing a partial hash will calculate the coordinate of the best matching system'
			]
		),
		'dist': createCommand(
			systemDistance,
			'Calculates the distance between the specified systems',
			[
				'Passing a partial origin and destination hash will calculate the distance between the best matching systems'
			]
		),
		'avgdist': createCommand(
			systemAverageDistances,
			'Calculates the average distance between all systems',
			[
				'Passing no arguments will calculate the average distance between every system',
				'Passing a partial origin will calculate the average distance to the best matching system'
			]
		),
		'maxdist': createCommand(
			systemMaximumDistance,
			'Calculates the maximum distance between all systems',
			[
				'Passing no arguments will calculate the maximum distance between every system',
				'Passing a partial origin will calculate the maximum distance to the best matching system'
			]
		),
		'mindist': createCommand(
			systemMinimumDistance,
			'Calculates the minimum distance between all systems',
			[
				'Passing no arguments will calculate the minimum distance between every system',
				'Passing a partial origin will calculate the minimum distance to the best matching system'
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