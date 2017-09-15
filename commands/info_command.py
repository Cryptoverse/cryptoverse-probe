from commands.base_command import BaseCommand

class InfoCommand(BaseCommand):

    COMMAND_NAME = 'info'

    def __init__(self, app):
        super(InfoCommand, self).__init__(app, self.COMMAND_NAME)

    # def on_command(self, *args):
    #     pass
