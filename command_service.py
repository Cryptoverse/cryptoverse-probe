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
        for current_command in ALL_COMMANDS:
            self.commands.append(current_command(app))


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
            current_cursor = -1

        if poll_result.is_return or poll_result.is_double_escape:
            current_output = '\n'
            current_cursor = -1
        if poll_result.is_double_escape:
            self.command = None
            self.command_index = 0
            self.command_history = -1
            return
    
        if current_output != None or current_cursor != None:
            self.app.callbacks.on_output(current_output, current_cursor)
        if poll_result.is_return:
            # TODO: Is command run???
            pass

    def register_command(self, command):
        if any(c.name == command.name for c in self.commands):
            raise Exception('A command definition for %s already exists' % command.name)
        self.commands.add(command)

    
    # Database functionality...
    def get_command(self, index):
        return 'Not impl'

    def count_commands(self):
        return 0