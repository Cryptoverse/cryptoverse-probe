from base_command import BaseCommand

class HelpCommand(BaseCommand):

    def __init__(self, app):
        super(HelpCommand, self).__init__(app, 'help')

    def on_command(self, *args):
        print 'todo: this'
