from base_command import BaseCommand

class ExitCommand(BaseCommand):

    def __init__(self, app):
        super(ExitCommand, self).__init__(app, 'exit', command = self.on_command)

    def on_command(self, *args):
        self.app.exit()
