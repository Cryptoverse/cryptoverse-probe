from commands.base_command import BaseCommand
from sync_command import SyncCommand

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
            
        self.app.commands.get_command(SyncCommand.COMMAND_NAME).synchronize(on_sync)