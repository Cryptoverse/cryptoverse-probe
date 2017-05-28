import re
import binascii
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_public_key
import util


def byte_size(limit, target):
    if limit < len(target):
        raise Exception('Length is not less than %s bytes' % limit)


def field_is_sha256(sha, field_name=None):
    """Verifies a string is a possible Sha256 hash.

    Args:
        sha (str): Hash to verify.
    """
    if not re.match(r'^[A-Fa-f0-9]{64}$', sha):
        raise Exception('Field is not a hash' if field_name is None else 'Field %s is not a hash' % field_name)


def rsa(public_key, signature, message):
    """Verifies an Rsa signature.
    Args:
        public_key (str): Public key with BEGIN and END sections.
        signature (str): Hex value of the signature with its leading 0x stripped.
        message (str): Message that was signed, unhashed.
    """
    try:
        public_rsa = load_pem_public_key(bytes(public_key), backend=default_backend())
        hashed = util.sha256(message)
        public_rsa.verify(
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
    """Verifies the hash matches the Sha256'd message.

    Args:
        sha (str): A Sha256 hash result.
        message (str): Message to hash and compare to.
    """
    if not sha == util.sha256(message):
        raise Exception('Sha256 does not match message' if name is None else 'Sha256 of %s does not match hash' % name)


def star_log(star_log_json):
    """Verifies the starlog has all the required fields, and any hashes and signatures match up.

    Args:
        star_log_json (dict): Target starlog json.
    """
    if not isinstance(star_log_json['hash'], basestring):
        raise Exception('hash is not a string')
    if not isinstance(star_log_json['version'], int):
        raise Exception('version is not an integer')
    if not isinstance(star_log_json['previous_hash'], basestring):
        raise Exception('previous_hash is not a string')
    if not isinstance(star_log_json['difficulty'], int):
        raise Exception('difficulty is not an integer')
    if not isinstance(star_log_json['nonce'], int):
        raise Exception('nonce is not an integer')
    if not isinstance(star_log_json['time'], int):
        raise Exception('time is not an integer')
    if util.get_time() < star_log_json['time']:
        raise Exception('time is greater than the current time')
    if not isinstance(star_log_json['events_hash'], basestring):
        raise Exception('events_hash is not a string')
    if star_log_json['events'] is None:
        raise Exception('events is missing')
    
    field_is_sha256(star_log_json['hash'], 'hash')
    field_is_sha256(star_log_json['previous_hash'], 'previous_hash')
    field_is_sha256(star_log_json['events_hash'], 'events_hash')
    sha256(star_log_json['hash'], util.concat_star_log_header(star_log_json), 'log_header')
    if not star_log_json['events_hash'] == util.hash_events(star_log_json['events']):
        raise Exception('events_hash does not match actual hash')
    difficulty(star_log_json['difficulty'], star_log_json['hash'])
    events(star_log_json['events'])


def events(events_json):
    """Verifies the state of a star log has all the required fields, and any hashes and signatures match up.

    Args:
        events_json (dict): Events json.
    """
    remaining_ship_rewards = util.shipReward()
    input_keys = []
    output_keys = []
    for current_event in events_json:
        event(current_event)
        if current_event['type'] == 'reward':
            if len(current_event['inputs']) != 0:
                raise Exception('reward events cannot have inputs')
            if len(current_event['outputs']) == 0:
                raise Exception('reward events with no recipients should not be included')
            for current_output in current_event['outputs']:
                remaining_ship_rewards -= current_output['count']
                if remaining_ship_rewards < 0:
                    raise Exception('number of ships rewarded is out of range')
                if current_output['type'] != 'reward':
                    raise Exception('reward outputs must be of type "reward"')
        elif current_event['type'] == 'jump':
            if len(current_event['inputs']) == 0:
                raise Exception('jump events cannot have zero inputs')
            output_length = len(current_event['outputs'])
            if output_length == 0:
                raise Exception('jump events cannot have zero outputs')
            if 2 < output_length:
                raise Exception('jump events cannot have more than 2 outputs')
            if 2 == output_length and current_event['outputs'][0]['star_system'] == current_event['outputs'][1]['star_system']:
                raise Exception('jump event cannot split in new system')
            for current_output in current_event['outputs']:
                if current_output['count'] <= 0:
                    raise Exception('jump events cannot jump zero or less ships')
                if current_output['type'] != 'jump':
                    raise Exception('jump outputs must be of type "jump"')
        elif current_event['type'] == 'attack':
            if len(current_event['inputs']) < 2:
                raise Exception('attack events need at least two inputs')
            if len(current_event['inputs']) < len(current_event['outputs']):
                raise Exception('attacks cannot have more outputs than inputs')
            for current_output in current_event['outputs']:
                if current_output['count'] <= 0:
                    raise Exception('attack events cannot outputs zero or less ships')
                if current_output['attack'] != 'attack':
                    raise Exception('attack outputs must be of type "attack"')
        else:
            raise ValueError('unrecognized event of type %s' % current_event['type'])
        
        for current_input in current_event['inputs']:
            key = current_input['key']
            if key in input_keys:
                raise Exception('event input key %s is listed more than once' % key)
            input_keys.append(key)
        for current_output in current_event['outputs']:
            key = current_output['key']
            if key in output_keys:
                raise Exception('event output key %s is listed more than once' % key)
            output_keys.append(key)


def event(event_json, require_index=True, require_star_system=False, reward_allowed=True):
    """Verifies the fields of an event.

    Args:
        event_json (dict): Target.
        require_index (bool): Verifies an integer index is included if True.
        require_star_system (bool): Verifies that every output specifies a star system if True.
    """
    if not isinstance(event_json['type'], basestring):
        raise Exception('type is not a string')
    if not isinstance(event_json['fleet_hash'], basestring):
        raise Exception('fleet_hash is not a string')
    if not isinstance(event_json['fleet_key'], basestring):
        raise Exception('fleet_key is not a string')
    if not isinstance(event_json['hash'], basestring):
        raise Exception('hash is not a string')
    if require_index and not isinstance(event_json['index'], int):
        raise Exception('index is not an integer')
    
    field_is_sha256(event_json['hash'], 'hash')

    if not reward_allowed and event_json['type'] == 'reward':
        raise Exception('event of type %s forbidden' % event_json['type'])
    if event_json['type'] not in ['reward', 'jump', 'attack']:
        raise Exception('unrecognized event of type %s' % event_json['type'])

    input_indices = []
    for currentInput in event_json['inputs']:
        event_input(currentInput)
        input_index = currentInput['index']
        if input_index in input_indices:
            raise Exception('duplicate input index %s' % input_index)
        input_indices.append(input_index)
    
    output_indices = []
    for currentOutput in event_json['outputs']:
        event_output(currentOutput, require_star_system)
        output_index = currentOutput['index']
        if output_index in output_indices:
            raise Exception('duplicate output index %s' % output_index)
        output_indices.append(output_index)

    if util.hash_event(event_json) != event_json['hash']:
        raise Exception('provided hash does not match the calculated one')

    field_is_sha256(event_json['fleet_hash'], 'fleet_hash')
    sha256(event_json['fleet_hash'], event_json['fleet_key'], 'fleet_key')
    rsa(util.expand_rsa_public_key(event_json['fleet_key']), event_json['signature'], event_json['hash'])


def event_input(input_json):
    if not isinstance(input_json['index'], int):
        raise Exception('index is not an integer')
    if not isinstance(input_json['key'], basestring):
        raise Exception('key is not a string')
    
    if input_json['index'] < 0:
        raise Exception('index is out of range')

    field_is_sha256(input_json['key'], 'key')


def event_output(output_json, require_star_system=False):
    if not isinstance(output_json['index'], int):
        raise Exception('index is not an integer')
    if not isinstance(output_json['type'], basestring):
        raise Exception('type is not a string')
    if not isinstance(output_json['fleet_hash'], basestring):
        raise Exception('fleet_hash is not a string')
    if not isinstance(output_json['key'], basestring):
        raise Exception('key is not a string')
    if output_json['star_system'] is None and require_star_system:
        raise Exception('star_system is missing')
    if output_json['star_system'] is not None:
        if not isinstance(output_json['star_system'], basestring):
            raise Exception('star_system is not a string')
        field_is_sha256(output_json['star_system'], 'star_system')
    if not isinstance(output_json['count'], int):
        raise Exception('count is not an integer')
    
    if output_json['index'] < 0:
        raise Exception('index is out of range')
    if output_json['count'] <= 0:
        raise Exception('count is out of range')

    field_is_sha256(output_json['fleet_hash'], 'fleet_hash')
    field_is_sha256(output_json['key'], 'key')


def event_rsa(event_json):
    """Verifies the Rsa signature of the provided event json.

    Args:
        event_json (dict): Event to validate.
    """
    try:
        rsa(util.expand_rsa_public_key(event_json['fleet_key']), event_json['signature'], util.concat_event(event_json))
    except InvalidSignature:
        raise Exception('Invalid RSA signature')


def difficulty(packed, sha, validate_params=True):
    """Takes the integer form of difficulty and verifies that the hash is less than it.

    Args:
        packed (int): Packed target difficulty the provided Sha256 hash must meet.
        sha (str): Hex target to test, stripped of its leading 0x.
    """
    if validate_params:
        if not isinstance(packed, (int, long)):
            raise Exception('difficulty is not an int')
        field_is_sha256(sha, 'difficulty target')
    
    mask = util.unpack_bits(packed, True)
    leading_zeros = len(mask) - len(mask.lstrip('0'))
    difficulty_unpacked(mask, leading_zeros, sha, validate_params)


def difficulty_unpacked(unpacked_stripped, leading_zeros, sha, validate_params=True):
    """Takes the unpacked form of difficulty and verifies that the hash is less than it.

    Args:
        unpacked_stripped (str): Unpacked target difficulty the provided Sha256 hash must meet.
        sha (str): Hex target to test, stripped of its leading 0x.
    """
    if validate_params:
        field_is_sha256(sha, 'difficulty target')
    
    try:
        for i in range(0, leading_zeros):
            if sha[i] != '0':
                raise Exception('Hash is greater than packed target')
        significant = sha[:len(unpacked_stripped)]
        if int(unpacked_stripped, 16) <= int(significant, 16):
            raise Exception('Hash is greater than packed target')
    except:
        raise Exception('Unable to cast to int from hexidecimal')


def lost_count(count, lost_count, origin_hash, destination_hash):
    # TODO: check the lost count is correct
    pass
