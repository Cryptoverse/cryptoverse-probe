from database_services.base_database import BaseDatabase
from database_services.sqlite_handlers.command_history_sqlite import CommandHistorySqlite
from database_services.sqlite_handlers.account_sqlite import AccountSqlite
from database_services.sqlite_handlers.meta_sqlite import MetaSqlite
from database_services.sqlite_handlers.node_sqlite import NodeSqlite
from database_services.sqlite_handlers.rules_sqlite import RulesSqlite
from database_services.sqlite_handlers.block_sqlite import BlockSqlite
from database_services.sqlite_handlers.block_data_sqlite import BlockDataSqlite

class SqliteDatabase(BaseDatabase):

    def __init__(self, app):
        super(SqliteDatabase, self).__init__(
            app,
            command_history = CommandHistorySqlite(),
            account = AccountSqlite(),
            meta = MetaSqlite(),
            node = NodeSqlite(),
            rules = RulesSqlite(),
            block = BlockSqlite(),
            block_data = BlockDataSqlite()
        )
