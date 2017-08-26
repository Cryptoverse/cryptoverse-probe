class BaseDatabase(object):

    def __init__(self, app):
        self.app = app

    def initialize(self, done):
        raise NotImplementedError

    # General functionality

    def create(self, model_type, done):
        raise NotImplementedError

    def drop(self, model, done):
        raise NotImplementedError

    def read(self, model_type, model_id, done):
        raise NotImplementedError

    def read_all(self, model_type, ids, done):
        raise NotImplementedError

    def write(self, model, done):
        raise NotImplementedError

    def sync(self, model, done):
        raise NotImplementedError

    def count(self, model_type, done):
        raise NotImplementedError

    # Optimizable functionality

    def find_command_history(self, index, done):
        raise NotImplementedError

    def find_account(self, name, done):
        raise NotImplementedError

    def find_block_latest(self, done):
        raise NotImplementedError

    def find_block_children(self, block_hash, done):
        raise NotImplementedError

    def find_block_highest(self, done, block_hash=None):
        raise NotImplementedError

    def find_block_highest_on_list(self, hashes, done):
        raise NotImplementedError

    def find_block(self, block_hash, done):
        raise NotImplementedError
    
    def find_block_at_height(self, block_hash, height, done):
        raise NotImplementedError

    def find_blocks_at_height(self, height, limit, done):
        raise NotImplementedError

    def find_block_hashes(self, done, block_hash=None, from_highest=False):
        raise NotImplementedError

    def find_blocks_share_chain(self, block_hashes, done):
        raise NotImplementedError

    def find_unused_events(self, done, from_block_hash=None, from_system=None, from_fleet=None)
        raise NotImplementedError

    def find_fleets(self, from_block_hash, done):
        raise NotImplementedError

    def any_events_exist(self, events, done, from_block_hash=None):
        raise NotImplementedError

    def any_events_used(self, events, done, from_block_hash=None):
        raise NotImplementedError
    
