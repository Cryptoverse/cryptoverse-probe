from json import dumps as json_dump
from os import getenv, environ
from sys import stdout, platform
from traceback import print_exc as print_exception
from datetime import datetime
from time import sleep
from ete3 import Tree
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from getch import getch
from probe_exceptions import CommandException, ProbeTimeoutException
import requests
import database
import util
import validate
import parameter_util as putil
from blueprints import DEFAULT_HULL, DEFAULT_CARGO, DEFAULT_JUMP_DRIVE, DEFAULT_VESSEL

import matplotlib
matplotlib.use('TkAgg')

from mpl_toolkits.mplot3d import Axes3D # pylint: disable=unused-import
import matplotlib.colors as pycolors
import matplotlib.pyplot as pyplot

AUTO_REBUILD = int(getenv('AUTO_REBUILD', '0')) == 1

# HOST_URL = getenv('HOST_URL', 'http://localhost:5000')
HOST_URL = getenv('HOST_URL', 'http://api.cryptoverse.io')
RULES_URL = HOST_URL + '/rules'
CHAINS_URL = HOST_URL + '/chains'
STAR_LOGS_URL = HOST_URL + '/star-logs'
EVENTS_URL = HOST_URL + '/events'

DEFAULT_COLOR = '\033[0m'
SUCCESS_COLOR = '\033[92m'
ERROR_COLOR = '\033[91m'
BOLD_COLOR = '\033[1m'
CURSOR_ERASE_SEQUENCE = '\033[K'
CURSOR_FORWARD_SEQUENCE = '\033[%sC'


def get_genesis():
    return {
        'nonce': 0,
        'height': 0,
        'hash': util.EMPTY_TARGET,
        'difficulty': util.difficultyStart(),
        'events': [],
        'version': 0,
        'time': 0,
        'previous_hash': util.EMPTY_TARGET,
        'events_hash': None,
        'meta': None,
        'meta_hash': None
    }

def get_event_signature(fleet_hash=None, fleet_key=None, event_hash=None, inputs=None, outputs=None, signature=None, event_type=None):
    return {
        'fleet_hash': fleet_hash,
        'fleet_key': fleet_key,
        'hash': event_hash,
        'inputs': [] if inputs is None else inputs,
        'outputs': [] if outputs is None else outputs,
        'signature': signature,
        'type': event_type
    }

def get_event_input(index, key):
    return {
        'index': index,
        'key': key
    }


def get_event_output(index, model, model_type, fleet_hash, key, star_system, type_name):
    return {
        'index': index,
        'model': model,
        'model_type': model_type,
        'fleet_hash': fleet_hash,
        'key': key,
        'star_system': star_system,
        'type': type_name
    }


def generate_account(name='default'):
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    private_serialized = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_serialized = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_lines = public_serialized.splitlines()
    public_shrunk = ''
    for line in range(1, len(public_lines) - 1):
        public_shrunk += public_lines[line].strip('\n')
    
    return {
        'name': name,
        'private_key': private_serialized,
        'public_key': public_shrunk
    }


def pretty_json(serialized):
    return json_dump(serialized, sort_keys=True, indent=4, separators=(',', ': '))


def get_request(url, payload=None):
    try:
        return requests.get(url, payload).json()
    except:
        print_exception()
        print 'error on get request '+url


def post_request(url, payload=None):
    try:
        serialized = json_dump(payload)
        return requests.post(url, data=serialized, headers={'content-type': 'application/json', 'cache-control': 'no-cache', }).json()
    except:
        print_exception()
        print 'error on post request '+url


def create_command(function, description, details=None):
    return {
        'function': function,
        'description': description,
        'details': details
    }


def command_help(commands, params=None):
    help_message = '%sThis help message'
    exit_message = '%sEnds this process'
    if params:
        if 0 < len(params):
            queried_command_name = params[0]
            selection = commands.get(queried_command_name, None)
            if selection:
                print '%s' % selection['description']
                details = selection['details']
                if details:
                    for detail in selection['details']:
                        print '\t - %s' % detail
                return
            elif queried_command_name == 'help':
                print help_message % ''
                return
            elif queried_command_name == 'exit':
                print exit_message % ''
                return
            raise CommandException('Command "%s" is not recognized, try typing "help" for a list of all commands' % queried_command_name)

    print help_message % 'help\t - '
    for command in commands:
        print '%s\t - %s' % (command, commands[command]['description'])
    print exit_message % 'exit\t - '


def account(params=None):
    if putil.retrieve(params, '-a', True, False):
        account_all()
    elif putil.retrieve(params, '-s', True, False):
        account_set(putil.retrieve_value(params, '-s', None))
    elif putil.retrieve(params, '-c', True, False):
        account_create(putil.retrieve_value(params, '-c', None))
    else:
        result = database.get_account()
        if result:
            print 'Using account "%s"' % result['name']
            print '\tFleet Hash: %s' % util.get_fleet_hash_name(result['public_key'])
        else:
            print 'No active account'


def account_all():
    message = 'No account information found'
    accounts = database.get_accounts()
    if accounts:
        message = 'Persistent data contains the following account entries'
        entry_message = '\n%s\t- %s\n\t\tFleet Hash: %s'
        for currentAccount in accounts:
            active_flag = '[CURR] ' if currentAccount['active'] else ''
            message += entry_message % (active_flag, currentAccount['name'], util.get_fleet_hash_name(currentAccount['public_key']))
    print message


def account_set(name):
    if not name:
        raise CommandException('Account cannot be set to None')
    if not database.any_account(name):
        raise CommandException('Unable to find account %s' % name)
    database.set_account_active(name)
    print 'Current account is now "%s"' % name


def account_create(name):
    if not name:
        raise CommandException('Include a unique name for this account')
    elif database.any_account(name):
        raise CommandException('An account named "%s" already exists' % name)
    created_account = generate_account(name)
    database.add_account(created_account)
    database.set_account_active(name)
    print 'Created and activated account "%s"' % name


def info():
    print 'Connected to %s with fudge %s, interval %s, duration %s' % (HOST_URL, util.difficultyFudge(), util.difficultyInterval(), util.difficultyDuration())


def star_log(params=None):
    target_hash = None
    if putil.has_any(params):
        if putil.has_single(params):
            target_hash = putil.single_str(params)
    # TODO: Actually support target_hash.
    print pretty_json(get_request(STAR_LOGS_URL))


def probe(params=None):
    # TODO: Sync first...
    from_genesis = putil.retrieve(params, '-g', True, False)
    post = putil.retrieve(params, '-a', False, True)
    verbose = putil.retrieve(params, '-v', True, False)
    silent = putil.retrieve(params, '-s', True, False)
    allow_duplicate_events = putil.retrieve(params, '-d', True, False)
    from_query = putil.retrieve_value(params, '-f', None)
    loop = putil.retrieve(params, '-l', True, False)
    wait = float(putil.retrieve_value(params, '-w', 0.0))
    blind = putil.retrieve(params, '-b', True, False)
    if wait < 0:
        raise CommandException('Cannot use a wait less than zero seconds')
    from_hash = None
    if from_query is not None:
        from_hash = putil.natural_match(from_query, database.get_star_log_hashes())
        if from_hash is None:
            raise CommandException('Unable to find a system hash containing %s' % from_query)
    if not blind:
        sync('-s')
    generated = None
    started = datetime.now()
    while generated is None:
        try:
            generated = generate_next_star_log(from_hash, from_genesis, allow_duplicate_events, started)
        except ProbeTimeoutException:
            if not blind:
                sync('-s')
    if not silent:
        print 'Probed new starlog %s' % util.get_system_name(generated['hash'])
        if verbose:
            print pretty_json(generated)
    if not post:
        return
    try:
        result = post_request(STAR_LOGS_URL, generated)
        if result == 200:
            database.add_star_log(generated)
        if not silent:
            prefix, postfix = SUCCESS_COLOR if result == 200 else ERROR_COLOR, DEFAULT_COLOR
            print 'Posted starlog with response %s%s%s' % (prefix, result, postfix)
    except:
        print_exception()
        print 'Something went wrong when trying to post the generated starlog'
    if loop:
        if 0 < wait:
            sleep(wait)
        probe(params)


def generate_next_star_log(from_star_log=None, from_genesis=False, allow_duplicate_events=False, start_time=None, timeout=180):
    next_star_log = get_genesis()
    if from_star_log:
        next_star_log = database.get_star_log(from_star_log)
    elif not from_genesis:
        local_highest = database.get_star_log_highest()
        if local_highest is not None:
            next_star_log = local_highest
    is_genesis = util.is_genesis_star_log(next_star_log['hash'])
    account_info = database.get_account()
    next_star_log['events'] = []

    if not is_genesis:
        event_results = get_request(EVENTS_URL, {'limit': util.eventsMaxLimit()})
        if event_results:
            unused_events = []
            for unused_event in database.get_unused_events(from_star_log=next_star_log['hash']):
                unused_events.append(unused_event['key'])
            used_inputs = []
            used_outputs = []
            events = []
            for event in event_results:
                validate.event(event, require_index=False, require_star_system=True, reward_allowed=False)
                conflict = False
                current_used_inputs = []
                for current_input in event['inputs']:
                    conflict = current_input['key'] in used_inputs + current_used_inputs or current_input['key'] not in unused_events
                    if conflict:
                        break
                    current_used_inputs.append(current_input['key'])
                if conflict:
                    continue
                current_used_outputs = []
                for current_output in event['outputs']:
                    output_key = current_output['key']
                    conflict = output_key in used_inputs + used_outputs + current_used_inputs + current_used_outputs
                    if conflict:
                        break
                    current_used_outputs.append(output_key)
                if conflict:
                    continue
                if not allow_duplicate_events:
                    if database.any_events_used(current_used_inputs, next_star_log['hash']) or database.any_events_exist(current_used_outputs, next_star_log['hash']):
                        continue
                
                used_inputs += current_used_inputs
                used_outputs += current_used_outputs
                event['index'] = len(events)
                events.append(event)
            
            next_star_log['events'] += events

    reward_output = {
        'index': 0,
        'type': 'reward',
        'fleet_hash': util.sha256(account_info['public_key']),
        'key': util.get_unique_key(),
        'star_system': None,
        'model': DEFAULT_VESSEL,
        'model_type': 'vessel',
    }

    reward_event = {
        'index': len(next_star_log['events']),
        'hash': None,
        'type': 'reward',
        'fleet_hash': util.sha256(account_info['public_key']),
        'fleet_key': account_info['public_key'],
        'inputs': [],
        'outputs': [
            reward_output
        ],
        'signature': None
    }

    if not is_genesis:
        # TODO: This won't work correctly if there are multiple genesis blocks!
        # TODO: Change this to get from the local database
        first_star_log = get_request(CHAINS_URL, {'height': 0})
        # Until we have a way to select where to send your reward ships, just send them to the genesis block.
        reward_output['star_system'] = first_star_log[0]['hash']

    reward_event['hash'] = util.hash_event(reward_event)
    reward_event['signature'] = util.rsa_sign(account_info['private_key'], reward_event['hash'])

    meta = database.get_meta_content()
    next_star_log['meta'] = '' if meta is None else meta
    next_star_log['meta_hash'] = util.sha256(next_star_log['meta'])
    next_star_log['events'].append(reward_event)
    next_star_log['previous_hash'] = next_star_log['hash']
    next_star_log['time'] = util.get_time()
    next_star_log['nonce'] = 0
    next_star_log['events_hash'] = util.hash_events(next_star_log['events'])
    next_star_log['log_header'] = util.concat_star_log_header(next_star_log)
    next_star_log['height'] = 0 if is_genesis else next_star_log['height'] + 1

    if not is_genesis and util.is_difficulty_changing(next_star_log['height']):
        # We have to recalculate the difficulty at this height.
        previous_recalculation = database.get_star_log_at_height(next_star_log['previous_hash'], next_star_log['height'] - util.difficultyInterval())
        previous_star_log = database.get_star_log(next_star_log['previous_hash'])
        next_star_log['difficulty'] = util.calculate_difficulty(previous_recalculation['difficulty'], previous_star_log['time'] - previous_recalculation['time'])

    found = False
    tries = 0
    check_interval = 10000000
    next_check = check_interval
    curr_started = datetime.now()
    started = curr_started if start_time is None else start_time
    last_checkin = curr_started
    # This initial hash hangles the hashing of events and such.
    next_star_log = util.hash_star_log(next_star_log)
    current_difficulty = util.unpack_bits(next_star_log['difficulty'], True)
    current_difficulty_leading_zeros = len(current_difficulty) - len(current_difficulty.lstrip('0'))
    current_nonce = 0
    log_prefix = util.concat_star_log_header(next_star_log, False)
    current_hash = None

    while not found:
        current_hash = util.sha256('%s%s' % (log_prefix, current_nonce))
        try:
            validate.difficulty_unpacked(current_difficulty, current_difficulty_leading_zeros, current_hash, False)
            found = True
            break
        except:
            pass
        if tries == next_check:
            next_check = tries + check_interval
            now = datetime.now()
            if timeout < (now - curr_started).total_seconds():
                raise ProbeTimeoutException('Probing timed out')
            hashes_per_second = tries / (now - last_checkin).total_seconds()
            elapsed_minutes = (now - started).total_seconds() / 60
            print '\tProbing at %.0f hashes per second, %.1f minutes elapsed...' % (hashes_per_second, elapsed_minutes)
        current_nonce += 1
        if util.MAXIMUM_NONCE <= current_nonce:
            current_nonce = 0
            next_star_log['time'] = util.get_time()
            log_prefix = util.concat_star_log_header(next_star_log, False)
        tries += 1
    if found:
        next_star_log['nonce'] = current_nonce
        next_star_log['log_header'] = util.concat_star_log_header(next_star_log)
        next_star_log['hash'] = current_hash
    else:
        raise CommandException('Unable to probe a new starlog')
    return next_star_log


def sync(params=None):
    silent = putil.retrieve(params, '-s', True, False)
    if putil.retrieve(params, '-f', True, False):
        if not silent:
            print 'Removing all locally cached starlogs'
        database.initialize(True)

    latest = database.get_star_log_latest()
    latest_time = 0 if latest is None else latest['time']
    all_results = []
    last_count = util.starLogsMaxLimit()
    offset = 0
    while util.starLogsMaxLimit() == last_count:
        results = get_request(STAR_LOGS_URL, {'since_time': latest_time, 'limit': util.starLogsMaxLimit(), 'offset': offset})
        if results is None:
            last_count = 0
        else:
            last_count = len(results)
        offset += last_count
        all_results += results

    for result in all_results:
        database.add_star_log(result)

    if not silent:
        print 'Syncronized %s starlogs' % len(all_results)

    
def render_chain(params=None):
    # TODO: Fix bug that causes rendering to mess up after probing.
    limit = 6
    height = None
    # TODO: Actually get height from parameters.
    if putil.has_any(params):
        if putil.has_single(params):
            limit = putil.single_int(params)
        else:
            raise CommandException('Unsupported parameters')

    highest = database.get_star_log_highest()
    if highest is None:
        raise CommandException('No starlogs to render, try "sync"')
    height = highest['height'] if height is None else height
    results = database.get_star_logs_at_height(height, limit)
    strata = [(height, list(results))]
    remaining = limit - len(results)
    while 0 < height and remaining != 0:
        height -= 1
        ancestor_results = database.get_star_logs_at_height(height, remaining)
        current_results = []
        for ancestor in ancestor_results:
            has_children = False
            for result in results:
                has_children = result['previous_hash'] == ancestor['hash']
                if has_children:
                    break
            results.append(ancestor)
            if not has_children:
                current_results.append(ancestor)
        if current_results:
            strata.append((height, current_results))
            remaining = limit - len(current_results)
    
    tree = Tree()
    last_node = tree
    count = len(strata)
    for i in reversed(range(0, count)):
        stratum = strata[i]
        if i == 0:
            for orphan in stratum[1]:
                last_node.add_child(name=util.get_system_name(orphan['hash']))
        else:
            last_node = last_node.add_child()
            for orphan in stratum[1]:
                last_node.add_sister(name=util.get_system_name(orphan['hash']))
        
    print tree


def render_systems(params=None):
    figure = pyplot.figure()
    axes = figure.add_subplot(111, projection='3d')

    for currentSystem in database.get_star_log_hashes(from_highest=True):
        current_position = util.get_cartesian(currentSystem)
        xs = [current_position[0], current_position[0]]
        ys = [current_position[1], current_position[1]]
        zs = [0, current_position[2]]
        axes.plot(xs, ys, zs)
        axes.scatter(current_position[0], current_position[1], current_position[2], label=util.get_system_name(currentSystem))
    
    axes.legend()
    axes.set_title('Systems')
    axes.set_xlabel('X')
    axes.set_ylabel('Y')
    axes.set_zlabel('Z')

    pyplot.show()


def list_deployments(params=None):
    verbose = putil.retrieve(params, '-v', True, False)
    list_all = not putil.has_any(params) or putil.retrieve(params, '-a', True, False)
    from_hash = None
    if putil.retrieve(params, '-f', True, False):
        from_hash_query = putil.retrieve_value(params, '-f', None)
        if from_hash_query is None:
            raise CommandException('A system hash fragment must be passed with the -f parameter')
        from_hash = putil.natural_match(from_hash_query, database.get_star_log_hashes())
        if from_hash is None:
            raise CommandException('Unable to find a system hash containing %s' % from_hash_query)
    if list_all:
        list_all_deployments(from_hash, verbose)
        return
    hash_query = putil.single_str(params)
    selected_hash = putil.natural_match(hash_query, database.get_star_log_hashes())
    if selected_hash is None:
        raise CommandException('Unable to find a system hash containing %s' % hash_query)
    deployments = database.get_unused_events(from_star_log=from_hash, system_hash=selected_hash)
    if verbose:
        print pretty_json(deployments)
        return
    fleets = {}
    for deployment in deployments:
        fleet = deployment['fleet_hash']
        count = deployment['count']
        if fleet in fleets:
            fleets[fleet] += count
        else:
            fleets[fleet] = count
    result = 'No deployments in system %s' % util.get_system_name(selected_hash)
    if fleets:
        result = 'Deployments in star system %s' % util.get_system_name(selected_hash)
        fleet_keys = fleets.keys()
        for i in range(0, len(fleets)):
            current_fleet = fleet_keys[i]
            result += '\n - %s : %s' % (util.get_fleet_name(current_fleet), fleets[current_fleet])
        
    print result


def list_all_deployments(from_star_log, verbose):
    deployments = database.get_unused_events(from_star_log=from_star_log)
    if verbose:
        print pretty_json(deployments)
        return
    systems = {}
    for deployment in deployments:
        system = deployment['star_system']
        fleet = deployment['fleet_hash']
        if system in systems:
            current_system = systems[system]
        else:
            current_system = {}
            systems[system] = current_system
        
        active_jump_drives = 0
        broken_jump_drives = 0
        accessible_fuel = 0
        inaccessible_fuel = 0

        for module in deployment['model']['modules']:
            module_type = module['module_type']
            module_active = 0 < module['health']
            if module_type == 'jump_drive':
                if module_active:
                    active_jump_drives += 1
                else:
                    broken_jump_drives += 1
            elif module_type == 'cargo':
                contents = module['contents']
                if module_active:
                    accessible_fuel += contents.get('fuel', 0)
                else:
                    inaccessible_fuel += contents.get('fuel', 0)

        jump_status = 'No jump capability'
        fuel_status = 'with no fuel'

        if 0 < active_jump_drives:
            jump_status = 'Jump capable'
        elif 0 < broken_jump_drives:
            jump_status = 'Jump drive broken'
        
        if 0 < accessible_fuel:
            if 0 < inaccessible_fuel:
                fuel_status = 'with %s fuel accessible, and %s fuel in an inaccessible cargo tank' % (accessible_fuel, inaccessible_fuel)
            else:
                fuel_status = 'with %s fuel' % accessible_fuel
        elif 0 < inaccessible_fuel:
            fuel_status = 'with %s fuel in an inaccessible cargo tank' % inaccessible_fuel
        else:
            fuel_status = 'with no fuel'
        
        vessel_status = '%s %s %s' % (util.get_vessel_name(deployment['key']), jump_status, fuel_status)

        if fleet in current_system:
            current_system[fleet].append(vessel_status)
        else:
            current_system[fleet] = [ vessel_status ]
        
    result = 'No deployments in any systems'
    account_hash = util.sha256(database.get_account()['public_key'])
    if systems:
        result = 'Deployments in all systems'
        system_keys = systems.keys()
        for i in range(0, len(system_keys)):
            current_system = system_keys[i]
            result += '\n - %s' % util.get_system_name(current_system)
            fleet_keys = systems[current_system].keys()
            for fleet_key in range(0, len(fleet_keys)):
                current_fleet = fleet_keys[fleet_key]
                vessel_list = ''
                for current_vessel in systems[current_system][current_fleet]:
                    vessel_list += '\t\t%s\n' % current_vessel
                active_flag = '[CURR] ' if current_fleet == account_hash else ''
                result += '\n%s\t - %s\n%s' % (active_flag, util.get_fleet_name(current_fleet), vessel_list)
    print result
        
    
def attack(params=None):
    if not putil.has_at_least(params, 2):
        raise CommandException('An origin system and fleet must be specified')
    verbose = putil.retrieve(params, '-v', True, False)
    abort = putil.retrieve(params, '-a', True, False)
    origin_fragment = params[0]
    enemy_fragment = params[1]
    origin_hash = putil.natural_match(origin_fragment, database.get_star_log_hashes())
    if origin_hash is None:
        raise CommandException('Unable to find an origin system containing %s' % origin_fragment)
    highest_hash = database.get_star_log_highest(origin_hash)['hash']
    enemy_hash = putil.natural_match(enemy_fragment, database.get_fleets(highest_hash))
    if enemy_hash is None:
        raise CommandException('Unable to find a fleet containing %s' % enemy_fragment)
    enemy_deployments = database.get_unused_events(highest_hash, origin_hash, enemy_hash)
    if enemy_deployments is None:
        raise CommandException('Fleet %s has no ships deployed in %s' % (util.get_fleet_name(enemy_hash), util.get_system_name(origin_hash)))
    account_info = database.get_account()
    friendly_hash = util.sha256(account_info['public_key'])
    friendly_deployments = database.get_unused_events(highest_hash, origin_hash, friendly_hash)
    friendly_count = 0
    for friendly_deployment in friendly_deployments:
        friendly_count += friendly_deployment['count']
    if friendly_count == 0:
        raise CommandException('None of your fleet is deployed to %s' % util.get_system_name(origin_hash))
    
    # TODO: Break this out into its own get call.
    attack_event = {
        'fleet_hash': friendly_hash,
        'fleet_key': account_info['public_key'],
        'hash': None,
        'inputs': [],
        'outputs': [],
        'signature': None,
        'type': 'attack'
    }

    input_index = 0
    enemy_count = 0
    for enemy_deployment in enemy_deployments:
        attack_event['inputs'].append(get_event_input(input_index, enemy_deployment['key']))
        enemy_count += enemy_deployment['count']
        input_index += 1
        if friendly_count <= enemy_count:
            break
    friendly_count = 0
    for friendly_deployment in friendly_deployments:
        attack_event['inputs'].append(get_event_input(input_index, friendly_deployment['key']))
        friendly_count += friendly_deployment['count']
        input_index += 1
        if enemy_count <= friendly_count:
            break
    if enemy_count < friendly_count:
        attack_event['outputs'].append(get_event_output(0, friendly_count - enemy_count, friendly_hash, util.get_unique_key(), origin_hash, 'attack'))
    elif friendly_count < enemy_count:
        attack_event['outputs'].append(get_event_output(0, enemy_count - friendly_count, enemy_hash, util.get_unique_key(), origin_hash, 'attack'))
    
    attack_event['hash'] = util.hash_event(attack_event)
    attack_event['signature'] = util.rsa_sign(account_info['private_key'], attack_event['hash'])

    if verbose:
        print pretty_json(attack_event)
    if not abort:
        result = post_request(EVENTS_URL, attack_event)
        prefix, postfix = SUCCESS_COLOR if result == 200 else ERROR_COLOR, DEFAULT_COLOR
        print 'Posted attack event with response %s%s%s' % (prefix, result, postfix)


def jump(params=None):
    verbose = putil.retrieve(params, '-v', True, False)
    render = putil.retrieve(params, '-r', True, False)
    abort = putil.retrieve(params, '-a', True, False)
    # lossy = putil.retrieve(params, '-l', True, False)
    # TODO: Add actual support for non-lossy jumps.
    lossy = True
    count = None
    if not putil.has_any(params):
        raise CommandException('Specify a vessel and a destination system')
    if len(params) < 2:
        raise CommandException('A vessel and a destination system must be specified')
    vessel_fragment = params[0]
    destination_fragment = params[1]
    account_info = database.get_account()
    fleet_hash = util.sha256(account_info['public_key'])
    deployments = database.get_unused_events(fleet_hash=fleet_hash, model_type='vessel')
    vessel_key = putil.natural_match(vessel_fragment, [x['key'] for x in deployments])
    if vessel_key is None:
        raise CommandException('Unable to find a vessel key containing %s belonging to your fleet' % vessel_fragment)
    vessel_event = [x for x in deployments if x['key'] == vessel_key][0]
    vessel = vessel_event['model']
    found_jump_drive = False
    for jump_module in [x for x in vessel['modules'] if x['module_type'] == 'jump_drive']:
        found_jump_drive = 0 < jump_module['health']
        if found_jump_drive:
            jump_module['delta'] = not jump_module['delta']
            break
    
    if not found_jump_drive:
        raise CommandException('Vessel has no working jump drives')
    
    hashes = database.get_star_log_hashes()
    destination_hash = putil.natural_match(destination_fragment, hashes)
    if destination_hash is None:
        raise CommandException('Unable to find a destination system containing %s' % destination_fragment)
    origin_hash = vessel_event['star_system']
    accessible_fuel = util.get_vessel_resources(vessel)['fuel']
    jump_cost = util.get_jump_cost(origin_hash, destination_hash)
    if jump_cost == -1 or accessible_fuel <= jump_cost:
        raise CommandException('Not enough fuel to complete jump')
    
    jump_event = get_event_signature(fleet_hash, account_info['public_key'], event_type='jump')

    inputs = [ get_event_input(0, vessel_event['key']) ]

    jump_key = util.sha256('%s%s%s%s' % (util.get_time(), fleet_hash, origin_hash, destination_hash))
    vessel, remainder = util.subtract_vessel_resources(vessel, { 'fuel': jump_cost })
    outputs = [ get_event_output(0, vessel, 'vessel', fleet_hash, jump_key, destination_hash, 'jump') ]

    jump_event['inputs'] = inputs
    jump_event['outputs'] = outputs
    jump_event['hash'] = util.hash_event(jump_event)
    jump_event['signature'] = util.rsa_sign(account_info['private_key'], jump_event['hash'])

    if verbose:
        print pretty_json(jump_event)
    if render:
        render_jump(origin_hash, destination_hash)
    if not abort:
        result = post_request(EVENTS_URL, jump_event)
        prefix, postfix = SUCCESS_COLOR if result == 200 else ERROR_COLOR, DEFAULT_COLOR
        print 'Posted jump event with response %s%s%s' % (prefix, result, postfix)


def render_jump(origin_hash, destination_hash):
    highest = database.get_star_log_highest_from_list([origin_hash, destination_hash])
    
    figure = pyplot.figure()
    axes = figure.add_subplot(111, projection='3d')

    for current_system in database.get_star_log_hashes(highest):
        current_position = util.get_cartesian(current_system)
        xs = [current_position[0], current_position[0]]
        ys = [current_position[1], current_position[1]]
        zs = [0, current_position[2]]
        axes.plot(xs, ys, zs)
        axes.scatter(current_position[0], current_position[1], current_position[2], label=util.get_system_name(current_system))
    origin_position = util.get_cartesian(origin_hash)
    destination_position = util.get_cartesian(destination_hash)
    xs = [origin_position[0], destination_position[0]]
    ys = [origin_position[1], destination_position[1]]
    zs = [origin_position[2], destination_position[2]]
    axes.plot(xs, ys, zs, linestyle=':')
    
    axes.legend()
    axes.set_title('Jump %s -> %s' % (util.get_system_name(origin_hash), util.get_system_name(destination_hash)))
    axes.set_xlabel('X')
    axes.set_ylabel('Y')
    axes.set_zlabel('Z')

    pyplot.show()


def render_jump_range(params=None):
    if not putil.has_any(params):
        raise CommandException('Specify an origin system to render the jump range from')
    origin_fragment = putil.single_str(params)
    destination_fragment = putil.retrieve_value(params, '-d', None)

    hashes = database.get_star_log_hashes()
    origin_hash = putil.natural_match(origin_fragment, hashes)
    if origin_hash is None:
        raise CommandException('Unable to find an origin system containing %s' % origin_fragment)
    destination_hash = None
    highest = None
    if destination_fragment is not None:
        destination_hash = putil.natural_match(destination_fragment, hashes)
        if destination_hash is None:
            raise CommandException('Unable to find a destination system containing %s' % destination_fragment)
        if not database.get_star_logs_share_chain([origin_hash, destination_hash]):
            raise CommandException('Systems %s and %s exist on different chains' % (util.get_system_name(origin_hash), util.get_system_name(destination_hash)))
        highest = database.get_star_log_highest(database.get_star_log_highest_from_list([origin_hash, destination_hash]))['hash']
    
    figure = pyplot.figure()
    axes = figure.add_subplot(111, projection='3d')
    hue_start = 0.327
    hue_end = 0.0
    hue_delta = hue_end - hue_start
    for current_system in database.get_star_log_hashes(highest):
        cost = util.get_jump_cost(origin_hash, current_system)
        cost_hue = hue_start + (cost * hue_delta)
        cost_value = 0.0 if cost == 1.0 else 1.0
        color = pycolors.hsv_to_rgb([cost_hue, 0.7, cost_value])
        current_position = util.get_cartesian(current_system)
        xs = [current_position[0], current_position[0]]
        ys = [current_position[1], current_position[1]]
        zs = [0, current_position[2]]
        axes.plot(xs, ys, zs, c=color)
        marker = '^' if current_system == origin_hash else 'o'
        axes.scatter(current_position[0], current_position[1], current_position[2], label=util.get_system_name(current_system), c=color, marker=marker)
    if destination_hash is not None:
        origin_position = util.get_cartesian(origin_hash)
        destination_position = util.get_cartesian(destination_hash)
        xs = [origin_position[0], destination_position[0]]
        ys = [origin_position[1], destination_position[1]]
        zs = [origin_position[2], destination_position[2]]
        axes.plot(xs, ys, zs, linestyle=':')
    
    axes.legend()
    axes.set_title('Jump Range %s' % util.get_system_name(origin_hash))
    axes.set_xlabel('X')
    axes.set_ylabel('Y')
    axes.set_zlabel('Z')
    
    pyplot.show()


def system_position(params=None):
    if not putil.has_single(params):
        raise CommandException('An origin system must be specified')
    origin_fragment = putil.single_str(params)
    origin_hash = putil.natural_match(origin_fragment, database.get_star_log_hashes())
    if origin_hash is None:
        raise CommandException('Unable to find an origin system containing %s' % origin_fragment)
    print '%s system is at %s' % (util.get_system_name(origin_hash), util.get_cartesian(origin_hash))


def system_distance(params=None):
    if not putil.has_count(params, 2):
        raise CommandException('An origin and destination system must be specified')
    origin_fragment = params[0]
    destination_fragment = params[1]
    hashes = database.get_star_log_hashes()
    origin_hash = putil.natural_match(origin_fragment, hashes)
    if origin_hash is None:
        raise CommandException('Unable to find an origin system containing %s' % origin_fragment)
    destination_hash = putil.natural_match(destination_fragment, hashes)
    if destination_hash is None:
        raise CommandException('Unable to find a destination system containing %s' % destination_fragment)
    if not database.get_star_logs_share_chain([origin_hash, destination_hash]):
        raise CommandException('Systems %s and %s exist on different chains' % (util.get_system_name(origin_hash), util.get_system_name(destination_hash)))
    print 'Distance between %s and %s is %s' % (util.get_system_name(origin_hash), util.get_system_name(destination_hash), util.get_distance(origin_hash, destination_hash))


def system_average_distances(params=None):
    origin_hash = None
    if putil.has_single(params):
        origin_fragment = params[0]
        origin_hash = putil.natural_match(origin_fragment, database.get_star_log_hashes())
        if origin_hash is None:
            raise CommandException('Unable to find an origin system containing %s' % origin_fragment)
    total = 0
    count = 0
    if origin_hash:
        for currentHash in database.get_star_log_hashes(origin_hash):
            if currentHash == origin_hash:
                continue
            total += util.get_distance(currentHash, origin_hash)
            count += 1
    else:
        hashes = database.get_star_log_hashes(from_highest=True)
        for currentHash in hashes:
            hashes = hashes[1:]
            for targetHash in hashes:
                total += util.get_distance(currentHash, targetHash)
                count += 1
    if count == 0:
        print 'No systems to get the average distances of'
    else:
        average = total / count
        if origin_hash is None:
            print 'Average distance between all systems is %s' % average
        else:
            print 'Average distance to system %s is %s' % (util.get_system_name(origin_hash), average)


def system_maximum_distance(params=None):
    system_min_max_distance(params)


def system_minimum_distance(params=None):
    system_min_max_distance(params, False)


def system_min_max_distance(params=None, calculating_max=True):
    modifier = 'Farthest' if calculating_max else 'Nearest'
    origin_hash = None
    if putil.has_single(params):
        origin_fragment = params[0]
        origin_hash = putil.natural_match(origin_fragment, database.get_star_log_hashes())
        if origin_hash is None:
            raise CommandException('Unable to find an origin system containing %s' % origin_fragment)
    if origin_hash:
        best_system = None
        best_distance = 0 if calculating_max else 999999999
        for current_hash in database.get_star_log_hashes(origin_hash):
            if current_hash == origin_hash:
                continue
            dist = util.get_distance(origin_hash, current_hash)
            if (calculating_max and best_distance < dist) or (not calculating_max and dist < best_distance):
                best_system = current_hash
                best_distance = dist
        print '%s system from %s is %s, with a distance of %s' % (modifier, util.get_system_name(origin_hash), util.get_system_name(best_system), best_distance)
    else:
        hashes = database.get_star_log_hashes(from_highest=True)
        best_system_origin = None
        best_system_destination = None
        best_distance = 0 if calculating_max else 999999999
        for current_hash in hashes:
            hashes = hashes[1:]
            for targetHash in hashes:
                dist = util.get_system_name(current_hash, targetHash)
                if (calculating_max and best_distance < dist) or (not calculating_max and dist < best_distance):
                    best_system_origin = current_hash
                    best_system_destination = targetHash
                    best_distance = dist
        print '%s systems are %s and %s, with a distance of %s' % (modifier, util.get_system_name(best_system_origin), util.get_system_name(best_system_destination), best_distance)


def transfer(params=None):
    verbose = putil.retrieve(params, '-v', True, False)
    abort = putil.retrieve(params, '-a', True, False)
    if not putil.has_any(params):
        raise CommandException('Another fleet hash must be specified')
    to_fleet = putil.single_str(params)
    try:
        validate.field_is_sha256(to_fleet)
    except:
        raise CommandException('A complete fleet hash must be specified')
    count = None
    if putil.has_at_least(params, 2):
        count = int(params[1])
        if count <= 0:
            raise CommandException('A valid number of ships must be specified')
    account_info = database.get_account()
    from_fleet = util.sha256(account_info['public_key'])
    events = database.get_unused_events(fleet_hash=from_fleet)
    if events is None:
        raise CommandException('No ships are available to be transferred for fleet %s' % util.get_fleet_name(from_fleet))
    total_count = 0
    for event in events:
        total_count += event['count']
    if count is None:
        count = total_count
    elif total_count < count:
        raise CommandException('Only %s are available to transfer' % total_count)
    transfer_event = get_event_signature(from_fleet, account_info['public_key'], event_type='transfer')
    remaining_count = count
    overflow_count = 0
    input_index = 0
    output_index = 0
    while 0 < remaining_count:
        curr_input = events[input_index]
        count_delta = curr_input['count']
        if remaining_count < count_delta:
            count_delta = count_delta - remaining_count
        transfer_event['inputs'].append(get_event_input(input_index, curr_input['key']))
        existing_output = [x for x in transfer_event['outputs'] if x['fleet_hash'] == to_fleet and x['star_system'] == curr_input['star_system']]
        if existing_output:
            # Add to existing output
            existing_output = existing_output[0]
            existing_output['count'] += count_delta
        else:
            transfer_event['outputs'].append(get_event_output(output_index, count_delta, to_fleet, util.get_unique_key(), curr_input['star_system'], 'transfer'))
            output_index += 1
        
        if count_delta != curr_input['count']:
            # Leftover ships that need to be assigned back to the owner.
            input_index += 1
            transfer_event['outputs'].append(get_event_output(input_index, curr_input['count'] - count_delta, from_fleet, util.get_unique_key(), curr_input['star_system'], 'transfer'))
            remaining_count = 0
        else:
            remaining_count -= curr_input['count']
        input_index += 1
    transfer_event['hash'] = util.hash_event(transfer_event)
    transfer_event['signature'] = util.rsa_sign(account_info['private_key'], transfer_event['hash'])
    
    if verbose:
        print pretty_json(transfer_event)
    if not abort:
        result = post_request(EVENTS_URL, transfer_event)
        prefix, postfix = SUCCESS_COLOR if result == 200 else ERROR_COLOR, DEFAULT_COLOR
        print 'Posted transfer event with response %s%s%s' % (prefix, result, postfix)


def meta_content(params=None):
    if not putil.has_any(params):
        current_content = database.get_meta_content()
        if current_content is None:
            print 'No meta content set, use meta -s <content> to set one'
        else:
            print 'Meta content is "%s"' % current_content
        return
    
    if putil.retrieve(params, '-r', True, False):
        database.set_meta_content(None)
        print 'Meta content has been reset'
        return
    
    new_content = putil.retrieve_value(params, '-s', None)
    if putil.retrieve(params, '-s', True, False):
        if new_content is None:
            raise CommandException('Specify a new meta content, if you want to specify none use the -r flag instead')
    else:
        raise CommandException('An unrecognized parameter was passed')
    database.set_meta_content(new_content)
    print 'Meta content set to "%s"' % new_content


def poll_input():
    if platform.startswith('win'):
        return_sequence = [13]
        up_sequence = [224, 72]
        down_sequence = [224, 80]
        left_sequence = [224, 75]
        right_sequence = [224, 77]
        back_sequence = [8]
        control_c_sequence = [3]
        tab_sequence = [9]
        double_escape_sequence = [27, 27]
    else:
        return_sequence = [13]
        up_sequence = [27, 91, 65]
        down_sequence = [27, 91, 66]
        left_sequence = [27, 91, 68]
        right_sequence = [27, 91, 67]
        back_sequence = [127]
        control_c_sequence = [3]
        tab_sequence = [9]
        double_escape_sequence = [27, 27]

    special_sequences = [
        tab_sequence,
        return_sequence,
        up_sequence,
        down_sequence,
        left_sequence,
        right_sequence,
        back_sequence,
        control_c_sequence,
        double_escape_sequence
    ]
    alpha_numeric_range = range(32, 127)
    chars = []
    while True:
        is_special = chars in special_sequences
        if is_special:
            break
        char = ord(getch())
        chars.append(char)
        if len(chars) == 1 and char in alpha_numeric_range:
            break
        elif 1 < len(chars):
            last_chars = chars[-2:]
            if last_chars == double_escape_sequence:
                chars = last_chars
                is_special = True
                break
    
    alpha_numeric = ''
    is_return = False
    is_backspace = False
    is_control_c = False
    is_up = False
    is_down = False
    is_left = False
    is_right = False
    is_tab = False
    is_double_escape = False

    if is_special:
        if chars == return_sequence:
            is_return = True
        elif chars == back_sequence:
            is_backspace = True
        elif chars == control_c_sequence:
            is_control_c = True
        elif chars == up_sequence:
            is_up = True
        elif chars == down_sequence:
            is_down = True
        elif chars == left_sequence:
            is_left = True
        elif chars == right_sequence:
            is_right = True
        elif chars == tab_sequence:
            is_tab = True
        elif chars == double_escape_sequence:
            is_double_escape = True
        else:
            print 'Unrecognized special sequence %s' % chars
    elif len(chars) == 1:
        alpha_numeric = chr(chars[0])
    else:
        print 'Unrecognized alphanumeric sequence %s' % chars
    
    return alpha_numeric, is_return, is_backspace, is_control_c, is_up, is_down, is_left, is_right, is_tab, is_double_escape


def main():
    print 'Starting probe...'
    rules = get_request(RULES_URL)
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

    print 'Connected to %s\n\t - Fudge: %s\n\t - Interval: %s\n\t - Duration: %s\n\t - Starting Difficulty: %s\n\t - Ship Reward: %s' % (HOST_URL, util.difficultyFudge(), util.difficultyInterval(), util.difficultyDuration(), util.difficultyStart(), util.shipReward())
    min_x, min_y, min_z = util.get_cartesian_minimum()
    max_x, max_y, max_z = util.get_cartesian_maximum()
    universe_size = '( %s, %s, %s ) - ( %s, %s, %s )' % (min_x, min_y, min_z, max_x, max_y, max_z)
    print '\t - Universe Size: %s\n\t - Jump Cost: %s%% to %s%%\n\t - Jump Distance Max: %s' % (universe_size, util.jumpCostMinimum() * 100, util.jumpCostMaximum() * 100, util.jumpDistanceMaximum())
    if AUTO_REBUILD:
        print 'Automatically rebuilding database...'

    database.initialize(AUTO_REBUILD)

    sync()

    if not database.get_accounts():
        print 'Unable to find existing accounts, creating default...'
        default_account = generate_account()
        database.add_account(default_account)
        database.set_account_active(default_account['name'])
    elif database.get_account() is None:
        print 'No active account, try "help account" for more information on selecting an active account'

    all_commands = {
        'info': create_command(
            info, 
            'Displays information about the connected server'
        ),
        'sync': create_command(
            sync,
            'Syncs the local cache with updates from the server',
            [
                '"-f" replaces the local cache with fresh results',
                '"-s" silently executes the command'
            ]
        ),
        'slog': create_command(
            star_log,
            'Retrieves the latest starlog'
        ),
        'probe': create_command(
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
        'meta': create_command(
            meta_content,
            'Retrieves or sets the meta content included in probed starlogs',
            [
                'Passing no arguments retrieves the current meta content being included with probed starlogs',
                '"-s" sets a new meta content',
                '"-r" resets the meta content to nothing' 
            ]
        ),
        'account': create_command(
            account,
            'Information about the current account',
            [
                'Passing no arguments gets the current account information',
                '"-a" lists all accounts stored in persistent data',
                '"-s" followed by an account name changes the current account to the specified one',
                '"-c" followed by an account name creates a new account'
            ]
        ),
        'rchain': create_command(
            render_chain,
            'Render starlog chain information to the command line',
            [
                'Passing no arguments renders the highest chains and their siblings',
                'Passing an integer greater than zero renders that many chains'
            ]
        ),
        'rsys': create_command(
            render_systems,
            'Render systems in an external plotter'
        ),
        'ldeploy': create_command(
            list_deployments,
            'List deployments in the specified system',
            [
                'Passing a partial hash will list deployments in the best matching system',
                '"-a" lists all systems with deployments',
                '"-f" looks for deployments on the chain with the matching head'
            ]
        ),
        'attack': create_command(
            attack,
            'Attack fleets in the specified system',
            [
                'Passing a partial origin and enemy fleet hash will attack the best matching fleet',
                '"-v" prints the attack to the console',
                '"-a" aborts without posting attack to the server'
            ]
        ),
        'jump': create_command(
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
        'transfer': create_command(
            transfer,
            'Transfer ships from one fleet to another',
            [
                'Passing a complete fleet hash will transfer all ships to that fleet',
                'Passing a complete fleet hash and a valid number of ships will transfer that number of ships to that fleet',
                '"-v" prints the transfer to the console',
                '"-a" aborts without posting transfer to the server'
            ]
        ),
        'jrange': create_command(
            render_jump_range,
            'Renders the range of jumps in an external plotter',
            [
                'Passing partial origin hash will render with that system in focus',
                '"-d" followed by a destination hash will render a line between the best matching system and the origin'
            ]
        ),
        'pos': create_command(
            system_position,
            'Calculates the coordinates of the specified system',
            [
                'Passing a partial hash will calculate the coordinate of the best matching system'
            ]
        ),
        'dist': create_command(
            system_distance,
            'Calculates the distance between the specified systems',
            [
                'Passing a partial origin and destination hash will calculate the distance between the best matching systems'
            ]
        ),
        'avgdist': create_command(
            system_average_distances,
            'Calculates the average distance between all systems',
            [
                'Passing no arguments will calculate the average distance between every system',
                'Passing a partial origin will calculate the average distance to the best matching system'
            ]
        ),
        'maxdist': create_command(
            system_maximum_distance,
            'Calculates the maximum distance between all systems',
            [
                'Passing no arguments will calculate the maximum distance between every system',
                'Passing a partial origin will calculate the maximum distance to the best matching system'
            ]
        ),
        'mindist': create_command(
            system_minimum_distance,
            'Calculates the minimum distance between all systems',
            [
                'Passing no arguments will calculate the minimum distance between every system',
                'Passing a partial origin will calculate the minimum distance to the best matching system'
            ]
        )
    }
    
    command_prefix = '> '
    command = None
    command_index = 0
    command_history = -1
    command_in_session = 0
    while True:
        
        if command is None:
            command = ''
            stdout.write('\r%s%s%s' % (command_prefix, command, CURSOR_ERASE_SEQUENCE))
            stdout.write('\r%s' % (CURSOR_FORWARD_SEQUENCE % (command_index + len(command_prefix))))

        alpha_numeric, is_return, is_backspace, is_control_c, is_up, is_down, is_left, is_right, is_tab, is_double_escape = poll_input()
        old_command_index = command_index
        old_command = command
        
        if is_backspace:
            if 0 < command_index:
                if len(command) == command_index:
                    # We're at the end of the string
                    command = command[:-1]
                else:
                    # We're in the middle of a string
                    command = command[:command_index - 1] + command[command_index:]
                command_index -= 1
        elif is_control_c:
            break
        elif is_up:
            command_history = min(command_history + 1, database.count_commands() - 1)
            command = database.get_command(command_history)
            command_index = 0 if command is None else len(command)
        elif is_down:
            command_history = max(command_history - 1, -1)
            if command_history < 0:
                command = ''
            else:
                command = database.get_command(command_history)
            command_index = 0 if command is None else len(command)
        elif is_left:
            if 0 < command_index:
                command_index -= 1
        elif is_right:
            if command_index < len(command):
                command_index += 1
        elif alpha_numeric:
            if len(command) == command_index:
                command += alpha_numeric
            else:
                command = command[:command_index] + alpha_numeric + command[command_index:]
            command_index += 1

        if old_command != command:
            stdout.write('\r%s%s%s%s%s' % (command_prefix, BOLD_COLOR, command, DEFAULT_COLOR, CURSOR_ERASE_SEQUENCE))
        if old_command_index != command_index:
            stdout.write('\r%s' % (CURSOR_FORWARD_SEQUENCE % (command_index + len(command_prefix))))

        if is_return or is_double_escape:
            stdout.write('\n')
        if is_double_escape:
            command = None
            command_index = 0
            command_history = -1
            continue
        if not is_return:
            continue

        try:
            if not command:
                print 'Type help for more commands'
                continue
            args = command.split(' ')
            command_name = args[0]
            command_args = args[1:]
            selected_command = all_commands.get(command_name, None)
            if not selected_command:
                if command_name == 'help':
                    command_help(all_commands, command_args)
                elif command_name == 'exit':
                    break
                else:
                    print 'No command "%s" found, try typing help for more commands' % command
            else:
                if not command_args:
                    selected_command['function']()
                else:
                    selected_command['function'](command_args)
        except CommandException as exception:
            print exception
        except:
            print_exception()
            print 'Error with your last command'
        database.add_command(command, util.get_time(), command_in_session)
        command = None
        command_index = 0
        command_history = -1
        command_in_session += 1

if __name__ == '__main__':
    main()
    stdout.write('\nExiting...\n')
