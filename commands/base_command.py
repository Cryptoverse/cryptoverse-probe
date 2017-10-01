from traceback import print_exc

class BaseCommand(object):

    def __init__(self, app, name, **kwargs):
        self.app = app
        self.name = name
        self.description = kwargs.get('description', 'No description provided')
        self.parameter_usages = kwargs.get('parameter_usages', [])
        self.command_handlers = kwargs.get('command_handlers', [])

        self.app.callbacks.enter_command += self.on_enter_command

    def on_enter_command(self, command, *args):
        if command == self.name:
            has_stack_arg = '--stack' in args
            if has_stack_arg: 
                args = [arg for arg in args if arg != '--stack']
            try:
                self.on_command(*args)
            except NotImplementedError:
                message = 'Command "%s" is not implemented'
                if has_stack_arg:
                    print_exc()
                else:
                    message += ', include "--stack" for more information'
                self.app.callbacks.on_error(message % self.name)
            except:
                print_exc()
                self.app.callbacks.on_error('Command "%s" raised an exception' % self.name)

    def on_command(self, *args):
        if self.command_handlers is None or len(self.command_handlers) == 0:
            raise NotImplementedError
        
        parameter_count = len(args)
        if parameter_count == 0:
            handler = next((h for h in self.command_handlers if (h[0] is None and h[2] == 0)), None)
            if handler is None:
                self.app.callbacks.on_error('Command "%s" does not have a parameterless functionality' % self.name)
                return
            handler[1]()
            return
        handler = next((h for h in self.command_handlers if (h[0] == args[0] and h[2] == (parameter_count - 1))), None)
        if handler is None:
            self.app.callbacks.on_error('Command "%s" does not have a parameter "%s" that takes %s options' % (self.name, args[0], parameter_count - 1))
            return
        handler[1](*args[1:])

    def get_handler(self, name, handler, parameter_count=0):
        return (name, handler, parameter_count)