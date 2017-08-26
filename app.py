from datetime import datetime
from callback_service import CallbackService
from command_service import CommandService

class App():

    def __init__(self):
        self.callbacks = CallbackService()
        self.exited = False
        self.callbacks.update += self.on_update

        from prompt_services.terminal_prompt import TerminalPrompt
        self.prompt = TerminalPrompt(self)

        self.commands = CommandService(self)

    def begin(self):
        last_update = datetime.now()
        while not self.exited:
            now = datetime.now()
            self.callbacks.on_update((now - last_update).total_seconds())
            last_update = now

    def exit(self, reason = 'User request'):
        self.callbacks.on_output('Exiting: %s' % reason, False)
        self.exited = True

    def on_update(self, delta):
        pass