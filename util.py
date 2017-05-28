import os
import hashlib
import binascii
import time
import math
import uuid
import numpy
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import load_pem_private_key

def difficultyFudge():
    return int(os.getenv('DIFFICULTY_FUDGE', '0'))
def difficultyInterval():
    return int(os.getenv('DIFFICULTY_INTERVAL', '10080'))
def difficultyDuration():
    return int(os.getenv('DIFFICULTY_DURATION', '1209600'))
def difficultyStart():
    return int(os.getenv('DIFFICULTY_START', '486604799'))
def shipReward():
    return int(os.getenv('SHIP_REWARD', '10'))
def maximumStarLogSize():
    return int(os.getenv('STARLOGS_MAX_BYTES', '999999'))
def maximumEventSize():
    return int(os.getenv('EVENTS_MAX_BYTES', '999999'))
def cartesianDigits():
    return int(os.getenv('CARTESIAN_DIGITS', '3'))
def jumpCostMinimum():
    return float(os.getenv('JUMP_COST_MIN', '0.01'))
def jumpCostMaximum():
    return float(os.getenv('JUMP_COST_MAX', '1.0'))
def jumpDistanceMaximum():
    return float(os.getenv('JUMP_DIST_MAX', '2048.0'))
def starLogsMaxLimit():
    return int(os.getenv('STARLOGS_MAX_LIMIT', '10'))
def eventsMaxLimit():
    return int(os.getenv('EVENTS_MAX_LIMIT', '10'))
def chainsMaxLimit():
    return int(os.getenv('CHAINS_MAX_LIMIT', '10'))

MAXIMUM_NONCE = 2147483647
MAXIMUM_TARGET = '00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
EMPTY_TARGET = '0000000000000000000000000000000000000000000000000000000000000000'

EVENT_TYPES = [
    'unknown',
    'reward',
    'jump',
    'attack'
]

SHIP_EVENT_TYPES = [
    'reward',
    'jump',
    'attack'
]

def get_maximum_target():
    if difficultyFudge() == 0:
        return MAXIMUM_TARGET
    if not 0 <= difficultyFudge() <= 8:
        raise Exception('DIFFICULTY_FUDGE must be a value from 0 to 8 (inclusive)')
    return MAXIMUM_TARGET[difficultyFudge():] + MAXIMUM_TARGET[:difficultyFudge()]

if not 3 <= cartesianDigits() <= 21:
    raise Exception('CARTESIAN_DIGITS must be a value from 3 to 21 (inclusive)')

if not 0 <= jumpCostMinimum() < 1:
    raise Exception('JUMP_COST_MIN must be a value from 0.0 to 1.0 (inclusive - exclusive)')

if not 0 < jumpCostMaximum() <= 1:
    raise Exception('JUMP_COST_MAX must be a value from 0.0 to 1.0 (exclusive - inclusive)')

if jumpCostMaximum() <= jumpCostMinimum():
    raise Exception('JUMP_COST_MIN must be less than JUMP_COST_MAX')

if jumpDistanceMaximum() <= 0:
    raise Exception('JUMP_DIST_MAX must be greater than 0.0')


def is_genesis_star_log(sha):
    """Checks if the provided hash could only belong to the parent of the genesis star log.

    Args:
        sha (str): Hash to check.

    Results:
        bool: True if equal to the hash of the parent of the genesis block's parent.
    """
    return sha == EMPTY_TARGET


def sha256(message):
    """Sha256 hash of message.
    
    Args:
        message (str): Message to hash.
    
    Returns:
        str: Sha256 hash of the provided string, or the hash of nothing if None is passed.
    """
    return hashlib.sha256('' if message is None else message).hexdigest()


def difficulty_to_hex(difficulty):
    """Converts a packed int representation of difficulty to its packed hex format.
    
    Args:
        difficulty (int): Packed int format of difficulty.
    
    Returns:
        str: Packed hex format of difficulty, stripped of its leading 0x.
    """
    return hex(difficulty)[2:]


def difficulty_from_hex(difficulty):
    """Takes a hex string of difficulty, missing the 0x, and returns the integer from of difficulty.
    
    Args:
        difficulty (str): Packed hex format of difficulty.
    
    Returns:
        int: Packed int format of difficulty.
    """
    return int(difficulty, 16)


def difficulty_from_target(target):
    """Calculates the difficulty this target is equal to.
    
    Args:
        target (str): Hex target, stripped of its leading 0x.
    
    Returns:
        str: Packed hex difficulty of the target, stripped of its leading 0x.
    """
    # TODO: Cleanup shitwise operators that use string transformations, they're ugly... though they do work...
    stripped = target.lstrip('0')

    # If we stripped too many zeros, add one back.
    if len(stripped) % 2 == 0:
        stripped = '0' + stripped

    count = len(stripped) / 2
    stripped = stripped[:6]

    # If we're past the max value allowed for the mantissa, truncate it further and increase the exponent.
    if 0x7fffff < int(stripped, 16):
        stripped = '00' + stripped[0:4]
        count += 1

    result = hex(count)[2:] + stripped

    # Negative number switcharoo
    if 0x00800000 & int(result, 16):
        result = hex(count + 1)[2:] + '00' + stripped[:4]
    # # Lazy max number check...
    # if 0x1d00ffff < int(result, 16):
    #     result = '1d00ffff'
    return result


def is_difficulty_changing(height):
    """Checks if it's time to recalculate difficulty.
    
    Args:
        height (int): Height of an entry in the chain.
    
    Returns:
        bool: True if a difficulty recalculation should take place.
    """
    return (height % difficultyInterval()) == 0


def calculate_difficulty(difficulty, duration):
    """Takes the packed integer difficulty and the duration of the last interval to calculate the new difficulty.
    
    Args:
        difficulty (int): Packed int format of the last difficulty.
        duration (int): Seconds elapsed since the last time difficulty was calculated.
    
    Returns:
        int: Packed int format of the next difficulty.
    """
    if duration < difficultyDuration() / 4:
        duration = difficultyDuration() / 4
    elif duration > difficultyDuration() * 4:
        duration = difficultyDuration() * 4

    limit = long(get_maximum_target(), 16)
    result = long(unpack_bits(difficulty), 16)
    result *= duration
    result /= difficultyDuration()

    if limit < result:
        result = limit

    return difficulty_from_hex(difficulty_from_target(hex(result)[2:]))


def concat_star_log_header(star_log, include_nonce=True):
    """Concats the header information from the provided json.
    
    Args:
        star_log (dict): StarLog to create header from.

    Returns:
        str: Resulting header.
    """
    return '%s%s%s%s%s%s' % (star_log['version'], star_log['previous_hash'], star_log['difficulty'], star_log['events_hash'], star_log['time'], star_log['nonce'] if include_nonce else '')


def concat_event(event_json):
    """Concats the information of an event from the provided json.

    Args:
        event_json (dict): Event to pull the information from.

    Returns:
        str: Resulting concatenated information of the event.
    """
    concat = '%s%s%s' % (event_json['fleet_hash'], event_json['fleet_key'], event_json['type'])
    if event_json['inputs']:
        for current_input in sorted(event_json['inputs'], key=lambda x: x['index']):
            concat += current_input['key']
    if event_json['outputs']:
        for current_output in sorted(event_json['outputs'], key=lambda x: x['index']):
            concat += '%s%s%s%s%s' % (current_output['type'], current_output['fleet_hash'], current_output['key'], current_output['star_system'], current_output['count'])
    return concat


def expand_rsa_public_key(shrunk_public_key):
    """Reformats a shrunk Rsa public key.

    Args:
        shrunk_public_key (str): Rsa public key without the BEGIN or END sections.
    
    Returns:
        str: The public key with its BEGIN and END sections reattatched.
    """
    return '-----BEGIN PUBLIC KEY-----\n%s\n-----END PUBLIC KEY-----'%(shrunk_public_key)


def rsa_sign(private_key, message):
    """Signs a message with the provided Rsa private key.

    Args:
        private_key (str): Rsa private key with BEGIN and END sections.
        message (str): Message to be hashed and signed.
    
    Returns:
        str: Hex signature of the message, with its leading 0x stripped.
    """
    private_rsa = load_pem_private_key(bytes(private_key), password=None, backend=default_backend())
    hashed = sha256(message)
    signature = private_rsa.sign(
        hashed,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return binascii.hexlify(bytearray(signature))


def hash_star_log(star_log):
    """Hashed value of the provided star log's header.

    Args:
        star_log (dict): Json data for the star log to be hashed.
    
    Returns:
        dict: Supplied star log with its `events_hash`, `log_header`, and `hash` fields calculated.
    """
    star_log['events_hash'] = hash_events(star_log['events'])
    star_log['log_header'] = concat_star_log_header(star_log)
    star_log['hash'] = sha256(star_log['log_header'])
    return star_log


def hash_events(events):
    """Hashed value of the provided events.

    Args:
        events (dict): Json data for the events to be hashed.

    Returns:
        str: Sha256 hash of the provided events.
    """
    concat = ''
    for event in events:
        concat += hash_event(event)
    return sha256(concat)


def hash_event(event):
    """Hashed value of the provided event.

    Args:
        event (dict): Json data for the event to be hashed.

    Returns:
        str: Sha256 hash of the provided event.
    """
    return sha256(concat_event(event))


def unpack_bits(difficulty, strip=False):
    """Unpacks int difficulty into a target hex.

    Args:
        difficulty (int): Packed int representation of a difficulty.
    
    Returns:
        str: Hex value of a target hash equal to this difficulty, stripped of its leading 0x.
    """
    if not isinstance(difficulty, (int, long)):
        raise TypeError('difficulty is not int')
    sha = difficulty_to_hex(difficulty)
    digit_count = int(sha[:2], 16)

    if digit_count == 0:
        digit_count = 3

    digits = []
    if digit_count == 29:
        digits = [sha[4:6], sha[6:8]]
    else:
        digits = [sha[2:4], sha[4:6], sha[6:8]]

    digit_count = min(digit_count, 28)
    significant_count = len(digits)

    leading_padding = 28 - digit_count
    trailing_padding = 28 - (leading_padding + significant_count)

    base256 = ''

    for i in range(0, leading_padding + 4):
        base256 += '00'
    for i in range(0, significant_count):
        base256 += digits[i]
    for i in range(0, trailing_padding):
        base256 += '00'

    if 0 < difficultyFudge():
        base256 = base256[difficultyFudge():] + base256[:difficultyFudge()]
    return base256.rstrip('0') if strip else base256


def get_fleets(events_json):
    """Gets all fleets with their keys.

    Args:
        events_json (dict): List of all events to check.
    
    Returns:
        list: A list of tuples with fleet hashes and their key.
    """
    results = []
    for current_event in events_json:
        fleet_hash = current_event['fleet_hash']
        fleet_key = current_event['fleet_key']
        if None in (fleet_hash, fleet_key):
            continue
        results.append((fleet_hash, fleet_key))
    return results


def get_event_inputs(events_json):
    """Gets all input events.

    Args:
        events_json (dict): List of all events to search.
    
    Returns:
        list: A list the input events.
    """
    results = []
    for current_event in events_json:
        for current_output in current_event['inputs']:
            results.append(current_output)
    return results


def get_event_outputs(events_json):
    """Gets all output events.

    Args:
        events_json (dict): List of all events to search.
    
    Returns:
        list: A list the output events.
    """
    results = []
    for current_event in events_json:
        for current_output in current_event['outputs']:
            results.append(current_output)
    return results


def get_event_type_id(event_name):
    """Gets the integer associated with the event type.

    Args:
        event_name (str): Name of the event.
    
    Returns:
        int: Integer of the event type.
    """
    for i in range(0, len(EVENT_TYPES)):
        if EVENT_TYPES[i] == event_name:
            return i
    return 0


def get_event_type_name(event_id):
    """Gets the str name associated with the event type.

    Args:
        event_id (int): Id of the event.
    
    Returns:
        str: Str of the event type.
    """
    return EVENT_TYPES[event_id] if event_id is not None and event_id < len(EVENT_TYPES) else EVENT_TYPES[0]


def get_jump_cost(origin_hash, destination_hash, count=None):
    """Gets the floating point scalar for the number of ships that will be lost in this jump.

    Args:
        origin_hash (str): The starting hash of the jump.
        destination_hash (str): The ending hash of the jump.
        count (int): The number of ships in the jump.
    
    Returns:
        float: A scalar value of the ships lost in the jump.
    """
    distance = get_distance(origin_hash, destination_hash)
    max_distance = jumpDistanceMaximum()
    cost_max = jumpCostMaximum()
    if max_distance <= distance:
        return cost_max if count is None else int(math.ceil(cost_max * count))
    # Scalar is x^2
    scalar = math.sqrt(distance / max_distance)
    cost_min = jumpCostMinimum()
    cost_range = 1.0 - ((1.0 - cost_max) + cost_min)
    scalar = cost_min + (cost_range * scalar)
    return scalar if count is None else int(math.ceil(scalar * count))


def get_cartesian_minimum():
    """Gets the (x, y, z) position of the minimum possible system.
    
    Returns:
        array: A list containing the (x, y, z) position.
    """
    return numpy.array([0, 0, 0])


def get_cartesian_maximum():
    """Gets the (x, y, z) position of the maximum possible system.
    
    Returns:
        array: A list containing the (x, y, z) position.
    """
    max_value = pow(16, cartesianDigits())
    return numpy.array([max_value, max_value, max_value])


def get_cartesian(system_hash):
    """Gets the (x, y, z) position of the specified system.

    Args:
        system_hash (str): The system's Sha256 hash.
    
    Returns:
        numpy.array: A list containing the (x, y, z) position.
    """
    cartesian_hash = sha256('%s%s' % ('cartesian', system_hash))
    digits = cartesianDigits()
    total_digits = digits * 3
    cartesian = cartesian_hash[-total_digits:]
    return numpy.array([int(cartesian[:digits], 16), int(cartesian[digits:-digits], 16), int(cartesian[(2*digits):], 16)])


def get_distance(origin_hash, destination_hash):
    """Gets the distance between the specified systems in cartesian space.

    Args:
        origin_hash (str): The origin system's Sha256 hash.
        destination_hash (str): The destination system's Sha256 hash.
    
    Returns:
        float: The distance between the two systems.
    """
    origin_pos = get_cartesian(origin_hash)
    destination_pos = get_cartesian(destination_hash)
    return int(math.ceil(numpy.linalg.norm(origin_pos - destination_pos)))


def get_unique_key():
    """The sha256 of a unique id.

    Returns:
        str: The sha256 of a unique id.
    """
    return sha256(str(uuid.uuid4()))


def get_fleet_hash_name(stripped_public_key, length=6):
    """Gets the human readable name for a fleet by hashing and shortening its stripped public key.

    Args:
        stripped_public_key (str): The fleet's public key after stripping.
        length (int): The length of the shortened name.
    
    Returns:
        str: The shortened name.
    """
    return get_fleet_name(sha256(stripped_public_key), length)


def get_fleet_name(fleet_hash, length=6):
    """Gets the human readable name for a fleet.

    Args:
        fleet_hash (str): The fleet's Sha256 hash.
        length (int): The length of the shortened name.
    
    Returns:
        str: The shortened name.
    """
    return '(%s)' % get_shortened_hash(fleet_hash, length, False)


def get_system_name(system_hash, length=6):
    """Gets the human readable name for a system.

    Args:
        system_hash (str): The system's Sha256 hash.
        length (int): The length of the shortened name.
    
    Returns:
        str: The shortened name.
    """
    return '[%s]' % get_shortened_hash(system_hash, length)


def get_shortened_hash(sha, length=6, strip_zeros=True):
    """Gets the human readable name for a hash.

    Args:
        sha (str): The Sha256 hash.
        length (int): The length of the shortened name.
    
    Returns:
        str: The shortened name.
    """
    if strip_zeros:
        sha = sha.lstrip('0')
    if len(sha) <= length:
        return sha
    else:
        return sha[:length]


def get_time():
    """UTC time in seconds.

    Returns:
        int: The number of seconds since the UTC epoch started.
    """
    return int(time.time())
