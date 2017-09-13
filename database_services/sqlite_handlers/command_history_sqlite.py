from callback_result import CallbackResult
from database_services.sqlite_handlers.base_sqlite_handler import BaseSqliteHandler
from models.command_history_model import CommandHistoryModel

class CommandHistorySqlite(BaseSqliteHandler):

    COMMAND_HISTORY_LIMIT = 100

    def __init__(self):
        super(CommandHistorySqlite, self).__init__(
            CommandHistoryModel,
            'command_history',
            [
                'command',
                'time',
                'session_order'
            ]
        )

    # General functionality

    def write(self, model, done=None):
        connection, cursor = self.begin()
        try:
            if model.id is None:
                cursor.execute('INSERT INTO command_history VALUES (?, ?, ?)', (model.command, model.time, model.session_order))
                model.id = cursor.lastrowid
            else:
                cursor.execute('UPDATE command_history SET command=?, time=?, session_order=? WHERE rowid=?', (model.command, model.time, model.session_order))

            if self.COMMAND_HISTORY_LIMIT <= self.locked_count(cursor):
                delete_start = cursor.execute('SELECT time FROM command_history ORDER BY time DESC, session_order DESC LIMIT 1 OFFSET ?', (self.COMMAND_HISTORY_LIMIT,)).fetchone()[0]
                cursor.execute('DELETE FROM command_history WHERE time <= ?', (delete_start,))

            connection.commit()
            if done:
                done(CallbackResult(model))
        finally:
            connection.close()

    # Optimized functionality

    def find_command_history(self, index, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, command, time, session_order FROM command_history ORDER BY time DESC, session_order DESC LIMIT 1 OFFSET ?', (index,)).fetchone()
            if result:
                model = CommandHistoryModel()
                model.id = result[0]
                model.command = result[1]
                model.time = result[2]
                model.session_order = result[3]
                done(CallbackResult(model))
            else:
                done(CallbackResult(None))
        finally:
            connection.close()