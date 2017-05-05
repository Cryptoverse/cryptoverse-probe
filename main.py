import sys
import traceback
import os
import json
from datetime import datetime
from ete3 import Tree
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from getch import getch
import matplotlib.pyplot as pyplot
import requests

autoRebuild = int(os.getenv('AUTO_REBUILD', '0')) == 1
commandHistoryLimit = int(os.getenv('COMMAND_HISTORY', '100'))
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

def generateAccount(name='default'):
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
	publicLines = publicSerialized.splitlines()
	publicShrunk = ''
	for line in range(1, len(publicLines) - 1):
		publicShrunk += publicLines[line].strip('\n')
	
	return {
		'name': name,
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
			print 'Command "%s" is not recognized, try typing "help" for a list of all commands' % queriedCommandName
			return

	print helpMessage % 'help\t - '
	for curr in commands:
		print '%s\t - %s' % (curr, commands[curr]['description'])
	print exitMessage % 'exit\t - '

def account(params=None):
	if putil.retrieve(params, '-a', True, False):
		accountAll()
	elif putil.retrieve(params, '-s', True, False):
		accountSet(putil.retrieveValue(params, '-s', None))
	else:
		result = database.getAccount()
		if result:
			print 'Using account "%s"' % result['name']
			print '\tFleet Hash: [%s]' % util.sha256(result['public_key'])[:6]
		else:
			print 'No active account'

def accountAll():
	message = 'No account information found'
	accounts = database.getAccounts()
	if accounts:
		message = 'Persistent data contains the following account entries'
		entryMessage = '\n%s\t- %s\n\t\tFleet Hash: [%s]'
		for currentAccount in accounts:
			activeFlag = '[CURR] ' if currentAccount['active'] else ''
			message += entryMessage % (activeFlag, currentAccount['name'], util.sha256(currentAccount['public_key'])[:6])
	print message

def accountSet(name):
	if not name:
		print 'Account cannot be set to None'
	if not database.anyAccount(name):
		print 'Unable to find account %s' % name
		return
	database.setAccountActive(name)
	print 'Current account is now "%s"' % name

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
	fromGenesis = putil.retrieve(params, '-g', True, False)
	post = putil.retrieve(params, '-a', False, True)
	verbose = putil.retrieve(params, '-v', True, False)
	silent = putil.retrieve(params, '-s', True, False)
	allowDuplicateEvents = putil.retrieve(params, '-d', True, False)
	fromStarLog = putil.retrieveValue(params, '-f', None)
	if fromStarLog is not None:
		fromStarLog = putil.naturalMatch(fromStarLog, database.getStarLogHashes())
	generated = generateNextStarLog(fromStarLog, fromGenesis, allowDuplicateEvents)
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

def generateNextStarLog(fromStarLog=None, fromGenesis=False, allowDuplicateEvents=False):
	nextStarLog = getGenesis()
	if fromStarLog:
		nextStarLog = database.getStarLog(fromStarLog)
	elif not fromGenesis:
		localHighest = database.getStarLogHighest()
		if localHighest is not None:
			nextStarLog = localHighest
	isGenesis = util.isGenesisStarLog(nextStarLog['hash'])
	accountInfo = database.getAccount()
	nextStarLog['events'] = []

	if not isGenesis:
		eventResults = getRequest(eventsUrl, {'limit': eventsMaxLimit})
		if eventResults:
			unusedEvents = []
			for unusedEvent in database.getUnusedEvents(fromStarLog=nextStarLog['hash']):
				unusedEvents.append(unusedEvent['key'])
			usedInputs = []
			usedOutputs = []
			events = []
			for event in eventResults:
				validate.event(event, requireIndex=False, requireStarSystem=True, rewardAllowed=False)
				conflict = False
				currentUsedInputs = []
				for currentInput in event['inputs']:
					conflict = currentInput['key'] in usedInputs + currentUsedInputs or currentInput['key'] not in unusedEvents
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
	nextStarLog['height'] = 0 if isGenesis else nextStarLog['height'] + 1
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

def renderSystems(params=None):
	figure = pyplot.figure()
	axes = figure.add_subplot(111, projection='3d')

	for currentSystem in database.getStarLogHashes(fromHighest=True):
		currentPosition = util.getCartesian(currentSystem)
		xs = [ currentPosition[0], currentPosition[0] ]
		ys = [ currentPosition[1], currentPosition[1] ]
		zs = [ 0, currentPosition[2] ]
		axes.plot(xs, ys, zs)
		axes.scatter(currentPosition[0], currentPosition[1], currentPosition[2], label=currentSystem[:6])
	
	axes.legend()
	axes.set_title('Systems')
	axes.set_xlabel('X')
	axes.set_ylabel('Y')
	axes.set_zlabel('Z')

	pyplot.show()

def listDeployments(params=None):
	verbose = putil.retrieve(params, '-v', True, False)
	listAll = not putil.hasAny(params) or putil.retrieve(params, '-a', True, False)
	fromHash = None
	if putil.retrieve(params, '-f', True, False):
		fromHashQuery = putil.retrieveValue(params, '-f', None)
		if fromHashQuery is None:
			print 'A system hash fragment must be passed with the -f parameter'
			return
		fromHash = putil.naturalMatch(fromHashQuery, database.getStarLogHashes())
		if fromHash is None:
			print 'Unable to find a system hash containing %s' % fromHashQuery
			return
	if listAll:
		listAllDeployments(fromHash, verbose)
		return
	hashQuery = putil.singleStr(params)
	selectedHash = putil.naturalMatch(hashQuery, database.getStarLogHashes())
	if selectedHash is None:
		print 'Unable to find a system hash containing %s' % hashQuery
		return
	deployments = database.getUnusedEvents(fromStarLog=fromHash, systemHash=selectedHash)
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
	result = 'No deployments in system [%s]' % selectedHash[:6]
	if fleets:
		result = 'Deployments in star system [%s]' % selectedHash[:6]
		fleetKeys = fleets.keys()
		for i in range(0, len(fleets)):
			currentFleet = fleetKeys[i]
			result += '\n - [%s] : %s' % (currentFleet[:6], fleets[currentFleet])
		
	print result

def listAllDeployments(fromStarLog, verbose):
	deployments = database.getUnusedEvents(fromStarLog=fromStarLog)
	if verbose:
		print prettyJson(deployments)
		return
	systems = {}
	for deployment in deployments:
		system = deployment['star_system']
		fleet = deployment['fleet_hash']
		count = deployment['count']
		currentSystem = None
		if system in systems:
			currentSystem = systems[system]
		else:
			currentSystem = {}
			systems[system] = currentSystem
		
		if fleet in currentSystem:
			currentSystem[fleet] += count
		else:
			currentSystem[fleet] = count
	result = 'No deployments in any systems'
	accountHash = util.sha256(database.getAccount()['public_key'])
	if systems:
		result = 'Deployments in all systems'
		systemKeys = systems.keys()
		for i in range(0, len(systemKeys)):
			currentSystem = systemKeys[i]
			result += '\n - [%s]' % currentSystem[:6]
			fleetKeys = systems[currentSystem].keys()
			for f in range(0, len(fleetKeys)):
				currentFleet = fleetKeys[f]
				fleetCount = systems[currentSystem][currentFleet]
				activeFlag = '[CURR] ' if currentFleet == accountHash else ''
				result += '\n%s\t - [%s] : %s' % (activeFlag, currentFleet[:6], fleetCount)
		
	print result
	
def jump(params=None):
	originFragment = None
	destinationFragment = None
	verbose = putil.retrieve(params, '-v', True, False)
	render = putil.retrieve(params, '-r', True, False)
	abort = putil.retrieve(params, '-a', True, False)
	count = None
	if putil.hasAny(params):
		if len(params) < 2:
			print 'An origin and destination system must be specified'
			return
		originFragment = params[0]
		destinationFragment = params[1]
		if 2 < len(params) and isinstance(params[2], int):
			count = int(params[2])
	else:
		print 'Specify an origin and destination system'
		return
	hashes = database.getStarLogHashes()
	originHash = putil.naturalMatch(originFragment, hashes)
	if originHash is None:
		print 'Unable to find an origin system containing %s' % originFragment
		return
	destinationHash = putil.naturalMatch(destinationFragment, hashes)
	if destinationHash is None:
		print 'Unable to find a destination system containing %s' % destinationFragment
		return
	if not database.getStarLogsShareChain([originHash, destinationHash]):
		print 'Systems [%s] and [%s] exist on different chains' % (originHash[:6], destinationHash[:6])
		return
	highestHash = database.getStarLogHighest(database.getStarLogHighestFromList([originHash, destinationHash]))['hash']
	accountInfo = database.getAccount()
	fleetHash = util.sha256(accountInfo['public_key'])
	deployments = database.getUnusedEvents(fromStarLog=highestHash, systemHash=originHash, fleetHash=fleetHash)
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

	if verbose:
		print prettyJson(jumpEvent)
	if render:
		renderJump(originHash, destinationHash)
	if not abort:
		result = postRequest(eventsUrl, jumpEvent)
		print 'Posted jump event with response %s' % result

def renderJump(originHash, destinationHash):
	higher = database.getStarLogHighestFromList([originHash, destinationHash])
	
	figure = pyplot.figure()
	axes = figure.add_subplot(111, projection='3d')

	for currentSystem in database.getStarLogHashes(higher):
		currentPosition = util.getCartesian(currentSystem)
		xs = [ currentPosition[0], currentPosition[0] ]
		ys = [ currentPosition[1], currentPosition[1] ]
		zs = [ 0, currentPosition[2] ]
		axes.plot(xs, ys, zs)
		axes.scatter(currentPosition[0], currentPosition[1], currentPosition[2], label=currentSystem[:6])
	originPosition = util.getCartesian(originHash)
	destinationPosition = util.getCartesian(destinationHash)
	xs = [ originPosition[0], destinationPosition[0] ]
	ys = [ originPosition[1], destinationPosition[1] ]
	zs = [ originPosition[2], destinationPosition[2] ]
	axes.plot(xs, ys, zs, linestyle=':')
	
	axes.legend()
	axes.set_title('Jump [%s] -> [%s]' % (originHash[:6], destinationHash[:6]))
	axes.set_xlabel('X')
	axes.set_ylabel('Y')
	axes.set_zlabel('Z')

	pyplot.show()

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
	if originHash is None:
		print 'Unable to find an origin system containing %s' % originFragment
		return
	destinationHash = putil.naturalMatch(destinationFragment, hashes)
	if destinationHash is None:
		print 'Unable to find a destination system containing %s' % destinationFragment
		return
	if not database.getStarLogsShareChain([originHash, destinationHash]):
		print 'Systems [%s] and [%s] exist on different chains' % (originHash[:6], destinationHash[:6])
		return
	print 'Distance between [%s] and [%s] is %s' % (originHash[:6], destinationHash[:6], util.getDistance(originHash, destinationHash))

def systemAverageDistances(params=None):
	originHash = None
	if putil.hasSingle(params):
		originFragment = params[0]
		originHash = putil.naturalMatch(originFragment, database.getStarLogHashes())
		if originHash is None:
			print 'Unable to find an origin system containing %s' % originFragment
			return
	total = 0
	count = 0
	if originHash:
		for currentHash in database.getStarLogHashes(originHash):
			if currentHash == originHash:
				continue
			total += util.getDistance(currentHash, originHash)
			count += 1
	else:
		hashes = database.getStarLogHashes(fromHighest=True)
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
	originHash = None
	if putil.hasSingle(params):
		originFragment = params[0]
		originHash = putil.naturalMatch(originFragment, database.getStarLogHashes())
		if originHash is None:
			print 'Unable to find an origin system containing %s' % originFragment
			return
	if originHash:
		bestSystem = None
		bestDistance = 0 if calculatingMax else 999999999
		for currentHash in database.getStarLogHashes(originHash):
			if currentHash == originHash:
				continue
			dist = util.getDistance(originHash, currentHash)
			if (calculatingMax and bestDistance < dist) or (not calculatingMax and dist < bestDistance):
				bestSystem = currentHash
				bestDistance = dist
		print '%s system from [%s] is [%s], with a distance of %s' % (modifier, originHash[:6], bestSystem[:6], bestDistance)
	else:
		hashes = database.getStarLogHashes(fromHighest=True)
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

def pollInput():
	returnSequence = [ 13 ]
	upSequence = [ 27, 91, 65 ]
	downSequence = [ 27, 91, 66 ]
	leftSequence = [ 27, 91, 68 ]
	rightSequence = [ 27, 91, 67 ]
	backSequence = [ 127 ]
	controlCSequence = [ 3 ]
	tabSequence = [ 9 ]
	doubleEscapeSequence = [ 27, 27 ]

	specialSequences = [
		tabSequence,
		returnSequence,
		upSequence,
		downSequence,
		leftSequence,
		rightSequence,
		backSequence,
		controlCSequence,
		doubleEscapeSequence
	]
	alphaNumericRange = range(32, 127)
	isSpecial = True
	chars = []
	while True:
		isSpecial = chars in specialSequences
		if isSpecial:
			break
		char = ord(getch())
		chars.append(char)
		if len(chars) == 1 and char in alphaNumericRange:
			break
		elif 1 < len(chars):
			lastChars = chars[-2:]
			if lastChars == doubleEscapeSequence:
				chars = lastChars
				isSpecial = True
				break
	
	alphaNumeric = ''
	isReturn = False
	isBackspace = False
	isControlC = False
	isUp = False
	isDown = False
	isLeft = False
	isRight = False
	isTab = False
	isDoubleEscape = False

	if isSpecial:
		if chars == returnSequence:
			isReturn = True
		elif chars == backSequence:
			isBackspace = True
		elif chars == controlCSequence:
			isControlC = True
		elif chars == upSequence:
			isUp = True
		elif chars == downSequence:
			isDown = True
		elif chars == leftSequence:
			isLeft = True
		elif chars == rightSequence:
			isRight = True
		elif chars == tabSequence:
			isTab = True
		elif chars == doubleEscapeSequence:
			isDoubleEscape = True
		else:
			print 'Unrecognized special sequence %s' % chars
	elif len(chars) == 1:
		alphaNumeric = chr(chars[0])
	else:
		print 'Unrecognized alphanumeric sequence %s' % chars
	
	return alphaNumeric, isReturn, isBackspace, isControlC, isUp, isDown, isLeft, isRight, isTab, isDoubleEscape

def main():
	print 'Connected to %s\n\t - Fudge: %s\n\t - Interval: %s\n\t - Duration: %s\n\t - Starting Difficulty: %s\n\t - Ship Reward: %s' % (hostUrl, difficultyFudge, difficultyInterval, difficultyDuration, difficultyStart, shipReward)
	
	if autoRebuild:
		print 'Automatically rebuilding database...'

	database.initialize(autoRebuild)

	sync()

	if not database.getAccounts():
		print 'Unable to find existing accounts, creating default...'
		defaultAccount = generateAccount()
		database.addAccount(defaultAccount)
		database.setAccountActive(defaultAccount['name'])
	elif database.getAccount() is None:
		print 'No active account, try "help account" for more information on selecting an active account'

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
				'"-a" aborts without posting starlog to the server',
				'"-d" allow duplicate events',
				'"-f" probes for a starlog ontop of the best matching system'
			]
		),
		'account': createCommand(
			account,
			'Information about the current account',
			[
				'Passing no arguments gets the current account information',
				'"-a" lists all accounts stored in persistent data',
				'"-s" followed by an account name changes the current account to the specified one'
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
		'rsys': createCommand(
			renderSystems,
			'Render systems in an external plotter'
		),
		'ldeploy': createCommand(
			listDeployments,
			'List deployments in the specified system',
			[
				'Passing a partial hash will list deployments in the best matching system',
				'"-a" lists all systems with deployments',
				'"-f" looks for deployments on the chain with the matching head'
			]
		),
		'jump': createCommand(
			jump,
			'Jump ships from one system to another',
			[
				'Passing partial origin and destination hashes will jump all ships from the origin system',
				'Passing partial origin and destination hashes along with a valid number of ships will jump that many from the origin system',
				'"-v" prints the jump to the console',
				'"-r" renders the jump in an external plotter before executing it',
				'"-a" aborts without posting jump to the server'
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
	
	commandPrefix = '> '
	command = None
	commandIndex = 0
	commandHistory = -1
	commandInSession = 0
	while True:
		
		if command is None:
			command = ''
			sys.stdout.write('\r%s%s\033[K' % (commandPrefix, command))
			sys.stdout.write('\r\033[%sC' % (commandIndex + len(commandPrefix)))

		alphaNumeric, isReturn, isBackspace, isControlC, isUp, isDown, isLeft, isRight, isTab, isDoubleEscape = pollInput()
		oldCommandIndex = commandIndex
		oldCommand = command
		
		if isBackspace:
			if 0 < commandIndex:
				if len(command) == commandIndex:
					# We're at the end of the string
					command = command[:-1]
				else:
					# We're in the middle of a string
					command = command[:commandIndex] + command[commandIndex + 1:]
				commandIndex -= 1
		elif isControlC:
			break
		elif isUp:
			commandHistory = min(commandHistory + 1, database.countCommands() - 1)
			command = database.getCommand(commandHistory)
			commandIndex = 0 if command is None else len(command)
		elif isDown:
			commandHistory = max(commandHistory - 1, -1)
			if commandHistory < 0:
				command = ''
			else:
				command = database.getCommand(commandHistory)
			commandIndex = 0 if command is None else len(command)
		elif isLeft:
			if 0 < commandIndex:
				commandIndex -= 1
		elif isRight:
			if commandIndex < len(command):
				commandIndex += 1
		elif alphaNumeric:
			if len(command) == commandIndex:
				command += alphaNumeric
			else:
				command = command[:commandIndex] + alphaNumeric + command[commandIndex:]
			commandIndex += 1

		if oldCommand != command:
			sys.stdout.write('\r%s%s\033[K' % (commandPrefix, command))
		if oldCommandIndex != commandIndex:
			sys.stdout.write('\r\033[%sC' % (commandIndex + len(commandPrefix)))

		if isReturn or isDoubleEscape:
			sys.stdout.write('\n')
		if isDoubleEscape:
			command = None
			commandIndex = 0
			commandHistory = -1
			continue
		if not isReturn:
			continue

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
					break
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
		database.addCommand(command, util.getTime(), commandInSession)
		command = None
		commandIndex = 0
		commandHistory = -1
		commandInSession += 1

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

	os.environ['COMMAND_HISTORY'] = str(commandHistoryLimit)

	import util
	import validate
	import database
	import parameterUtil as putil
	main()
	sys.stdout.write('\nExiting...\n')