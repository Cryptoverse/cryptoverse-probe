from traceback import print_exc

class BaseCommand(object):

    def __init__(self, app, name, **kwargs):
        self.app = app
        self.name = name
        self.description = kwargs.get('description', 'No description provided')
        self.parameter_usages = kwargs.get('parameter_usages', [])

        self.app.callbacks.enter_command += self.on_enter_command

    def on_enter_command(self, command, *args):
        if command == self.name:
            try:
                self.on_command(*args)
            except NotImplementedError:
                message = 'Command "%s" is not implemented'
                if '--stack' in args:
                    print_exc()
                else:
                    message += ', include "--stack" for more information'
                self.app.callbacks.on_error(message % self.name)
            except:
                print_exc()
                self.app.callbacks.on_error('Command "%s" raised an exception' % self.name)

    def on_command(self, *args):
        raise NotImplementedError