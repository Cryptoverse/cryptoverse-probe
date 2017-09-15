from callback_result import CallbackResult
from database_services.sqlite_handlers.base_sqlite_handler import BaseSqliteHandler
from models.node_model import NodeModel

class NodeSqlite(BaseSqliteHandler):

    def __init__(self):
        super(NodeSqlite, self).__init__(
            NodeModel,
            'nodes',
            [
                'url',
                'last_response_datetime',
                'last_request_datetime',
                'events_limit_max',
                'blocks_limit_max',
                'blacklisted',
                'blacklist_reason'
            ]    
        )

    # General functionality

    def write(self, model, done=None):
        connection, cursor = self.begin()
        try:
            values = (
                model.url,
                model.last_response_datetime,
                model.last_request_datetime,
                model.events_limit_max,
                model.blocks_limit_max,
                1 if model.blacklisted else 0,
                model.blacklist_reason
            )
            if model.id is None:
                cursor.execute('INSERT INTO nodes VALUES (?,?,?,?,?,?,?)', values)
                model.id = cursor.lastrowid
            else:
                cursor.execute('UPDATE nodes SET %s WHERE rowid=?' % self.column_updates, values + (model.id,))
            
            connection.commit()
            if done:
                done(CallbackResult(model))
        finally:
            connection.close()

    def read(self, model_id, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM nodes WHERE rowid=?', (model_id,)).fetchone()
            if result:
                model = self.model_from_request(result)
                done(CallbackResult(model))
            else:
                done(CallbackResult('Node with id %s not found' % model_id, False))
        finally:
            connection.close()

    def read_all(self, model_ids, done):
        connection, cursor = self.begin()
        try:
            if model_ids is None:
                query = cursor.execute('SELECT rowid, * FROM nodes')
            else:
                query = cursor.execute('SELECT rowid, * FROM nodes WHERE rowid IN ?', (self.concat_list(model_ids),))
            
            results = query.fetchall()
            models = []
            if results:
                for result in results:
                    models.append(self.model_from_request(result))
            done(CallbackResult(models))
        finally:
            connection.close()


    def drop(self, model, done=None):
        connection, cursor = self.begin()
        try:
            cursor.execute('DELETE FROM nodes WHERE rowid=?', (model.id,))
            connection.commit()
        finally:
            connection.close()

    # Optimized functionality

    def find_recent_nodes(self, done):
        connection, cursor = self.begin()
        try:
            results = cursor.execute('SELECT rowid, * FROM nodes WHERE blacklisted=? ORDER BY last_response_datetime DESC', (0,)).fetchall()
            models = []
            if results:
                for result in results:
                    models.append(self.model_from_request(result))
            done(CallbackResult(models))
        finally:
            connection.close()

    def find_by_url(self, url, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM nodes WHERE url=?', (url,)).fetchone()
            if result:
                done(CallbackResult(self.model_from_request(result)))
            else:
                done(CallbackResult('No node with url "%s" exists' % url, False))
        finally:
            connection.close()
    
    def find_by_id(self, model_id, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM nodes WHERE rowid=?', (model_id,)).fetchone()
            if result:
                done(CallbackResult(self.model_from_request(result)))
            else:
                done(CallbackResult('No node with id "%s" exists' % model_id, False))
        finally:
            connection.close()

    # Utility

    def model_from_request(self, result):
        model = NodeModel()
        model.id = result[0]
        model.url = result[1]
        model.last_response_datetime = result[2]
        model.last_request_datetime = result[3]
        model.events_limit_max = result[4]
        model.blocks_limit_max = result[5]
        model.blacklisted = result[6] == 1
        model.blacklist_reason = result[7]
        return model