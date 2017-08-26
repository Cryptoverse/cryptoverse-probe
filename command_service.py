from commands import ALL_COMMANDS

class CommandService(object):
    
    def __init__(self, app):
        self.app = app
        self.command = None
        self.command_index = 0
        self.command_history = -1
        self.command_in_session = 0

        self.app.callbacks.input += self.on_input

        self.commands = []
        self.command_names = []
        for current_command in ALL_COMMANDS:
            command_instance = current_command(app)
            self.commands.append(command_instance)
            self.command_names.append(command_instance.name)


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
            self.command = self.get_command(self.command_history)
            self.command_index = 0 if self.command is None else len(self.command)
        elif poll_result.is_down:
            self.command_history = max(self.command_history - 1, -1)
            if self.command_history < 0:
                self.command = ''
            else:
                self.command = self.get_command(self.command_history)
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

            self.add_command(self.command)
            
            if command_name in self.command_names:
                self.app.callbacks.on_enter_command(command_name, command_parameters)
            else:
                self.app.callbacks.on_undefined_command(command_name, command_parameters)
                self.app.callbacks.on_output('Command "%s" not found, try typing "help" to see all commands' % command_name)
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

    # Database functionality...
    def get_command(self, index):
        return 'Not impl'

    def add_command(self, command):
        # TODO: Add command to history, if not already in it
        pass

    def count_commands(self):
        return 0