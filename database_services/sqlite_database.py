from database_services.base_database import BaseDatabase
from database_services.sqlite_handlers.command_history_sqlite import CommandHistorySqlite
from database_services.sqlite_handlers.account_sqlite import AccountSqlite
from database_services.sqlite_handlers.meta_sqlite import MetaSqlite

class SqliteDatabase(BaseDatabase):

    def __init__(self, app):

        self.command_history = CommandHistorySqlite()
        self.account = AccountSqlite()
        self.meta = MetaSqlite()

        super(SqliteDatabase, self).__init__(
            app,
            [
                self.command_history,
                self.account,
                self.meta
            ]
        )

    def find_command_history(self, index, done):
        self.command_history.find_command_history(index, done)

    def find_account_active(self, done):
        self.account.find_account_active(done)