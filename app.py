from sys import platform
from datetime import datetime
from callback_service import CallbackService
from command_service import CommandService

class App(object):

    def __init__(self):
        self.callbacks = CallbackService()
        self.exited = False
        self.callbacks.update += self.on_update

        platform_database, platform_prompt = self.get_platform_services()
        
        self.database = platform_database(self)
        self.prompt = platform_prompt(self)
        self.commands = CommandService(self)

    def get_platform_services(self):
        if platform == 'darwin':
            from database_services.sqlite_database import SqliteDatabase
            from prompt_services.terminal_prompt import TerminalPrompt
            return (SqliteDatabase, TerminalPrompt)
        elif platform == 'win32':
            raise Exception('Windows is not currently supported')
        elif platform == 'linux2':
            raise Exception('Linux is not currently supported')

    def begin(self):
        self.database.initialize(self.on_initialized)

    def on_initialized(self, result):
        if result.is_error:
            raise Exception(result.content if result.content is not None else 'Initialization failed')

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