from sys import stdout, platform
from prompt_services.base_prompt import BasePrompt

class TerminalPrompt(BasePrompt):

    COMMAND_PREFIX = '> '
    DEFAULT_COLOR = '\033[0m'
    SUCCESS_COLOR = '\033[92m'
    ERROR_COLOR = '\033[91m'
    BOLD_COLOR = '\033[1m'
    CURSOR_ERASE_SEQUENCE = '\033[K'
    CURSOR_FORWARD_SEQUENCE = '\033[%sC'

    def __init__(self, app):
        super(TerminalPrompt, self).__init__(app)
        self.app.callbacks.prompt_output += self.on_prompt_output
        self.app.callbacks.enter_command += self.on_any_command
        self.app.callbacks.undefined_command += self.on_any_command
        self.app.callbacks.output += self.on_output

    def define_sequences(self):
        self.return_sequence = [13]
        self.up_sequence = [27, 91, 65]
        self.down_sequence = [27, 91, 66]
        self.left_sequence = [27, 91, 68]
        self.right_sequence = [27, 91, 67]
        self.back_sequence = [127]
        self.control_c_sequence = [3]
        self.tab_sequence = [9]
        self.double_escape_sequence = [27, 27]

    def on_prompt_output(self, message = None, cursor_index = -1):
        if message != None:
            stdout.write('\r%s%s%s%s%s' % (self.COMMAND_PREFIX, self.BOLD_COLOR, message, self.DEFAULT_COLOR, self.CURSOR_ERASE_SEQUENCE))
        if cursor_index != None:
            stdout.write('\r%s' % (self.CURSOR_FORWARD_SEQUENCE % (cursor_index + len(self.COMMAND_PREFIX))))

    def on_any_command(self, *args):
        stdout.write('\n')

    def on_output(self, message = None, prompt = True):
        stdout.write(message)
        if prompt:
            stdout.write('\n')
            self.on_prompt_output('', 0)