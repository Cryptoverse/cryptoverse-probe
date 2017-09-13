from database_services.base_database import BaseDatabase
from database_services.sqlite_handlers.command_history_sqlite import CommandHistorySqlite
from database_services.sqlite_handlers.account_sqlite import AccountSqlite
from database_services.sqlite_handlers.meta_sqlite import MetaSqlite
from database_services.sqlite_handlers.node_sqlite import NodeSqlite
from database_services.sqlite_handlers.rules_sqlite import RulesSqlite

class SqliteDatabase(BaseDatabase):

    def __init__(self, app):

        self.command_history = CommandHistorySqlite()
        self.account = AccountSqlite()
        self.meta = MetaSqlite()
        self.node = NodeSqlite()
        self.rules = RulesSqlite()

        super(SqliteDatabase, self).__init__(
            app,
            [
                self.command_history,
                self.account,
                self.meta,
                self.node,
                self.rules
            ]
        )

    def find_command_history(self, index, done):
        self.command_history.find_command_history(index, done)

    def find_account_active(self, done):
        self.account.find_account_active(done)

    def find_recent_nodes(self, done):
        self.node.find_recent_nodes(done)