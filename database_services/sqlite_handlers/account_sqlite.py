from callback_result import CallbackResult
from database_services.sqlite_handlers.base_sqlite_handler import BaseSqliteHandler
from models.account_model import AccountModel

class AccountSqlite(BaseSqliteHandler):

    def __init__(self):
        super(AccountSqlite, self).__init__(
            AccountModel,
            'accounts',
            [
                'active',
                'name',
                'private_key',
                'public_key'
            ]
        )

    # General functionality

    def write(self, model, done=None):
        connection, cursor = self.begin()
        try:
            active_as_int = 1 if model.active == 1 else 0
            if model.id is None:
                cursor.execute('INSERT INTO accounts VALUES (?, ?, ?, ?)', (active_as_int, model.name, model.private_key, model.public_key))
                model.id = cursor.lastrowid
            else:
                cursor.execute('UPDATE accounts SET active=?, name=?, private_key=?, public_key=? WHERE rowid=?', (active_as_int, model.name, model.private_key, model.public_key, model.id))
            
            self.locked_confirm_active(model, cursor)

            connection.commit()
            if done:
                done(CallbackResult(model))
        finally:
            connection.close()

    def read(self, model_id, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT * FROM accounts WHERE rowid=?', (model_id,)).fetchone()
            if result:
                model = AccountModel()
                model.id = model_id
                model.active = result[0] == 1
                model.name = result[1]
                model.private_key = result[2]
                model.public_key = result[3]
                done(CallbackResult(model))
            else:
                done(CallbackResult('Account with id %s not found' % model_id, False))
        finally:
            connection.close()

    def read_all(self, model_ids, done):
        connection, cursor = self.begin()
        try:
            if model_ids is None:
                query = cursor.execute('SELECT rowid, * FROM accounts')
            else:
                query = cursor.execute('SELECT rowid, * FROM accounts WHERE rowid IN ?', (self.concat_list(model_ids),))
            
            results = query.fetchall()
            if results:
                models = []
                for result in results:
                    model = AccountModel()
                    model.id = result[0]
                    model.active = result[1] == 1
                    model.name = result[2]
                    model.private_key = result[3]
                    model.public_key = result[4]
                    models.append(model)
                done(CallbackResult(models))
            else:
                done(CallbackResult('Accounts with provided ids could not be found', False))
        finally:
            connection.close()

    def drop(self, model, done=None):
        connection, cursor = self.begin()
        try:
            cursor.execute('DELETE FROM accounts WHERE rowid=?', (model.id,))
            connection.commit()
        finally:
            connection.close()

    # Optimized functionality

    def find_account(self, name, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM accounts WHERE name=?', (name,)).fetchone()
            if result:
                model = AccountModel()
                model.id = result[0]
                model.active = result[1] == 1
                model.name = result[2]
                model.private_key = result[3]
                model.public_key = result[4]
                done(CallbackResult(model))
            else:
                done(CallbackResult('No active account found', False))
        finally:
            connection.close()

    def find_account_active(self, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM accounts WHERE active=?', (1,)).fetchone()
            if result:
                model = AccountModel()
                model.id = result[0]
                model.active = result[1] == 1
                model.name = result[2]
                model.private_key = result[3]
                model.public_key = result[4]
                done(CallbackResult(model))
            else:
                done(CallbackResult('No active account found', False))
        finally:
            connection.close()

    # Shared

    def locked_confirm_active(self, model, cursor):
        if model.id is None or not model.active:
            return
        cursor.execute('UPDATE accounts SET active=0 WHERE NOT rowid=?', (model.id,))