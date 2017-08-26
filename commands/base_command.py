class BaseCommand(object):

    def __init__(self, app, name, **kwargs):
        self.app = app
        self.name = name
        self.description = kwargs.get('description', 'No description provided')
        self.parameter_usages = kwargs.get('parameter_usages', [])

        self.app.callbacks.enter_command += self.on_enter_command

    def get_help(self):
        return 'todo: this'

    def on_enter_command(self, command, *args):
        if command == self.name:
            self.on_command(*args)

    def on_command(self, *args):
        self.app.callbacks.on_output('Command "%s" is not implemented' % self.name)