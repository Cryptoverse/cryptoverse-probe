import re
import binascii
import traceback
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
	if util.getTime() < starLogJson['time']:
		raise Exception('time is greater than the current time')
	if not isinstance(starLogJson['state_hash'], basestring):
		raise Exception('state_hash is not a string')
	if starLogJson['state'] is None:
		raise Exception('state is missing')
	
	fieldIsSha256(starLogJson['hash'], 'hash')
	fieldIsSha256(starLogJson['previous_hash'], 'previous_hash')
	fieldIsSha256(starLogJson['state_hash'], 'state_hash')
	sha256(starLogJson['hash'], util.concatStarLogHeader(starLogJson), 'log_header')
	if not starLogJson['state_hash'] == util.hashState(starLogJson['state']):
		raise Exception('state_hash does not match actual hash')
	difficulty(starLogJson['difficulty'], starLogJson['hash'])
	state(starLogJson['state'])

def state(stateJson):
	'''Verifies the state of a star log has all the required fields, and any hashes and signatures match up.

	Args:
		stateJson (dict): State json.
	'''
	remainingShipRewards = util.shipReward
	jumpKeys = []
	for currentJump in stateJson['jumps']:
		jump(currentJump)
		if currentJump['origin'] is None:
			remainingShipRewards -= currentJump['count']
			if remainingShipRewards < 0:
				raise ValueError('number of ships rewarded is out of range')
		key = currentJump['key']
		if key in jumpKeys:
			raise ValueError('jump key "%s" is listed more than once' % key)
		jumpKeys.append(key)
	
	systemHashes = []
	for currentSystem in stateJson['star_systems']:
		starSystem(currentSystem)
		systemHash = currentSystem['hash']
		if systemHash in systemHashes:
			raise ValueError('system hash "%s" is listed more than once' % systemHash)
		systemHashes.append(systemHash)

def jump(jumpJson):
	'''Verifies the fields of a jump.

	Args:
		jumpJson (dict): Target.
	'''
	# rewardJump = {
	# 	'fleet_hash': util.sha256(accountInfo['public_key']),
	# 	'fleet_key': accountInfo['public_key'],
	# 	'key': util.sha256('%s%s' % (util.getTime(), accountInfo['public_key'])),
	# 	'origin': None,
	# 	'destination': None,
	# 	'count': util.shipReward,
	# 	'lost_count': 0,
	# 	'signature': None
	# }
	if not isinstance(jumpJson['fleet_hash'], basestring):
		raise Exception('fleet_hash is not a string')
	if not isinstance(jumpJson['fleet_key'], basestring):
		raise Exception('fleet_key is not a string')
	if not isinstance(jumpJson['key'], basestring):
		raise Exception('key is not a string')
	if not isinstance(jumpJson['count'], int):
		raise Exception('count is not a integer')
	if not isinstance(jumpJson['lost_count'], int):
		raise Exception('lost_count is not a integer')
	if not isinstance(jumpJson['signature'], basestring):
		raise Exception('signature is not a string')
	
	if jumpJson['count'] <= 0:
		raise ValueError('count cannot be equal to or less than zero')
	if jumpJson['lost_count'] < 0:
		raise ValueError('lost_count cannot be less than zero')
	if jumpJson['count'] <= jumpJson['lost_count']:
		raise ValueError('count cannot be equal to or less than lost_count')

	if isinstance(jumpJson['destination'], basestring):
		fieldIsSha256(jumpJson['destination'], 'destination')
	if isinstance(jumpJson['origin'], basestring):
		fieldIsSha256(jumpJson['origin'], 'origin')
		lostCount(jumpJson['count'], jumpJson['lost_count'], jumpJson['origin'], jumpJson['destination'])

	fieldIsSha256(jumpJson['key'], 'key')
	sha256(jumpJson['fleet_hash'], jumpJson['fleet_key'], 'fleet_hash')

	jumpRsa(jumpJson)

def starSystem(starSystemJson):
	'''Verifies the fields of a star system.

	Args:
		starSystemJson (dict): Target.
	'''
	# TODO: Validation of star systems.
	pass

def jumpRsa(jumpJson):
	'''Verifies the Rsa signature of the provided jump json.

	Args:
		jump (dict): Jump to validate.
	'''
	try:
		rsa(util.expandRsaPublicKey(jumpJson['fleet_key']), jumpJson['signature'], util.concatJump(jumpJson))
	except InvalidSignature:
		raise Exception('Invalid RSA signature')

def difficulty(packed, sha):
	'''Takes the integer form of difficulty and verifies that the hash is less than it.

	Args:
		packed (int): Packed target difficulty the provided Sha256 hash must meet.
		sha (str): Hex target to test, stripped of its leading 0x.
	'''
	if not isinstance(packed, (int, long)):
		raise Exception('difficulty is not an int')
	
	fieldIsSha256(sha, 'difficulty target')

	mask = util.unpackBits(packed).rstrip('0')
	significant = sha[:len(mask)]
	try:
		if int(mask, 16) <= int(significant, 16):
			raise Exception('Hash is greater than packed target')
	except:
		raise Exception('Unable to cast to int from hexidecimal')

def lostCount(count, lostCount, originHash, destinationHash):
	# TODO: check the lost count is correct
	pass