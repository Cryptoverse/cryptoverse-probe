from callback_result import CallbackResult
from database_services.sqlite_handlers.base_sqlite_handler import BaseSqliteHandler
from models.block_data_model import BlockDataModel

class BlockDataSqlite(BaseSqliteHandler):

    def __init__(self):
        super(BlockDataSqlite, self).__init__(
            BlockDataModel,
            'block_data',
            [
                'block_id',
                'previous_block_id',
                'uri',
                'data'
            ]
        )

    # General functionality

    def write(self, model, done=None):
        connection, cursor = self.begin()
        try:
            values = (
                model.block_id,
                model.previous_block_id,
                model.uri,
                model.data
            )
            if model.id is None:
                cursor.execute('INSERT INTO block_data VALUES (?,?,?,?)', values)
                model.id = cursor.lastrowid
            else:
                cursor.execute('UPDATE block_data SET %s WHERE rowid=?' % self.column_updates, values + (model.id,))
            
            connection.commit()
            if done:
                done(CallbackResult(model))
        finally:
            connection.close()

    def read(self, model_id, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM block_data WHERE rowid=?', (model_id,)).fetchone()
            if result:
                model = self.model_from_request(result)
                done(CallbackResult(model))
            else:
                done(CallbackResult('Block Data with id %s not found' % model_id, False))
        finally:
            connection.close()

    # Optimized functionality

    def find_data_by_block_id(self, block_id, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM block_data WHERE block_id=?', (block_id,)).fetchone()
            if result:
                model = self.model_from_request(result)
                done(CallbackResult(model))
            else:
                done(CallbackResult('Block Data with block_id %s not found' % block_id, False))
        finally:
            connection.close()

    # Utility

    def model_from_request(self, result):
        model = BlockDataModel()
        model.id = result[0]
        model.block_id = result[1]
        model.previous_block_id = result[2]
        model.uri = result[3]
        model.data = result[4]
        return model