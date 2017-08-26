from commands.base_command import BaseCommand

class InfoCommand(BaseCommand):

    def __init__(self, app):
        super(InfoCommand, self).__init__(app, 'info')

    # def on_command(self, *args):
    #     pass
