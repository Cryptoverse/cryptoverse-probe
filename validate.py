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
	'''Verifies the star log has all the required fields, and any hashes and signatures match up.

	Args:
		target (dict): Target starlog json.
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
	if starLogJson['state']['fleet']:
		if not isinstance(starLogJson['state']['fleet'], basestring):
			raise Exception('state.fleet is not a string')
		fieldIsSha256(starLogJson['state']['fleet'], 'state.fleet')
	
	fieldIsSha256(starLogJson['hash'], 'hash')
	fieldIsSha256(starLogJson['previous_hash'], 'previous_hash')
	fieldIsSha256(starLogJson['state_hash'], 'state_hash')
	sha256(starLogJson['hash'], util.concatStarLogHeader(starLogJson), 'log_header')
	if not starLogJson['state_hash'] == util.hashState(starLogJson['state']):
		raise Exception('state_hash does not match actual hash')
	difficulty(starLogJson['difficulty'], starLogJson['hash'])

def previousJump(previousFleet, jumpJson):
	'''Verifies the fields of a previous jump, included with a starlog by the prober.

	Args:
		jumpJson (dict): Target.
	'''
	if previousFleet is None:
		raise ValueError('previousFleet is missing')
	if jumpJson is None:
		raise ValueError('jumpJson is missing')
	if previousFleet.hash is None:
		raise ValueError('previousFleet.hash is missing')
	if jumpJson['fleet_hash'] is None:
		raise ValueError('jumpJson.fleet_hash is missing')
	if previousFleet.hash != jumpJson['fleet_hash']:
		raise ValueError('previousFleet.hash and jumpJson.fleet_hash do not match')
	

def jumpRsa(jump):
	'''Verifies the Rsa signature of the provided jump json.

	Args:
		jump (dict): Jump to validate.
	'''
	if not rsa(util.expandRsaPublicKey(jump['fleet_key']), jump['signature'], util.concatJump(jump)):
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