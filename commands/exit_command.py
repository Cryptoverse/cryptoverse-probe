from commands.base_command import BaseCommand

class ExitCommand(BaseCommand):

    def __init__(self, app):
        super(ExitCommand, self).__init__(app, 'exit')

    def on_command(self, *args):
        self.app.exit()