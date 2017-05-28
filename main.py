from json import dumps as jsonDump
from os import getenv, environ
from sys import stdout, platform
from traceback import print_exc as printException
from datetime import datetime
from time import sleep
from ete3 import Tree
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from getch import getch
from probeExceptions import CommandException, ProbeTimeoutException
import requests
import database
import util
import validate
import parameterUtil as putil

import matplotlib
matplotlib.use('TkAgg')

from mpl_toolkits.mplot3d import Axes3D # pylint: disable=unused-import
import matplotlib.colors as pycolors
import matplotlib.pyplot as pyplot

autoRebuild = int(getenv('AUTO_REBUILD', '0')) == 1

# hostUrl = getenv('HOST_URL', 'http://localhost:5000')
hostUrl = getenv('HOST_URL', 'http://api.cryptoverse.io')
rulesUrl = hostUrl + '/rules'
chainsUrl = hostUrl + '/chains'
starLogsUrl = hostUrl + '/star-logs'
eventsUrl = hostUrl + '/events'

defaultColor = '\033[0m'
successColor = '\033[92m'
errorColor = '\033[91m'
boldColor = '\033[1m'
cursorEraseSequence = '\033[K'
cursorForwardSequence = '\033[%sC'

def getGenesis():
	return {
		'nonce': 0,
		'height': 0,
		'hash': util.EMPTY_TARGET,
		'difficulty': util.difficultyStart(),
		'events': [],
		'version': 0,
		'time': 0,
		'previous_hash': util.EMPTY_TARGET,
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
	return jsonDump(serialized, sort_keys=True, indent=4, separators=(',', ': '))

def getRequest(url, payload=None):
	try:
		return requests.get(url, payload).json()
	except:
		printException()
		print 'error on get request '+url

def postRequest(url, payload=None):
	try:
		serialized = jsonDump(payload)
		return requests.post(url, data=serialized, headers={ 'content-type': 'application/json', 'cache-control': 'no-cache', }).json()
	except:
		printException()
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
			raise CommandException('Command "%s" is not recognized, try typing "help" for a list of all commands' % queriedCommandName)

	print helpMessage % 'help\t - '
	for curr in commands:
		print '%s\t - %s' % (curr, commands[curr]['description'])
	print exitMessage % 'exit\t - '

def account(params=None):
	if putil.retrieve(params, '-a', True, False):
		accountAll()
	elif putil.retrieve(params, '-s', True, False):
		accountSet(putil.retrieveValue(params, '-s', None))
	elif putil.retrieve(params, '-c', True, False):
		accountCreate(putil.retrieveValue(params, '-c', None))
	else:
		result = database.getAccount()
		if result:
			print 'Using account "%s"' % result['name']
			print '\tFleet Hash: %s' % util.get_fleet_hash_name(result['public_key'])
		else:
			print 'No active account'

def accountAll():
	message = 'No account information found'
	accounts = database.getAccounts()
	if accounts:
		message = 'Persistent data contains the following account entries'
		entryMessage = '\n%s\t- %s\n\t\tFleet Hash: %s'
		for currentAccount in accounts:
			activeFlag = '[CURR] ' if currentAccount['active'] else ''
			message += entryMessage % (activeFlag, currentAccount['name'], util.get_fleet_hash_name(currentAccount['public_key']))
	print message

def accountSet(name):
	if not name:
		raise CommandException('Account cannot be set to None')
	if not database.anyAccount(name):
		raise CommandException('Unable to find account %s' % name)
	database.setAccountActive(name)
	print 'Current account is now "%s"' % name

def accountCreate(name):
	if not name:
		raise CommandException('Include a unique name for this account')
	elif database.anyAccount(name):
		raise CommandException('An account named "%s" already exists' % name)
	createdAccount = generateAccount(name)
	database.addAccount(createdAccount)
	database.setAccountActive(name)
	print 'Created and activated account "%s"' % name

def info():
	print 'Connected to %s with fudge %s, interval %s, duration %s' % (hostUrl, util.difficultyFudge(), util.difficultyInterval(), util.difficultyDuration()) 

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
	fromQuery = putil.retrieveValue(params, '-f', None)
	loop = putil.retrieve(params, '-l', True, False)
	wait = float(putil.retrieveValue(params, '-w', 0.0))
	blind = putil.retrieve(params, '-b', True, False)
	if wait < 0:
		raise CommandException('Cannot use a wait less than zero seconds')
	fromHash = None
	if fromQuery is not None:
		fromHash = putil.naturalMatch(fromQuery, database.getStarLogHashes())
		if fromHash is None:
			raise CommandException('Unable to find a system hash containing %s' % fromQuery)
	if not blind:
		sync('-s')
	generated = None
	started = datetime.now()
	while generated is None:
		try:
			generated = generateNextStarLog(fromHash, fromGenesis, allowDuplicateEvents, started)
		except ProbeTimeoutException:
			if not blind:
				sync('-s')
	if not silent:
		print 'Probed new starlog %s' % util.get_system_name(generated['hash'])
		if verbose:
			print prettyJson(generated)
	if not post:
		return
	try:
		result = postRequest(starLogsUrl, generated)
		if result == 200:
			database.addStarLog(generated)
		if not silent:
			prefix, postfix = successColor if result == 200 else errorColor, defaultColor
			print 'Posted starlog with response %s%s%s' % (prefix, result, postfix)
	except:
		printException()
		print 'Something went wrong when trying to post the generated starlog'
	if loop:
		if 0 < wait:
			sleep(wait)
		probe(params)

def generateNextStarLog(fromStarLog=None, fromGenesis=False, allowDuplicateEvents=False, startTime=None, timeout=180):
	nextStarLog = getGenesis()
	if fromStarLog:
		nextStarLog = database.getStarLog(fromStarLog)
	elif not fromGenesis:
		localHighest = database.getStarLogHighest()
		if localHighest is not None:
			nextStarLog = localHighest
	isGenesis = util.is_genesis_star_log(nextStarLog['hash'])
	accountInfo = database.getAccount()
	nextStarLog['events'] = []

	if not isGenesis:
		eventResults = getRequest(eventsUrl, {'limit': util.maximumEventSize()})
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
		'key': util.sha256('%s%s' % (util.get_time(), accountInfo['public_key'])),
		'star_system': None,
		'count': util.shipReward(),
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

	rewardEvent['hash'] = util.hash_event(rewardEvent)
	rewardEvent['signature'] = util.rsa_sign(accountInfo['private_key'], rewardEvent['hash'])

	nextStarLog['events'].append(rewardEvent)
	nextStarLog['previous_hash'] = nextStarLog['hash']
	nextStarLog['time'] = util.get_time()
	nextStarLog['nonce'] = 0
	nextStarLog['events_hash'] = util.hash_events(nextStarLog['events'])
	nextStarLog['log_header'] = util.concat_star_log_header(nextStarLog)
	nextStarLog['height'] = 0 if isGenesis else nextStarLog['height'] + 1

	if not isGenesis and util.is_difficulty_changing(nextStarLog['height']):
		# We have to recalculate the difficulty at this height.
		previousRecalculation = database.getStarLogAtHight(nextStarLog['previous_hash'], nextStarLog['height'] - util.difficultyInterval())
		previousStarLog = database.getStarLog(nextStarLog['previous_hash'])
		nextStarLog['difficulty'] = util.calculate_difficulty(previousRecalculation['difficulty'], previousStarLog['time'] - previousRecalculation['time'])

	found = False
	tries = 0
	checkInterval = 10000000
	nextCheck = checkInterval
	currStarted = datetime.now()
	started = currStarted if startTime is None else startTime
	lastCheckin = currStarted
	# This initial hash hangles the hashing of events and such.
	nextStarLog = util.hash_star_log(nextStarLog)
	currentDifficulty = util.unpack_bits(nextStarLog['difficulty'], True)
	currentDifficultyLeadingZeros = len(currentDifficulty) - len(currentDifficulty.lstrip('0'))
	currentNonce = 0
	logPrefix = util.concat_star_log_header(nextStarLog, False)
	currentHash = None

	while not found:
		currentHash = util.sha256('%s%s' % (logPrefix, currentNonce))
		try:
			validate.difficultyUnpacked(currentDifficulty, currentDifficultyLeadingZeros, currentHash, False)
			found = True
			break
		except:
			pass
		if tries == nextCheck:
			nextCheck = tries + checkInterval
			now = datetime.now()
			if timeout < (now - currStarted).total_seconds():
				raise ProbeTimeoutException('Probing timed out')
			hashesPerSecond = tries / (now - lastCheckin).total_seconds()
			elapsedMinutes = (now - started).total_seconds() / 60
			print '\tProbing at %.0f hashes per second, %.1f minutes elapsed...' % (hashesPerSecond, elapsedMinutes)
		currentNonce += 1
		if util.MAXIMUM_NONCE <= currentNonce:
			currentNonce = 0
			nextStarLog['time'] = util.get_time()
			logPrefix = util.concat_star_log_header(nextStarLog, False)
		tries += 1
	if found:
		nextStarLog['nonce'] = currentNonce
		nextStarLog['log_header'] = util.concat_star_log_header(nextStarLog)
		nextStarLog['hash'] = currentHash
	else:
		raise CommandException('Unable to probe a new starlog')
	return nextStarLog

def sync(params=None):
	silent = putil.retrieve(params, '-s', True, False)
	if putil.retrieve(params, '-f', True, False):
		if not silent:
			print 'Removing all locally cached starlogs'
		database.initialize(True)

	latest = database.getStarLogLatest()
	latestTime = 0 if latest is None else latest['time']
	allResults = []
	lastCount = util.starLogsMaxLimit()
	offset = 0
	while util.starLogsMaxLimit() == lastCount:
		results = getRequest(starLogsUrl, { 'since_time': latestTime, 'limit': util.starLogsMaxLimit(), 'offset': offset })
		if results is None:
			lastCount = 0
		else:
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
			raise CommandException('Unsupported parameters')

	highest = database.getStarLogHighest()
	if highest is None:
		raise CommandException('No starlogs to render, try "sync"')
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
				lastNode.add_child(name=util.get_system_name(orphan['hash']))
		else:
			lastNode = lastNode.add_child()
			for orphan in stratum[1]:
				lastNode.add_sister(name=util.get_system_name(orphan['hash']))
		
	print tree

def renderSystems(params=None):
	figure = pyplot.figure()
	axes = figure.add_subplot(111, projection='3d')

	for currentSystem in database.getStarLogHashes(fromHighest=True):
		currentPosition = util.get_cartesian(currentSystem)
		xs = [ currentPosition[0], currentPosition[0] ]
		ys = [ currentPosition[1], currentPosition[1] ]
		zs = [ 0, currentPosition[2] ]
		axes.plot(xs, ys, zs)
		axes.scatter(currentPosition[0], currentPosition[1], currentPosition[2], label=util.get_system_name(currentSystem))
	
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
			raise CommandException('A system hash fragment must be passed with the -f parameter')
		fromHash = putil.naturalMatch(fromHashQuery, database.getStarLogHashes())
		if fromHash is None:
			raise CommandException('Unable to find a system hash containing %s' % fromHashQuery)
	if listAll:
		listAllDeployments(fromHash, verbose)
		return
	hashQuery = putil.singleStr(params)
	selectedHash = putil.naturalMatch(hashQuery, database.getStarLogHashes())
	if selectedHash is None:
		raise CommandException('Unable to find a system hash containing %s' % hashQuery)
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
	result = 'No deployments in system %s' % util.get_system_name(selectedHash)
	if fleets:
		result = 'Deployments in star system %s' % util.get_system_name(selectedHash)
		fleetKeys = fleets.keys()
		for i in range(0, len(fleets)):
			currentFleet = fleetKeys[i]
			result += '\n - %s : %s' % (util.get_fleet_name(currentFleet), fleets[currentFleet])
		
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
			result += '\n - %s' % util.get_system_name(currentSystem)
			fleetKeys = systems[currentSystem].keys()
			for f in range(0, len(fleetKeys)):
				currentFleet = fleetKeys[f]
				fleetCount = systems[currentSystem][currentFleet]
				activeFlag = '[CURR] ' if currentFleet == accountHash else ''
				result += '\n%s\t - %s : %s' % (activeFlag, util.get_fleet_name(currentFleet), fleetCount)
		
	print result
	
def attack(params=None):
	if not putil.hasAtLeast(params, 2):
		raise CommandException('An origin system and fleet must be specified')
	verbose = putil.retrieve(params, '-v', True, False)
	abort = putil.retrieve(params, '-a', True, False)
	originFragment = params[0]
	enemyFragment = params[1]
	originHash = putil.naturalMatch(originFragment, database.getStarLogHashes())
	if originHash is None:
		raise CommandException('Unable to find an origin system containing %s' % originFragment)
	highestHash = database.getStarLogHighest(originHash)['hash']
	enemyHash = putil.naturalMatch(enemyFragment, database.getFleets(highestHash))
	if enemyHash is None:
		raise CommandException('Unable to find a fleet containing %s' % enemyFragment)
	enemyDeployments = database.getUnusedEvents(highestHash, originHash, enemyHash)
	if enemyDeployments is None:
		raise CommandException('Fleet %s has no ships deployed in %s' % (util.get_fleet_name(enemyHash), util.get_system_name(originHash)))
	accountInfo = database.getAccount()
	friendlyHash = util.sha256(accountInfo['public_key'])
	friendlyDeployments = database.getUnusedEvents(highestHash, originHash, friendlyHash)
	friendlyCount = 0
	for friendlyDeployment in friendlyDeployments:
		friendlyCount += friendlyDeployment['count']
	if friendlyCount == 0:
		raise CommandException('None of your fleet is deployed to %s' % util.get_system_name(originHash))
	
	# TODO: Break this out into its own get call.
	attackEvent = {
		'fleet_hash': friendlyHash,
		'fleet_key': accountInfo['public_key'],
		'hash': None,
		'inputs': [],
		'outputs': [],
		'signature': None,
		'type': 'attack'
	}

	inputIndex = 0
	enemyCount = 0
	for enemyDeployment in enemyDeployments:
		attackEvent['inputs'].append(getEventInput(inputIndex, enemyDeployment['key']))
		enemyCount += enemyDeployment['count']
		inputIndex += 1
		if friendlyCount <= enemyCount:
			break
	friendlyCount = 0
	for friendlyDeployment in friendlyDeployments:
		attackEvent['inputs'].append(getEventInput(inputIndex, friendlyDeployment['key']))
		friendlyCount += friendlyDeployment['count']
		inputIndex += 1
		if enemyCount <= friendlyCount:
			break
	if enemyCount < friendlyCount:
		attackEvent['outputs'].append(getEventOutput(0, friendlyCount - enemyCount, friendlyHash, util.get_unique_key(), originHash, 'attack'))
	elif friendlyCount < enemyCount:
		attackEvent['outputs'].append(getEventOutput(0, enemyCount - friendlyCount, enemyHash, util.get_unique_key(), originHash, 'attack'))
	
	attackEvent['hash'] = util.hash_event(attackEvent)
	attackEvent['signature'] = util.rsa_sign(accountInfo['private_key'], attackEvent['hash'])

	if verbose:
		print prettyJson(attackEvent)
	if not abort:
		result = postRequest(eventsUrl, attackEvent)
		prefix, postfix = successColor if result == 200 else errorColor, defaultColor
		print 'Posted attack event with response %s%s%s' % (prefix, result, postfix)

def jump(params=None):
	originFragment = None
	destinationFragment = None
	verbose = putil.retrieve(params, '-v', True, False)
	render = putil.retrieve(params, '-r', True, False)
	abort = putil.retrieve(params, '-a', True, False)
	# lossy = putil.retrieve(params, '-l', True, False)
	# TODO: Add actual support for non-lossy jumps.
	lossy = True
	count = None
	if putil.hasAny(params):
		if len(params) < 2:
			raise CommandException('An origin and destination system must be specified')
		originFragment = params[0]
		destinationFragment = params[1]
		if 2 < len(params) and isinstance(params[2], int):
			count = int(params[2])
	else:
		raise CommandException('Specify an origin and destination system')
	hashes = database.getStarLogHashes()
	originHash = putil.naturalMatch(originFragment, hashes)
	if originHash is None:
		raise CommandException('Unable to find an origin system containing %s' % originFragment)
	destinationHash = putil.naturalMatch(destinationFragment, hashes)
	if destinationHash is None:
		raise CommandException('Unable to find a destination system containing %s' % destinationFragment)
	if not database.getStarLogsShareChain([originHash, destinationHash]):
		raise CommandException('Systems %s and %s exist on different chains' % (util.get_system_name(originHash), util.get_system_name(destinationHash)))
	highestHash = database.getStarLogHighest(database.getStarLogHighestFromList([originHash, destinationHash]))['hash']
	accountInfo = database.getAccount()
	fleetHash = util.sha256(accountInfo['public_key'])
	deployments = database.getUnusedEvents(fromStarLog=highestHash, systemHash=originHash, fleetHash=fleetHash)
	totalShips = 0
	for deployment in deployments:
		totalShips += deployment['count']
	if count is None:
		count = totalShips
		lossy = True
	elif totalShips < count:
		raise CommandException('Not enough ships to jump from the origin system')
	if count <= 0:
		raise CommandException('A number of ships greater than zero must be specified for a jump')
	# TODO: Insert support for non-lossy jumps here.
	jumpCost = util.get_jump_cost(destinationHash, originHash, count)
	if jumpCost == count:
		raise CommandException('Unable to complete a jump where all ships would be lost')

	# TODO: Break this out into its own get call.
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
	jumpKey = util.sha256('%s%s%s%s' % (util.get_time(), fleetHash, originHash, destinationHash))
	if 0 < extraShips:
		outputs.append(getEventOutput(index, extraShips, fleetHash, util.get_unique_key(), originHash, 'jump'))
		index += 1
	outputs.append(getEventOutput(index, count - jumpCost, fleetHash, jumpKey, destinationHash, 'jump'))

	jumpEvent['inputs'] = inputs
	jumpEvent['outputs'] = outputs
	jumpEvent['hash'] = util.hash_event(jumpEvent)
	jumpEvent['signature'] = util.rsa_sign(accountInfo['private_key'], jumpEvent['hash'])

	if verbose:
		print prettyJson(jumpEvent)
	if render:
		renderJump(originHash, destinationHash)
	if not abort:
		result = postRequest(eventsUrl, jumpEvent)
		prefix, postfix = successColor if result == 200 else errorColor, defaultColor
		print 'Posted jump event with response %s%s%s' % (prefix, result, postfix)

def renderJump(originHash, destinationHash):
	highest = database.getStarLogHighestFromList([originHash, destinationHash])
	
	figure = pyplot.figure()
	axes = figure.add_subplot(111, projection='3d')

	for currentSystem in database.getStarLogHashes(highest):
		currentPosition = util.get_cartesian(currentSystem)
		xs = [ currentPosition[0], currentPosition[0] ]
		ys = [ currentPosition[1], currentPosition[1] ]
		zs = [ 0, currentPosition[2] ]
		axes.plot(xs, ys, zs)
		axes.scatter(currentPosition[0], currentPosition[1], currentPosition[2], label=util.get_system_name(currentSystem))
	originPosition = util.get_cartesian(originHash)
	destinationPosition = util.get_cartesian(destinationHash)
	xs = [ originPosition[0], destinationPosition[0] ]
	ys = [ originPosition[1], destinationPosition[1] ]
	zs = [ originPosition[2], destinationPosition[2] ]
	axes.plot(xs, ys, zs, linestyle=':')
	
	axes.legend()
	axes.set_title('Jump %s -> %s' % (util.get_system_name(originHash), util.get_system_name(destinationHash)))
	axes.set_xlabel('X')
	axes.set_ylabel('Y')
	axes.set_zlabel('Z')

	pyplot.show()

def renderJumpRange(params=None):
	if not putil.hasAny(params):
		raise CommandException('Specify an origin system to render the jump range from')
	originFragment = putil.singleStr(params)
	destinationFragment = putil.retrieveValue(params, '-d', None)

	hashes = database.getStarLogHashes()
	originHash = putil.naturalMatch(originFragment, hashes)
	if originHash is None:
		raise CommandException('Unable to find an origin system containing %s' % originFragment)
	destinationHash = None
	highest = None
	if destinationFragment is not None:
		destinationHash = putil.naturalMatch(destinationFragment, hashes)
		if destinationHash is None:
			raise CommandException('Unable to find a destination system containing %s' % destinationFragment)
		if not database.getStarLogsShareChain([originHash, destinationHash]):
			raise CommandException('Systems %s and %s exist on different chains' % (util.get_system_name(originHash), util.get_system_name(destinationHash)))
		highest = database.getStarLogHighest(database.getStarLogHighestFromList([originHash, destinationHash]))['hash']
	
	figure = pyplot.figure()
	axes = figure.add_subplot(111, projection='3d')
	hueStart = 0.327
	hueEnd = 0.0
	hueDelta = hueEnd - hueStart
	for currentSystem in database.getStarLogHashes(highest):
		cost = util.get_jump_cost(originHash, currentSystem)
		costHue = hueStart + (cost * hueDelta)
		costValue = 0.0 if cost == 1.0 else 1.0
		color = pycolors.hsv_to_rgb([costHue, 0.7, costValue])
		currentPosition = util.get_cartesian(currentSystem)
		xs = [ currentPosition[0], currentPosition[0] ]
		ys = [ currentPosition[1], currentPosition[1] ]
		zs = [ 0, currentPosition[2] ]
		axes.plot(xs, ys, zs, c=color)
		marker = '^' if currentSystem == originHash else 'o'
		axes.scatter(currentPosition[0], currentPosition[1], currentPosition[2], label=util.get_system_name(currentSystem), c=color, marker=marker)
	if destinationHash is not None:
		originPosition = util.get_cartesian(originHash)
		destinationPosition = util.get_cartesian(destinationHash)
		xs = [ originPosition[0], destinationPosition[0] ]
		ys = [ originPosition[1], destinationPosition[1] ]
		zs = [ originPosition[2], destinationPosition[2] ]
		axes.plot(xs, ys, zs, linestyle=':')
	
	axes.legend()
	axes.set_title('Jump Range %s' % util.get_system_name(originHash))
	axes.set_xlabel('X')
	axes.set_ylabel('Y')
	axes.set_zlabel('Z')
	
	pyplot.show()

def systemPosition(params=None):
	if not putil.hasSingle(params):
		raise CommandException('An origin system must be specified')
	originFragment = putil.singleStr(params)
	originHash = putil.naturalMatch(originFragment, database.getStarLogHashes())
	if originHash is None:
		raise CommandException('Unable to find an origin system containing %s' % originFragment)
	print '%s system is at %s' % (util.get_system_name(originHash), util.get_cartesian(originHash))

def systemDistance(params=None):
	if not putil.hasCount(params, 2):
		raise CommandException('An origin and destination system must be specified')
	originFragment = params[0]
	destinationFragment = params[1]
	hashes = database.getStarLogHashes()
	originHash = putil.naturalMatch(originFragment, hashes)
	if originHash is None:
		raise CommandException('Unable to find an origin system containing %s' % originFragment)
	destinationHash = putil.naturalMatch(destinationFragment, hashes)
	if destinationHash is None:
		raise CommandException('Unable to find a destination system containing %s' % destinationFragment)
	if not database.getStarLogsShareChain([originHash, destinationHash]):
		raise CommandException('Systems %s and %s exist on different chains' % (util.get_system_name(originHash), util.get_system_name(destinationHash)))
	print 'Distance between %s and %s is %s' % (util.get_system_name(originHash), util.get_system_name(destinationHash), util.get_distance(originHash, destinationHash))

def systemAverageDistances(params=None):
	originHash = None
	if putil.hasSingle(params):
		originFragment = params[0]
		originHash = putil.naturalMatch(originFragment, database.getStarLogHashes())
		if originHash is None:
			raise CommandException('Unable to find an origin system containing %s' % originFragment)
	total = 0
	count = 0
	if originHash:
		for currentHash in database.getStarLogHashes(originHash):
			if currentHash == originHash:
				continue
			total += util.get_distance(currentHash, originHash)
			count += 1
	else:
		hashes = database.getStarLogHashes(fromHighest=True)
		for currentHash in hashes:
			hashes = hashes[1:]
			for targetHash in hashes:
				total += util.get_distance(currentHash, targetHash)
				count += 1
	if count == 0:
		print 'No systems to get the average distances of'
	else:
		average = total / count
		if originHash is None:
			print 'Average distance between all systems is %s' % average
		else:
			print 'Average distance to system %s is %s' % (util.get_system_name(originHash), average)

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
			raise CommandException('Unable to find an origin system containing %s' % originFragment)
	if originHash:
		bestSystem = None
		bestDistance = 0 if calculatingMax else 999999999
		for currentHash in database.getStarLogHashes(originHash):
			if currentHash == originHash:
				continue
			dist = util.get_distance(originHash, currentHash)
			if (calculatingMax and bestDistance < dist) or (not calculatingMax and dist < bestDistance):
				bestSystem = currentHash
				bestDistance = dist
		print '%s system from %s is %s, with a distance of %s' % (modifier, util.get_system_name(originHash), util.get_system_name(bestSystem), bestDistance)
	else:
		hashes = database.getStarLogHashes(fromHighest=True)
		bestSystemOrigin = None
		bestSystemDestination = None
		bestDistance = 0 if calculatingMax else 999999999
		for currentHash in hashes:
			hashes = hashes[1:]
			for targetHash in hashes:
				dist = util.get_system_name(currentHash, targetHash)
				if (calculatingMax and bestDistance < dist) or (not calculatingMax and dist < bestDistance):
					bestSystemOrigin = currentHash
					bestSystemDestination = targetHash
					bestDistance = dist
		print '%s systems are %s and %s, with a distance of %s' % (modifier, util.get_system_name(bestSystemOrigin), util.get_system_name(bestSystemDestination), bestDistance)

def pollInput():
	if platform.startswith('win'):
		returnSequence = [ 13 ]
		upSequence = [ 224, 72 ]
		downSequence = [ 224, 80 ]
		leftSequence = [ 224, 75 ]
		rightSequence = [ 224, 77 ]
		backSequence = [ 8 ]
		controlCSequence = [ 3 ]
		tabSequence = [ 9 ]
		doubleEscapeSequence = [ 27, 27 ]
	else:
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
	print 'Starting probe...'
	rules = getRequest(rulesUrl)
	if not rules:
		raise ValueError('null rules')
	
	environ['DIFFICULTY_FUDGE'] = str(rules['difficulty_fudge'])
	environ['DIFFICULTY_INTERVAL'] = str(rules['difficulty_interval'])
	environ['DIFFICULTY_DURATION'] = str(rules['difficulty_duration'])
	environ['DIFFICULTY_START'] = str(rules['difficulty_start'])
	environ['SHIP_REWARD'] = str(rules['ship_reward'])
	environ['CARTESIAN_DIGITS'] = str(rules['cartesian_digits'])
	environ['JUMP_COST_MIN'] = str(rules['jump_cost_min'])
	environ['JUMP_COST_MAX'] = str(rules['jump_cost_max'])
	environ['JUMP_DIST_MAX'] = str(rules['jump_distance_max'])
	environ['STARLOGS_MAX_BYTES'] = str(rules['star_logs_max_limit'])
	environ['EVENTS_MAX_BYTES'] = str(rules['events_max_limit'])

	environ['COMMAND_HISTORY'] = getenv('COMMAND_HISTORY', '100')

	print 'Connected to %s\n\t - Fudge: %s\n\t - Interval: %s\n\t - Duration: %s\n\t - Starting Difficulty: %s\n\t - Ship Reward: %s' % (hostUrl, util.difficultyFudge(), util.difficultyInterval(), util.difficultyDuration(), util.difficultyStart(), util.shipReward())
	minX, minY, minZ = util.get_cartesian_minimum()
	maxX, maxY, maxZ = util.get_cartesian_maximum()
	universeSize = '( %s, %s, %s ) - ( %s, %s, %s )' % (minX, minY, minZ, maxX, maxY, maxZ)
	print '\t - Universe Size: %s\n\t - Jump Cost: %s%% to %s%%\n\t - Jump Distance Max: %s' % (universeSize, util.jumpCostMinimum() * 100, util.jumpCostMaximum() * 100, util.jumpDistanceMaximum())
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
		'sync': createCommand(
			sync,
			'Syncs the local cache with updates from the server',
			[
				'"-f" replaces the local cache with fresh results',
				'"-s" silently executes the command'
			]
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
				'"-f" probes for a starlog ontop of the best matching system',
				'"-l" loop and probe again after posting to the server',
				'"-w" number of seconds to wait before looping to probe again',
				'"-b" blindly probe for new stars without syncing inbetween'
			]
		),
		'account': createCommand(
			account,
			'Information about the current account',
			[
				'Passing no arguments gets the current account information',
				'"-a" lists all accounts stored in persistent data',
				'"-s" followed by an account name changes the current account to the specified one',
				'"-c" followed by an account name creates a new account'
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
		'attack': createCommand(
			attack,
			'Attack fleets in the specified system',
			[
				'Passing a partial origin and enemy fleet hash will attack the best matching fleet',
				'"-v" prints the attack to the console',
				'"-a" aborts without posting attack to the server'
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
		'jrange': createCommand(
			renderJumpRange,
			'Renders the range of jumps in an external plotter',
			[
				'Passing partial origin hash will render with that system in focus',
				'"-d" followed by a destination hash will render a line between the best matching system and the origin'
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
			stdout.write('\r%s%s%s' % (commandPrefix, command, cursorEraseSequence))
			stdout.write('\r%s' % (cursorForwardSequence % (commandIndex + len(commandPrefix))))

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
					command = command[:commandIndex - 1] + command[commandIndex:]
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
			stdout.write('\r%s%s%s%s%s' % (commandPrefix, boldColor, command, defaultColor, cursorEraseSequence))
		if oldCommandIndex != commandIndex:
			stdout.write('\r%s' % (cursorForwardSequence % (commandIndex + len(commandPrefix))))

		if isReturn or isDoubleEscape:
			stdout.write('\n')
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
		except CommandException as exception:
			print exception
		except:
			printException()
			print 'Error with your last command'
		database.addCommand(command, util.get_time(), commandInSession)
		command = None
		commandIndex = 0
		commandHistory = -1
		commandInSession += 1

if __name__ == '__main__':
	main()
	stdout.write('\nExiting...\n')