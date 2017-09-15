from commands.base_command import BaseCommand

class ExitCommand(BaseCommand):

    COMMAND_NAME = 'exit'

    def __init__(self, app):
        super(ExitCommand, self).__init__(app, self.COMMAND_NAME)

    def on_command(self, *args):
        self.app.exit()
