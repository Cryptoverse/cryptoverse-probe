from base_command import BaseCommand

class HelpCommand(BaseCommand):

    def __init__(self, app):
        super(HelpCommand, self).__init__(app, 'help', command = self.on_command)

    def on_command(self, *args):
        self.app.callbacks.on_output('todo: this help')
