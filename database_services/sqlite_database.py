from database_services.base_database import BaseDatabase
from database_services.sqlite_handlers.command_history_sqlite import CommandHistorySqlite

class SqliteDatabase(BaseDatabase):

    def __init__(self, app):

        self.command_history = CommandHistorySqlite()

        super(SqliteDatabase, self).__init__(
            app,
            [
                self.command_history
            ]
        )

    def find_command_history(self, index, done):
        self.command_history.find_command_history(index, done)