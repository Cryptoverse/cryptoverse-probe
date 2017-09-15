from commands.base_command import BaseCommand

class ProbeCommand(BaseCommand):

    def __init__(self, app):
        super(ProbeCommand, self).__init__(
            app, 
            'probe',
            description = 'Probes for a new block and posts the results to recent nodes',
            parameter_usages = [
                'None: probes for a new block ontop of the highest block in the chain'
            ],
            command_handlers = [
                self.get_handler(None, self.on_probe)
            ]
        )

    def on_probe(self):
        raise NotImplementedError