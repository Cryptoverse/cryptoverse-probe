from getch import getch

class BasePrompt(object):

    def __init__(self, app):
        self.app = app
        
        self.define_sequences()
        self.define_special_sequences()

        self.app.callbacks.prompt_output += self.on_prompt_output
        self.app.callbacks.enter_command += self.on_any_command
        self.app.callbacks.undefined_command += self.on_any_command
        self.app.callbacks.output += self.on_output
        self.app.callbacks.error += self.on_error
        self.app.callbacks.update += self.on_update


    def define_sequences(self):
        self.return_sequence = None
        self.up_sequence = None
        self.down_sequence = None
        self.left_sequence = None
        self.right_sequence = None
        self.back_sequence = None
        self.control_c_sequence = None
        self.tab_sequence = None
        self.double_escape_sequence = None

    def define_special_sequences(self):
        self.special_sequences = [
            self.tab_sequence,
            self.return_sequence,
            self.up_sequence,
            self.down_sequence,
            self.left_sequence,
            self.right_sequence,
            self.back_sequence,
            self.control_c_sequence,
            self.double_escape_sequence
        ]

    def poll_input(self):
        alpha_numeric_range = range(32, 127)
        chars = []
        while True:
            is_special = chars in self.special_sequences
            if is_special:
                break
            char = ord(getch())
            chars.append(char)
            if len(chars) == 1 and char in alpha_numeric_range:
                break
            elif 1 < len(chars):
                last_chars = chars[-2:]
                if last_chars == self.double_escape_sequence:
                    chars = last_chars
                    is_special = True
                    break
        
        result = PollResult()

        if is_special:
            if chars == self.return_sequence:
                result.is_return = True
            elif chars == self.back_sequence:
                result.is_backspace = True
            elif chars == self.control_c_sequence:
                result.is_control_c = True
            elif chars == self.up_sequence:
                result.is_up = True
            elif chars == self.down_sequence:
                result.is_down = True
            elif chars == self.left_sequence:
                result.is_left = True
            elif chars == self.right_sequence:
                result.is_right = True
            elif chars == self.tab_sequence:
                result.is_tab = True
            elif chars == self.double_escape_sequence:
                result.is_double_escape = True
            else:
                print 'Unrecognized special sequence %s' % chars
        elif len(chars) == 1:
            result.alpha_numeric = chr(chars[0])
        else:
            print 'Unrecognized alphanumeric sequence %s' % chars
        
        return result

    def on_update(self, delta):
        result = self.poll_input()
        if result.has_input():
            self.app.callbacks.on_input(result)

    def on_prompt_output(self, message = None, cursor_index = -1):
        raise NotImplementedError

    def on_any_command(self, *args):
        raise NotImplementedError

    def on_output(self, message = None, prompt = True):
        raise NotImplementedError

    def on_error(self, message):
        raise NotImplementedError

class PollResult(object):

    def __init__(self, **kwargs):
        self.alpha_numeric = kwargs.get('alpha_numeric', '')
        self.is_return = kwargs.get('is_return', False)
        self.is_backspace = kwargs.get('is_backspace', False)
        self.is_control_c = kwargs.get('is_control_c', False)
        self.is_up = kwargs.get('is_up', False)
        self.is_down = kwargs.get('is_down', False)
        self.is_left = kwargs.get('is_left', False)
        self.is_right = kwargs.get('is_right', False)
        self.is_tab = kwargs.get('is_tab', False)
        self.is_double_escape = kwargs.get('is_double_escape', False)

    def has_input(self):
        return (
            self.alpha_numeric != '' or 
            self.is_return or
            self.is_backspace or
            self.is_control_c or
            self.is_up or
            self.is_down or
            self.is_left or
            self.is_right or
            self.is_tab or
            self.is_double_escape
        )