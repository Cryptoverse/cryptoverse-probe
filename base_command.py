class BaseCommand(object):

    def __init__(self, app, name, **kwargs):
        self.app = app
        self.name = name
        self.description = kwargs.get('description', 'No description provided')
        self.parameter_usage = kwargs.get('paramater_usage', set())
        self.command = kwargs.get('command', self.on_missing_command)

        self.app.callbacks.enter_command += self.on_enter_command

    def get_help(self):
        return 'todo: this'

    def on_enter_command(self, *args):
        if self.name == args[0]:
            self.command(args)

    def on_missing_command(self, *args):
        self.app.callbacks.on_output('Command "%s" is not implemented' % self.name)