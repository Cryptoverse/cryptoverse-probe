class BaseCommand(object):

    def __init__(self, app, name, **kwargs):
        self.app = app
        self.name = name
        self.description = kwargs.get('description', 'No description provided')
        self.parameter_usage = kwargs.get('paramater_usage', set())


    def get_help(self):
        return 'todo: this'


    # def on_command(self, *args):
    #     pass