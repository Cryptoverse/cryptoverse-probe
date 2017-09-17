from datetime import datetime
from commands.base_command import BaseCommand
from sync_command import SyncCommand
from callback_result import CallbackResult
from models.block_model import BlockModel
from models.event_model import EventModel
from models.event_output_model import EventOutputModel
from models.event_outputs.vessel_model import VesselModel
from models.fleet_model import FleetModel
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
            def on_get_account(get_account_result):
                if get_account_result.is_error:
                    self.app.callbacks.on_error(get_account_result.content)
                    return
                if get_account_result.content is None:
                    self.app.callbacks.on_error('No active account')
                    return
                self.create_block(get_account_result.content, None)
            self.app.database.account.find_account_active(on_get_account)
            

            # generated = None
            # started = datetime.now()
            # while generated is None:
            #     pass
                # try:
                #     generated = generate_next_star_log(from_hash, from_genesis, allow_duplicate_events, started)
                # except ProbeTimeoutException:
                #     if not blind:
                #         sync('-s')
        self.app.commands.get_command(SyncCommand.COMMAND_NAME).synchronize(on_sync)

    def create_block(self, account, block_hash):
        def on_find_block(find_block_result):
            if find_block_result.is_error:
                self.app.callbacks.on_error(find_block_result.content)
                return
            self.get_events(account, find_block_result.content)

        if block_hash is None:
            # If genesis...
            block = BlockModel()

            block.hash = util.EMPTY_TARGET
            block.nonce = 0
            block.previous_hash = util.EMPTY_TARGET
            block.height = 0
            block.difficulty = util.difficultyStart()
            block.time = util.get_time()
            block.events = []

            on_find_block(CallbackResult(block))
        else:
            raise NotImplementedError

    def get_meta(self, account, block):
        def on_get_meta(get_meta_result):
            if get_meta_result.is_error:
                self.app.callbacks.on_error(get_meta_result.context)
                return
            block.meta = get_meta_result.content
            self.get_events(account, block)
        self.app.database.meta.find_meta(on_get_meta)

    def get_events(self, account, block):
        reward_event = EventModel()
        reward_event.index = 0
        reward_event.fleet = account.get_fleet()
        # TODO: Enumify this somewhere...
        reward_event.event_type = 'reward'
        reward_event.inputs = []
        reward_event.outputs = []

        reward_output = EventOutputModel()
        reward_output.index = 0
        reward_output.fleet = account.get_fleet()
        # TODO: Enumify this somewhere...
        reward_output.output_type = 'reward'
        reward_output.key = util.get_unique_key()
        reward_output.model = self.app.blueprints.get_default_vessel()

        reward_event.outputs.append(reward_output)
        reward_event.generate_signature(account.private_key)
        
        block.events.append(reward_event)

        if block.is_genesis():
            self.generate_hash(block)
            return
        
        def on_find_node(find_node_result):
            if find_node_result.is_error:
                self.app.callbacks.on_error(find_node_result.content)
                return
            if find_node_result.content is None:
                self.app.callbacks.on_error('No node available')
                return
            def on_get_events(get_events_result):
                if get_events_result.is_error:
                    self.app.callbacks.on_error(get_events_result.content)
                    return
                self.filter_events(account, block, get_events_result.content)
            self.app.remote.get_events(find_node_result.content, on_get_events)
            
        self.app.database.node.find_recent_node(on_find_node)

    def filter_events(self, account, block, events):
        raise NotImplementedError

    def generate_hash(self, block):
        raise NotImplementedError

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


'''
    def get_genesis(self):
        # TODO: Turn this into a model
        return {
            'hash': util.EMPTY_TARGET,
            'nonce': 0,
            'previous_hash': util.EMPTY_TARGET,
            'height': 0,
            'version': 0,
            'difficulty': util.difficultyStart(),
            'time': 0,
            'events': [],
            'events_hash': None,
            'meta': None,
            'meta_hash': None
        }


'''