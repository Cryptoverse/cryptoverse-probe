from callback_event import CallbackEvent as Event

class CallbackService(object):
    
    def __init__(self):
        self.update = Event()
        self.input = Event()
        self.output = Event()
        self.prompt_output = Event()
        self.enter_command = Event()
        self.undefined_command = Event()

    def on_update(self, delta):
        self.update(delta)

    def on_input(self, poll_result):
        self.input(poll_result)

    def on_output(self, message = None):
        self.output(message)

    def on_prompt_output(self, message = None, cursor_index = -1):
        self.prompt_output(message, cursor_index)

    def on_enter_command(self, command, *args):
        self.enter_command(command)

    def on_undefined_command(self, command, *args):
        self.undefined_command(command)