from callback_result import CallbackResult
from database_services.sqlite_handlers.base_sqlite_handler import BaseSqliteHandler
from models.meta_model import MetaModel

class MetaSqlite(BaseSqliteHandler):

    def __init__(self):
        super(MetaSqlite, self).__init__(MetaModel)

    def initialize(self, done, rebuild=False):
        connection, cursor = self.begin()
        try:
            if rebuild:
                cursor.execute('''DROP TABLE IF EXISTS meta''')
            cursor.execute('''CREATE TABLE IF NOT EXISTS meta (text_content)''')
            connection.commit()
        finally:
            connection.close()
        done(CallbackResult())

    # General functionality

    def write(self, model, done=None):
        connection, cursor = self.begin()
        try:
            if model.id is None:
                cursor.execute('INSERT INTO meta VALUES (?)', (model.text_content,))
                model.id = cursor.lastrowid
            else:
                cursor.execute('UPDATE meta SET text_content=? WHERE rowid=?', (model.text_content, model.id))
            
            connection.commit()
            if done:
                done(CallbackResult(model))
        finally:
            connection.close()

    def read(self, model_id, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT * FROM meta WHERE rowid=?', (model_id,)).fetchone()
            if result:
                model = MetaModel()
                model.id = model_id
                model.text_content = result[0]
                done(CallbackResult(model))
            else:
                done(CallbackResult('Meta with id %s not found' % model_id, False))
        finally:
            connection.close()

    def drop(self, model, done=None):
        connection, cursor = self.begin()
        try:
            cursor.execute('DELETE FROM meta WHERE rowid=?', (model.id,))
            connection.commit()
        finally:
            connection.close()

    # Optimized functionality

    def find_meta(self, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM meta').fetchone()
            if result:
                model = MetaModel()
                model.id = result[0]
                model.text_content = result[1]
                done(CallbackResult(model))
            else:
                done(CallbackResult('No meta found', False))
        finally:
            connection.close()