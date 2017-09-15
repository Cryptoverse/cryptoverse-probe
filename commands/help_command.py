from commands.base_command import BaseCommand

class HelpCommand(BaseCommand):

    COMMAND_NAME = 'help'

    def __init__(self, app):
        super(HelpCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'This help message',
            parameter_usages = [
                'None: List all commands'
                '"help <command>" to retrieve command details'
            ]
        )

    def on_command(self, *args):
        parameter_count = len(args)

        if parameter_count == 0:
            self.help_all()
        elif parameter_count == 1:
            if args[0] in self.app.commands.command_names:
                self.help_specific(self.app.commands.get_command(args[0]))
            else:
                self.app.callbacks.on_error('Command "%s" not found, try typing "help" to see all commands' % args[0])
        else:
            self.app.callbacks.on_error('Command "help" does not accept more than one parameter')

    def help_all(self):
        message = 'Type "help <command>" to find out more'
        message += '\n======================================='
        for current_command in self.app.commands.commands:
            message += ('\n%s\t- %s' % (current_command.name, current_command.description))
        message += '\n======================================='
        self.app.callbacks.on_output(message)

    def help_specific(self, command):
        message = '[%s] %s' % (command.name, command.description)
        for parameter in command.parameter_usages:
            message += '\n\t- %s' % parameter
        self.app.callbacks.on_output(message)