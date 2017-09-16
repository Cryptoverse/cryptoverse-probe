from datetime import datetime
from commands.base_command import BaseCommand
from sync_command import SyncCommand
import util

class ProbeCommand(BaseCommand):

    COMMAND_NAME = 'probe'

    def __init__(self, app):
        super(ProbeCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'Probes for a new block and posts the results to recent nodes',
            parameter_usages = [
                'None: probes for a new block ontop of the highest block in the chain'
            ],
            command_handlers = [
                self.get_handler(None, self.on_probe)
            ]
        )

    def on_probe(self):
        def on_sync(sync_result):
            if sync_result.is_error:
                self.app.callbacks.on_error(sync_result.content)
                return
            generated = None
            started = datetime.now()
            while generated is None:
                pass
                # try:
                #     generated = generate_next_star_log(from_hash, from_genesis, allow_duplicate_events, started)
                # except ProbeTimeoutException:
                #     if not blind:
                #         sync('-s')
        self.app.commands.get_command(SyncCommand.COMMAND_NAME).synchronize(on_sync)

    def get_genesis(self):
        # TODO: Turn this into a model
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

    def generate_events(self, account, from_block):
        event_results = get_request(EVENTS_URL, {'limit': util.eventsMaxLimit()})
        def on_get_events(get_events_result):
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

'''
    # def generate_next_star_log(self, from_star_log=None, from_genesis=False, allow_duplicate_events=False, start_time=None, timeout=180):
    def generate_next_star_log(self, account, from_block, start_time=None, timeout=180):
        next_star_log = from_block
        is_genesis = util.is_genesis_star_log(next_star_log['hash'])
        account_info = account
        next_star_log['events'] = []

        if not is_genesis:
            

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
    '''