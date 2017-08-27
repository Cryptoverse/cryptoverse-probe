from database_services.database_result import DatabaseResult

class BaseDatabase(object):

    def __init__(self, app, database_handlers):
        self.app = app
        self.database_handlers = database_handlers
        self.uninitialized_handlers = database_handlers
        self.on_initialized = None
        self.rebuild = False

    def initialize(self, done, rebuild=False):
        self.rebuild = rebuild
        if done is None:
            raise TypeError('"done" cannot be None')
        self.on_initialized = done
        if self.database_handlers is None:
            self.on_initialized(DatabaseResult('No database handlers', False))
            return
        self.on_handler_initialized()

    def on_handler_initialized(self, result=None):
        if result is not None and result.is_error:
            self.on_initialized(result)
            return
        if not self.uninitialized_handlers:
            self.on_initialized(DatabaseResult('All handlers initialized'))
            return
        current = self.uninitialized_handlers[0]
        self.uninitialized_handlers = self.uninitialized_handlers[1:]
        current.initialize(self.on_handler_initialized, self.rebuild)

    # General functionality

    def get_handler(self, model_type):
        handler = next(handler for handler in self.database_handlers if handler.model_type == model_type)
        if not handler:
            raise Exception('Database handler for model type "%s" not found' % model_type)
        return handler

    def write(self, model, done=None):
        self.get_handler(type(model)).write(model, done)

    def read(self, model_type, model_id, done):
        self.get_handler(model_type).read(model_id, done)

    def read_all(self, model_type, model_ids, done):
        self.get_handler(model_type).read_all(model_ids, done)

    def drop(self, model, done):
        self.get_handler(type(model)).drop(model, done)

    def sync(self, model, done):
        self.get_handler(type(model)).sync(model, done)

    def count(self, model_type, done):
        self.get_handler(model_type).count(done)

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

    def find_unused_events(self, done, from_block_hash=None, from_system=None, from_fleet=None):
        raise NotImplementedError

    def find_fleets(self, from_block_hash, done):
        raise NotImplementedError

    def any_events_exist(self, events, done, from_block_hash=None):
        raise NotImplementedError

    def any_events_used(self, events, done, from_block_hash=None):
        raise NotImplementedError
