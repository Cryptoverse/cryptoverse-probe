import sys
import sqlite3
from os.path import dirname as directory_name, join as join_paths
from database_services.base_database_handler import BaseDatabaseHandler
from callback_result import CallbackResult

DATABASE_FILE_NAME = 'local.db'

if getattr(sys, 'frozen', False):
    APPLICATION_PATH = directory_name(sys.executable)
elif __file__:
    APPLICATION_PATH = directory_name(__file__)
else:
    raise RuntimeError('Cannot find application location')

DATABASE_LOCATION = join_paths(APPLICATION_PATH, DATABASE_FILE_NAME)

class BaseSqliteHandler(BaseDatabaseHandler):

    def __init__(self, app, model_type, table_name, column_names):
        super(BaseSqliteHandler, self).__init__(app, model_type)
        if table_name is None:
            raise ValueError('table_name cannot be None')
        if column_names is None:
            raise ValueError('column_names cannot be None')

        self.table_name = table_name
        self.column_names = column_names
        self.column_updates = ''

        column_count = len(self.column_names)
        for i in range(0, column_count):
            self.column_updates += '%s=?' % self.column_names[i]
            if i < column_count - 1:
                self.column_updates += ','

    def initialize(self, done, rebuild=False):
        connection, cursor = self.begin()
        try:
            if rebuild:
                cursor.execute('DROP TABLE IF EXISTS %s' % self.table_name)
            cursor.execute('CREATE TABLE IF NOT EXISTS %s %s' % (self.table_name, self.concat_list(self.column_names)))
            connection.commit()
        finally:
            connection.close()
        done(CallbackResult())

    def begin(self):
        connection = sqlite3.connect(DATABASE_LOCATION)
        cursor = connection.cursor()
        return connection, cursor

    def concat_list(self, target):
        if not target:
            raise ValueError('target cannot be None or empty')
        result = '('
        result += '%s, ' * (len(target) - 1)
        result += '%s)'
        result = result % tuple(target)
        return result

    def drop(self, model, done=None):
        connection, cursor = self.begin()
        try:
            cursor.execute('DELETE FROM %s WHERE rowid=?' % self.table_name, (model.id,))
            connection.commit()
            if done:
                done(CallbackResult())
        finally:
            connection.close()

    def drop_all(self, done=None):
        connection, cursor = self.begin()
        try:
            cursor.execute('DELETE FROM %s' % self.table_name)
            connection.commit()
            if done:
                done(CallbackResult())
        finally:
            connection.close()

    def count(self, done):
        connection, cursor = self.begin()
        try:
            done(CallbackResult(self.locked_count(cursor)))
        finally:
            connection.close()

    def locked_count(self, cursor):
        return cursor.execute('SELECT COUNT(*) FROM %s' % self.table_name).fetchone()[0]