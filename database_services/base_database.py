from callback_result import CallbackResult

class BaseDatabase(object):

    def __init__(self, app, **kwargs):
        self.app = app
        
        self.command_history = kwargs.get('command_history')
        self.account = kwargs.get('account')
        self.meta = kwargs.get('meta')
        self.node = kwargs.get('node')
        self.rules = kwargs.get('rules')
        self.block = kwargs.get('block')
        self.block_data = kwargs.get('block_data')

        self.database_handlers = [
            self.command_history,
            self.account,
            self.meta,
            self.node,
            self.rules,
            self.block,
            self.block_data
        ]

        self.uninitialized_handlers = self.database_handlers
        self.on_initialized = None
        self.rebuild = False

    def initialize(self, done, rebuild=False):
        self.rebuild = rebuild
        if done is None:
            raise TypeError('"done" cannot be None')
        self.on_initialized = done
        if self.database_handlers is None:
            self.on_initialized(CallbackResult('No database handlers', False))
            return
        self.on_handler_initialized()

    def on_handler_initialized(self, result=None):
        if result is not None and result.is_error:
            self.on_initialized(result)
            return
        if not self.uninitialized_handlers:
            self.on_initialized(CallbackResult('All handlers initialized'))
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