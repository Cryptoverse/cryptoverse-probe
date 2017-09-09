import sys
import sqlite3
from os.path import dirname as directory_name, join as join_paths
from database_services.base_database_handler import BaseDatabaseHandler
import app

DATABASE_FILE_NAME = 'local.db'

if getattr(sys, 'frozen', False):
    APPLICATION_PATH = directory_name(sys.executable)
elif __file__:
    APPLICATION_PATH = directory_name(__file__)
else:
    raise RuntimeError('Cannot find application location')

DATABASE_LOCATION = join_paths(APPLICATION_PATH, DATABASE_FILE_NAME)

class BaseSqliteHandler(BaseDatabaseHandler):

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