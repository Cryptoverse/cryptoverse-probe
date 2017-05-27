import re
import binascii
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import util

def byteSize(limit, target):
	if limit < len(target):
		raise Exception('Length is not less than %s bytes' % limit)

def fieldIsSha256(sha, fieldName=None):
	'''Verifies a string is a possible Sha256 hash.

	Args:
		sha (str): Hash to verify.
	'''
	if not re.match(r'^[A-Fa-f0-9]{64}$', sha):
		raise Exception('Field is not a hash' if fieldName is None else 'Field %s is not a hash' % fieldName)

def rsa(publicKey, signature, message):
	'''Verifies an Rsa signature.
	Args:
		publicKey (str): Public key with BEGIN and END sections.
		signature (str): Hex value of the signature with its leading 0x stripped.
		message (str): Message that was signed, unhashed.
	'''
	try:
		publicRsa = load_pem_public_key(bytes(publicKey), backend=default_backend())
		hashed = util.sha256(message)
		publicRsa.verify(
			binascii.unhexlify(signature),
			hashed,
			padding.PSS(
				mgf=padding.MGF1(hashes.SHA256()),
				salt_length=padding.PSS.MAX_LENGTH
			),
			hashes.SHA256()
		)
	except InvalidSignature:
		raise Exception('Invalid signature')

def sha256(sha, message, name=None):
	'''Verifies the hash matches the Sha256'd message.

	Args:
		sha (str): A Sha256 hash result.
		message (str): Message to hash and compare to.
	'''
	if not sha == util.sha256(message):
		raise Exception('Sha256 does not match message' if name is None else 'Sha256 of %s does not match hash' % name)

def starLog(starLogJson):
	'''Verifies the starlog has all the required fields, and any hashes and signatures match up.

	Args:
		starLogJson (dict): Target starlog json.
	'''
	if not isinstance(starLogJson['hash'], basestring):
		raise Exception('hash is not a string')
	if not isinstance(starLogJson['version'], int):
		raise Exception('version is not an integer')
	if not isinstance(starLogJson['previous_hash'], basestring):
		raise Exception('previous_hash is not a string')
	if not isinstance(starLogJson['difficulty'], int):
		raise Exception('difficulty is not an integer')
	if not isinstance(starLogJson['nonce'], int):
		raise Exception('nonce is not an integer')
	if not isinstance(starLogJson['time'], int):
		raise Exception('time is not an integer')
	if util.get_time() < starLogJson['time']:
		raise Exception('time is greater than the current time')
	if not isinstance(starLogJson['events_hash'], basestring):
		raise Exception('events_hash is not a string')
	if starLogJson['events'] is None:
		raise Exception('events is missing')
	
	fieldIsSha256(starLogJson['hash'], 'hash')
	fieldIsSha256(starLogJson['previous_hash'], 'previous_hash')
	fieldIsSha256(starLogJson['events_hash'], 'events_hash')
	sha256(starLogJson['hash'], util.concat_star_log_header(starLogJson), 'log_header')
	if not starLogJson['events_hash'] == util.hash_events(starLogJson['events']):
		raise Exception('events_hash does not match actual hash')
	difficulty(starLogJson['difficulty'], starLogJson['hash'])
	events(starLogJson['events'])

def events(eventsJson):
	'''Verifies the state of a star log has all the required fields, and any hashes and signatures match up.

	Args:
		stateJson (dict): State json.
	'''
	remainingShipRewards = util.shipReward()
	inputKeys = []
	outputKeys = []
	for currentEvent in eventsJson:
		event(currentEvent)
		if currentEvent['type'] == 'reward':
			if len(currentEvent['inputs']) != 0:
				raise Exception('reward events cannot have inputs')
			if len(currentEvent['outputs']) == 0:
				raise Exception('reward events with no recipients should not be included')
			for currentOutput in currentEvent['outputs']:
				remainingShipRewards -= currentOutput['count']
				if remainingShipRewards < 0:
					raise Exception('number of ships rewarded is out of range')
				if currentOutput['type'] != 'reward':
					raise Exception('reward outputs must be of type "reward"')
		elif currentEvent['type'] == 'jump':
			if len(currentEvent['inputs']) == 0:
				raise Exception('jump events cannot have zero inputs')
			outputLength = len(currentEvent['outputs'])
			if outputLength == 0:
				raise Exception('jump events cannot have zero outputs')
			if 2 < outputLength:
				raise Exception('jump events cannot have more than 2 outputs')
			if 2 == outputLength and currentEvent['outputs'][0]['star_system'] == currentEvent['outputs'][1]['star_system']:
				raise Exception('jump event cannot split in new system')
			for currentOutput in currentEvent['outputs']:
				if currentOutput['count'] <= 0:
					raise Exception('jump events cannot jump zero or less ships')
				if currentOutput['type'] != 'jump':
					raise Exception('jump outputs must be of type "jump"')
		elif currentEvent['type'] == 'attack':
			if len(currentEvent['inputs']) < 2:
				raise Exception('attack events need at least two inputs')
			if len(currentEvent['inputs']) < len(currentEvent['outputs']):
				raise Exception('attacks cannot have more outputs than inputs')
			for currentOutput in currentEvent['outputs']:
				if currentOutput['count'] <= 0:
					raise Exception('attack events cannot outputs zero or less ships')
				if currentOutput['attack'] != 'attack':
					raise Exception('attack outputs must be of type "attack"')
		else:
			raise ValueError('unrecognized event of type %s' % currentEvent['type'])
		
		for currentInput in currentEvent['inputs']:
			key = currentInput['key']
			if key in inputKeys:
				raise Exception('event input key %s is listed more than once' % key)
			inputKeys.append(key)
		for currentOutput in currentEvent['outputs']:
			key = currentOutput['key']
			if key in outputKeys:
				raise Exception('event output key %s is listed more than once' % key)
			outputKeys.append(key)

def event(eventJson, requireIndex=True, requireStarSystem=False, rewardAllowed=True):
	'''Verifies the fields of an event.

	Args:
		eventJson (dict): Target.
		requireIndex (bool): Verifies an integer index is included if True.
		requireStarSystem (bool): Verifies that every output specifies a star system if True.
	'''
	if not isinstance(eventJson['type'], basestring):
		raise Exception('type is not a string')
	if not isinstance(eventJson['fleet_hash'], basestring):
		raise Exception('fleet_hash is not a string')
	if not isinstance(eventJson['fleet_key'], basestring):
		raise Exception('fleet_key is not a string')
	if not isinstance(eventJson['hash'], basestring):
		raise Exception('hash is not a string')
	if requireIndex and not isinstance(eventJson['index'], int):
		raise Exception('index is not an integer')
	
	fieldIsSha256(eventJson['hash'], 'hash')

	if not rewardAllowed and eventJson['type'] == 'reward':
		raise Exception('event of type %s forbidden' % eventJson['type'])
	if eventJson['type'] not in ['reward', 'jump', 'attack']:
		raise Exception('unrecognized event of type %s' % eventJson['type'])

	inputIndices = []
	for currentInput in eventJson['inputs']:
		eventInput(currentInput)
		inputIndex = currentInput['index']
		if inputIndex in inputIndices:
			raise Exception('duplicate input index %s' % inputIndex)
		inputIndices.append(inputIndex)
	
	outputIndices = []
	for currentOutput in eventJson['outputs']:
		eventOutput(currentOutput, requireStarSystem)
		outputIndex = currentOutput['index']
		if outputIndex in outputIndices:
			raise Exception('duplicate output index %s' % outputIndex)
		outputIndices.append(outputIndex)

	if util.hash_event(eventJson) != eventJson['hash']:
		raise Exception('provided hash does not match the calculated one')

	fieldIsSha256(eventJson['fleet_hash'], 'fleet_hash')
	sha256(eventJson['fleet_hash'], eventJson['fleet_key'], 'fleet_key')
	rsa(util.expand_rsa_public_key(eventJson['fleet_key']), eventJson['signature'], eventJson['hash'])

def eventInput(inputJson):
	if not isinstance(inputJson['index'], int):
		raise Exception('index is not an integer')
	if not isinstance(inputJson['key'], basestring):
		raise Exception('key is not a string')
	
	if inputJson['index'] < 0:
		raise Exception('index is out of range')

	fieldIsSha256(inputJson['key'], 'key')

def eventOutput(outputJson, requireStarSystem=False):
	if not isinstance(outputJson['index'], int):
		raise Exception('index is not an integer')
	if not isinstance(outputJson['type'], basestring):
		raise Exception('type is not a string')
	if not isinstance(outputJson['fleet_hash'], basestring):
		raise Exception('fleet_hash is not a string')
	if not isinstance(outputJson['key'], basestring):
		raise Exception('key is not a string')
	if outputJson['star_system'] is None and requireStarSystem:
		raise Exception('star_system is missing')
	if outputJson['star_system'] is not None:
		if not isinstance(outputJson['star_system'], basestring):
			raise Exception('star_system is not a string')
		fieldIsSha256(outputJson['star_system'], 'star_system')
	if not isinstance(outputJson['count'], int):
		raise Exception('count is not an integer')
	
	if outputJson['index'] < 0:
		raise Exception('index is out of range')
	if outputJson['count'] <= 0:
		raise Exception('count is out of range')

	fieldIsSha256(outputJson['fleet_hash'], 'fleet_hash')
	fieldIsSha256(outputJson['key'], 'key')
	
def eventRsa(eventJson):
	'''Verifies the Rsa signature of the provided event json.

	Args:
		eventJson (dict): Event to validate.
	'''
	try:
		rsa(util.expand_rsa_public_key(eventJson['fleet_key']), eventJson['signature'], util.concat_event(eventJson))
	except InvalidSignature:
		raise Exception('Invalid RSA signature')

def difficulty(packed, sha, validateParams=True):
	'''Takes the integer form of difficulty and verifies that the hash is less than it.

	Args:
		packed (int): Packed target difficulty the provided Sha256 hash must meet.
		sha (str): Hex target to test, stripped of its leading 0x.
	'''
	if validateParams:
		if not isinstance(packed, (int, long)):
			raise Exception('difficulty is not an int')
		fieldIsSha256(sha, 'difficulty target')
	
	mask = util.unpack_bits(packed, True)
	leadingZeros = len(mask) - len(mask.lstrip('0'))
	difficultyUnpacked(mask, leadingZeros, sha, validateParams)

def difficultyUnpacked(unpackedStripped, leadingZeros, sha, validateParams=True):
	'''Takes the unpacked form of difficulty and verifies that the hash is less than it.

	Args:
		unpacked (str): Unpacked target difficulty the provided Sha256 hash must meet.
		sha (str): Hex target to test, stripped of its leading 0x.
	'''
	if validateParams:
		fieldIsSha256(sha, 'difficulty target')
	
	try:
		for i in range(0, leadingZeros):
			if sha[i] != '0':
				raise Exception('Hash is greater than packed target')
		significant = sha[:len(unpackedStripped)]
		if int(unpackedStripped, 16) <= int(significant, 16):
			raise Exception('Hash is greater than packed target')
	except:
		raise Exception('Unable to cast to int from hexidecimal')

def lostCount(count, lostCount, originHash, destinationHash):
	# TODO: check the lost count is correct
	pass