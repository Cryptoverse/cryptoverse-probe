from callback_result import CallbackResult
from commands.base_command import BaseCommand

class SyncCommand(BaseCommand):

    COMMAND_NAME = 'sync'

    def __init__(self, app):
        super(SyncCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'Synchronizes the local blockchain with new blocks from recent nodes',
            parameter_usages = [
                'None: synchronizes with all of the recent nodes'
            ],
            command_handlers = [
                self.get_handler(None, self.on_sync)
            ]
        )

    def on_sync(self):
        raise NotImplementedError

    def synchronize(self, done=None):
        # TODO: This should actually... do something...
        if done:
            done(CallbackResult())