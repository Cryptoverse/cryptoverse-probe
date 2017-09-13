from callback_result import CallbackResult

# TODO: Figure out if we need this, I think we will for versioned APIs.
class BaseRemote(object):

    def __init__(self, app):
        self.app = app
        self.on_initialized = None

    def initialize(self, done):
        if done is None:
            raise TypeError('"done" cannot be None')
        self.on_initialized = done
        self.app.database.find_recent_nodes(self.on_recent_nodes)

    def on_recent_nodes(self, result):
        if result.is_error:
            self.on_initialized(result)
            return
        if result.content is None:
            self.on_initialized(CallbackResult('Unable to syncronize, no recent nodes'))
            return
        self.on_initialized(CallbackResult('todo: lololol'))
    
    def get_rules(self, node, done):
        raise NotImplementedError