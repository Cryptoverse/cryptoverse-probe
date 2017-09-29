from json import dumps as json_dump
from datetime import datetime
from commands.base_command import BaseCommand
from commands.sync_command import SyncCommand
from callback_result import CallbackResult
from models.block_model import BlockModel
from models.event_model import EventModel
from models.event_output_model import EventOutputModel
from models.block_data_model import BlockDataModel
from probe_exceptions import ProbeTimeoutException
import util

class ProbeCommand(BaseCommand):

    COMMAND_NAME = 'probe'

    def __init__(self, app):
        super(ProbeCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'Probes for a new block and posts the results to recent nodes',
            parameter_usages = [
                'None: probes for a new block ontop of the highest block in the chain',
                '"-g" to create a new genesis block',
                '"-p <hash fragment>" to build off of the parent block with the closest matching hash'
            ],
            command_handlers = [
                self.get_handler(None, self.on_probe),
                self.get_handler('-g', self.on_probe_genesis),
                self.get_handler('-p', self.on_probe_hash, 1)
            ]
        )

    # Commands

    def on_probe_genesis(self):
        self.on_probe(is_genesis=True)


    def on_probe_hash(self, block_hash_fragment):
        if block_hash_fragment is None or block_hash_fragment == '':
            self.app.callbacks.on_error('A hash must be specified to build off of')
            return
        def on_find_block_by_hash_fragment(find_block_by_hash_fragment_result):
            if find_block_by_hash_fragment_result.is_error:
                self.app.callbacks.on_error(find_block_by_hash_fragment_result.content)
                return
            self.on_probe(find_block_by_hash_fragment_result.content.hash)
        self.app.database.block.find_block_by_hash_fragment(block_hash_fragment, on_find_block_by_hash_fragment)


    def on_probe(self, block_hash=None, is_genesis=False):
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
                self.get_rules(get_account_result.content, block_hash, is_genesis)
            self.app.database.account.find_account_active(on_get_account)
        self.app.commands.get_command(SyncCommand.COMMAND_NAME).synchronize(on_sync)

    # Shared

    def check_chain(self, done, block):
        def on_find_highest_block_on_chain(highest_block_on_chain_result):
            # If there's an error, it means the chain doesn't even exist, which is fine.
            if not highest_block_on_chain_result.is_error:
                highest_block = highest_block_on_chain_result.content
                if block.height <= highest_block.height:
                    # A chain is branching.
                    block.chain = util.get_unique_key()
                    block.root_id = block.previous_id
            done(CallbackResult(block))
        self.app.database.block.find_highest_block_on_chain(block.chain, on_find_highest_block_on_chain)

    def cache_block(self, done, block):
        def on_check_unique(check_unique_result):
            if not check_unique_result.is_error:
                done(CallbackResult(block))
                return
            # Block and data needs to be cached.
            def on_write_block(write_block_result):
                if write_block_result.is_error:
                    done(write_block_result)
                    return
                block = write_block_result.content
                def on_write_block_data(write_block_data_result):
                    if write_block_data_result.is_error:
                        done(write_block_data_result)
                        return
                    done(CallbackResult(block))
                block_data = BlockDataModel()
                block_data.block_id = block.id
                block_data.previous_block_id = block.previous_id
                block_data.uri = 'data_json' # Not really used at the moment, will eventually lead to a path on disk
                block_data.data = json_dump(block.get_json())
                self.app.database.block_data.write(block_data, on_write_block_data)
            self.app.database.block.write(block, on_write_block)
        self.app.database.block.find_block_by_hash(block.hash, on_check_unique)

    def post_to_nodes(self, done, block):
        def on_recent_nodes(recent_nodes_result):
            if recent_nodes_result.is_error:
                self.app.callbacks.on_error(recent_nodes_result.content)
                return
            self.on_post_to_nodes(done, block, recent_nodes_result.content)
        self.app.database.node.find_recent_nodes(on_recent_nodes)


    def on_post_to_nodes(self, done, block, nodes, node_successes=None):
        if node_successes is None:
            node_successes = []
        
        if len(nodes) == 0:
            done(CallbackResult(len(node_successes)))
            return

        current_node = nodes[0]
        nodes = nodes[1:]

        def on_post(post_result):
            if not post_result.is_error:
                node_successes.append(current_node)
            self.on_post_to_nodes(done, block, nodes, node_successes)
        self.app.remote.post_block(current_node, block, on_post)

    # Probe

    def get_rules(self, account, block_hash, is_genesis):
        def on_find_rules(find_rules_result):
            if find_rules_result.is_error:
                self.app.callbacks.on_error(find_rules_result.content)
                return
            if find_rules_result.content is None:
                self.app.callbacks.on_error('No rules have been set, unable to probe')
                return
            self.create_block(find_rules_result.content, account, block_hash, is_genesis)
        self.app.database.rules.find_rules(on_find_rules)


    def create_block(self, rules, account, block_hash=None, is_genesis=False):
        block = BlockModel()
        block.hash = rules.empty_target
        block.nonce = 0
        block.previous_hash = rules.empty_target
        block.height = 0
        block.difficulty = rules.difficulty_start
        block.time = util.get_time()
        block.events = []
        block.version = rules.version
        block.chain = util.get_unique_key()
        if is_genesis:
            # If genesis...
            self.get_meta(rules, account, block)
        elif block_hash is None:
            # Find highest block, or create a new genesis block.
            def on_find_highest_block(find_highest_block_result):
                if find_highest_block_result.is_error:
                    # Must be a genesis block
                    self.get_meta(rules, account, block)
                    return
                self.create_block_from_previous(rules, account, block, find_highest_block_result.content)
            self.app.database.block.find_highest_block(on_find_highest_block)
        else:
            def on_find_block(find_block_result):
                if find_block_result.is_error:
                    self.app.callbacks.on_error(find_block_result.content)
                    return
                self.create_block_from_previous(rules, account, block, find_block_result.content)
            self.app.database.block.find_block_by_hash(block_hash, on_find_block)


    def create_block_from_previous(self, rules, account, block, previous_block):
        if previous_block is None:
            self.app.callbacks.on_error('Cannot probe ontop of a None block')
            return
        block.height = previous_block.height + 1
        block.interval_id = previous_block.id if previous_block.interval_id is None else previous_block.interval_id
        block.root_id = previous_block.id if previous_block.root_id is None else previous_block.root_id
        block.chain = previous_block.chain
        block.difficulty = previous_block.difficulty
        block.previous_id = previous_block.id
        block.previous_hash = previous_block.hash
        self.check_difficulty(rules, account, block)


    def check_difficulty(self, rules, account, block):
        if not rules.is_difficulty_changing(block.height):
            self.get_meta(rules, account, block)
            return
        # Difficulty is changing...
        if block.interval_id is None:
            self.app.callbacks.on_error('Unable to recalculate difficulty, interval_id is None')
            return
        def on_find_interval_block(find_interval_block_result):
            if find_interval_block_result.is_error:
                self.app.callbacks.on_error(find_interval_block_result.content)
                return
            interval_block = find_interval_block_result.content
            difficulty_duration = block.time - interval_block.time
            block.interval_id = None
            block.difficulty = rules.calculate_difficulty(block.difficulty, difficulty_duration)
            self.get_meta(rules, account, block)
        self.app.database.block.find_block_by_id(block.interval_id, on_find_interval_block)


    def get_meta(self, rules, account, block):
        def on_find_meta(find_meta_result):
            block.meta = None if find_meta_result.is_error else find_meta_result.content.text_content
            self.get_events(rules, account, block)
        self.app.database.meta.find_meta(on_find_meta)


    def get_events(self, rules, account, block):
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

        if block.is_genesis(rules):
            self.generate_hash(rules, block)
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
                self.filter_events(rules, account, block, get_events_result.content)
            self.app.remote.get_events(find_node_result.content, on_get_events)
            
        self.app.database.node.find_recent_node(on_find_node)


    def filter_events(self, rules, account, block, events):
        if len(events) == 0:
            self.generate_hash(rules, block)
            return
        # TODO: Actually filter events...
        raise NotImplementedError


    def generate_hash(self, rules, block):

        # TODO: Figure out where timout should be set...
        timeout = 180

        found = False
        tries = 0
        check_interval = 10000000
        next_check = check_interval
        curr_started = datetime.now()
        started = curr_started
        last_checkin = curr_started
        # This initial hash hangles the hashing of events and such.
        current_difficulty = block.get_difficulty_target(rules.difficulty_fudge, True)
        current_difficulty_leading_zeros = len(current_difficulty) - len(current_difficulty.lstrip('0'))
        current_nonce = 0
        log_prefix = block.get_concat(False)

        while not found:
            block.assign_hash(current_nonce, log_prefix)
            found = block.is_valid(rules.difficulty_fudge, current_difficulty, current_difficulty_leading_zeros)
            if found:
                break
            
            if tries == next_check:
                next_check = tries + check_interval
                now = datetime.now()
                if timeout < (now - curr_started).total_seconds():
                    raise ProbeTimeoutException('Probing timed out')
                hashes_per_second = tries / (now - last_checkin).total_seconds()
                elapsed_minutes = (now - started).total_seconds() / 60
                print '\tProbing at %.0f hashes per second, %.1f minutes elapsed...' % (hashes_per_second, elapsed_minutes)
            current_nonce += 1
            if rules.maximum_nonce <= current_nonce:
                current_nonce = 0
                block.time = util.get_time()
                log_prefix = block.get_concat(False)
            tries += 1
        if found:
            def on_check_chain(check_chain_result):
                if check_chain_result.is_error:
                    self.app.callbacks.on_error(check_chain_result.content)
                    return
                def on_post_to_nodes(post_to_nodes_result):
                    if post_to_nodes_result.is_error:
                        self.app.callbacks.on_error(post_to_nodes_result.content)
                        return
                    self.on_done_probing(post_to_nodes_result.content)
                self.post_to_nodes(on_post_to_nodes, block)
            self.cache_block(on_check_chain, block)
        else:
            self.app.callbacks.on_error('Unable to probe a new starlog')

    def on_done_probing(self, success_count):
        # TODO: call output, instead of just printing...
        self.app.callbacks.on_output('posted successfully to %s nodes' % success_count)
