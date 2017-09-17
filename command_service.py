from commands import ALL_COMMANDS
from callback_result import CallbackResult
from models.command_history_model import CommandHistoryModel
from util import get_time

class CommandService(object):
    
    def __init__(self, app):
        self.app = app
        self.command = None
        self.command_index = 0
        self.command_history = -1
        self.command_in_session = 0
        self.command_count = 0
        self.command_last = None

        self.app.callbacks.input += self.on_input

        self.commands = []
        self.command_names = []
        for current_command in ALL_COMMANDS:
            command_instance = current_command(app)
            self.commands.append(command_instance)
            self.command_names.append(command_instance.name)

    # Initialization Begin

    def initialize(self, done):
        self.initialize_last_command(done)

    def initialize_last_command(self, done):
        def on_result(result):
            if result.is_error:
                done(result)
            else:
                self.command_last = result.content.command if result.content else None
                self.initialize_command_count(done)
        self.app.database.find_command_history(0, on_result)

    def initialize_command_count(self, done):
        def on_result(result):
            if result.is_error:
                done(result)
            else:
                self.command_count = result.content
                done(CallbackResult())
        self.app.database.count(CommandHistoryModel, on_result)
        
    # Initialization End

    def on_input(self, poll_result):

        current_output = None
        current_cursor = None

        if self.command is None:
            self.command = ''
            current_output = ''
            current_cursor = -1
        
        old_command_index = self.command_index
        old_command = self.command

        if poll_result.is_backspace:
            if 0 < self.command_index:
                if len(self.command) == self.command_index:
                    # We're at the end of the string
                    self.command = self.command[:-1]
                else:
                    # We're in the middle of a string
                    self.command = self.command[:self.command_index - 1] + self.command[self.command_index:]
                self.command_index -= 1
        elif poll_result.is_control_c:
            return
        elif poll_result.is_up:
            self.command_history = min(self.command_history + 1, self.count_commands() - 1)
            self.set_from_history(self.command_history)
            self.command_index = 0 if self.command is None else len(self.command)
        elif poll_result.is_down:
            self.command_history = max(self.command_history - 1, -1)
            if self.command_history < 0:
                self.command = ''
            else:
                self.set_from_history(self.command_history)
            self.command_index = 0 if self.command is None else len(self.command)
        elif poll_result.is_left:
            if 0 < self.command_index:
                self.command_index -= 1
        elif poll_result.is_right:
            if self.command_index < len(self.command):
                self.command_index += 1
        elif poll_result.alpha_numeric:
            if len(self.command) == self.command_index:
                self.command += poll_result.alpha_numeric
            else:
                self.command = self.command[:self.command_index] + poll_result.alpha_numeric + self.command[self.command_index:]
            self.command_index += 1

        if old_command != self.command:
            current_output = self.command
        if old_command_index != self.command_index:
            current_cursor = self.command_index

        if poll_result.is_double_escape:
            self.reset_command()
            return
    
        if poll_result.is_return:
            # Run command
            
            command_name, command_parameters = self.explode_command(self.command)
            
            if command_name is None:
                return

            if self.command != self.command_last:
                self.add_to_history(self.command)
            
            if command_name in self.command_names:
                self.app.callbacks.on_enter_command(command_name, *command_parameters)
            else:
                self.app.callbacks.on_undefined_command(command_name, *command_parameters)
                self.app.callbacks.on_error('Command "%s" not found, try typing "help" to see all commands' % command_name)
            self.reset_command()
        elif current_output != None or current_cursor != None:
            self.app.callbacks.on_prompt_output(current_output, current_cursor)

    def register_command(self, command):
        if any(c.name == command.name for c in self.commands):
            raise Exception('A command definition for %s already exists' % command.name)
        self.commands.add(command)

    def reset_command(self):
        self.command = None
        self.command_index = 0
        self.command_history = -1

    def explode_command(self, command):
        if self.command == '':
            return (None, None)
        
        elements = command.split()
        name = elements[0]
        parameters = []
        if 1 < len(elements):
            for current_parameter in elements[1:]:
                parameters.append(current_parameter)
        return (name, parameters)

    def get_command(self, name):
        try:
            return next(command for command in self.commands if command.name == name)
        except StopIteration:
            print 'Command "%s" cannot be found' % name
            raise

    def set_from_history(self, index):
        self.app.database.find_command_history(index, self.on_set_from_history)

    def on_set_from_history(self, result):
        if result.is_error:
            raise Exception(result.content)
        self.command = result.content.command if result.content else None

    def add_to_history(self, command):
        entry = CommandHistoryModel()
        entry.command = command
        entry.time = get_time()
        entry.session_order = self.command_in_session
        self.command_in_session += 1
        self.command_last = command
        self.app.database.write(entry)

    def count_commands(self):
        self.app.database.count(CommandHistoryModel, self.on_count_commands)
        return self.command_count

    def on_count_commands(self, result):
        if result.is_error:
            raise Exception(result.content)
        self.command_count = result.content