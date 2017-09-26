from callback_result import CallbackResult
from database_services.sqlite_handlers.base_sqlite_handler import BaseSqliteHandler
from models.block_model import BlockModel

class BlockSqlite(BaseSqliteHandler):

    def __init__(self):
        super(BlockSqlite, self).__init__(
            BlockModel,
            'blocks',
            [
                'hash',
                'previous_hash',
                'previous_id',
                'height',
                'size',
                'version',
                'difficulty',
                'time', 
                'interval_id',
                'root_id',
                'chain'
            ]
        )

    # General functionality

    def write(self, model, done=None):
        connection, cursor = self.begin()
        try:
            values = (
                model.hash,
                model.previous_hash,
                model.previous_id,
                model.height,
                model.size,
                model.version,
                model.difficulty,
                model.time,
                model.interval_id,
                model.root_id,
                model.chain
            )
            if model.id is None:
                cursor.execute('INSERT INTO blocks VALUES (?,?,?,?,?,?,?,?,?,?,?)', values)
                model.id = cursor.lastrowid
            else:
                cursor.execute('UPDATE blocks SET %s WHERE rowid=?' % self.column_updates, values + (model.id,))
            
            connection.commit()
            if done:
                done(CallbackResult(model))
        finally:
            connection.close()

    def read(self, model_id, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM blocks WHERE rowid=?', (model_id,)).fetchone()
            if result:
                model = self.model_from_request(result)
                done(CallbackResult(model))
            else:
                done(CallbackResult('Block with id %s not found' % model_id, False))
        finally:
            connection.close()

    # Optimized functionality

    def find_block_by_id(self, model_id, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM blocks WHERE rowid=?', (model_id,)).fetchone()
            if result:
                model = self.model_from_request(result)
                done(CallbackResult(model))
            else:
                done(CallbackResult('Block with id %s not found' % model_id, False))
        finally:
            connection.close()

    def find_block_by_hash(self, block_hash, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM blocks WHERE hash=?', (block_hash,)).fetchone()
            if result:
                model = self.model_from_request(result)
                done(CallbackResult(model))
            else:
                done(CallbackResult('Block with hash %s not found' % block_hash, False))
        finally:
            connection.close()

    def find_highest_block(self, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM blocks ORDER BY height DESC').fetchone()
            if result:
                model = self.model_from_request(result)
                highest_oldest_result = cursor.execute('SELECT rowid, * FROM blocks WHERE height=? ORDER BY time ASC', (model.height,)).fetchone()
                done(CallbackResult(self.model_from_request(highest_oldest_result)))
            else:
                done(CallbackResult('No blocks found', False))
        finally:
            connection.close()

    def find_highest_block_on_chain(self, chain, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM blocks WHERE chain=? ORDER BY height DESC', (chain,)).fetchone()
            if result:
                model = self.model_from_request(result)
                highest_oldest_result = cursor.execute('SELECT rowid, * FROM blocks WHERE height=? AND chain=? ORDER BY time ASC', (model.height,chain)).fetchone()
                done(CallbackResult(self.model_from_request(highest_oldest_result)))
            else:
                done(CallbackResult('No blocks on chain %s found' % chain, False))
        finally:
            connection.close()

    # Utility

    def model_from_request(self, result):
        model = BlockModel()
        model.id = result[0]
        model.hash = result[1]
        model.previous_hash = result[2]
        model.previous_id = result[3]
        model.height = result[4]
        model.size = result[5]
        model.version = result[6]
        model.difficulty = result[7]
        model.time = result[8]
        model.interval_id = result[9]
        model.root_id = result[10]
        model.chain = result[11]
        return model