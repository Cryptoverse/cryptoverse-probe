from callback_result import CallbackResult
from database_services.sqlite_handlers.base_sqlite_handler import BaseSqliteHandler
from models.rules_model import RulesModel

class RulesSqlite(BaseSqliteHandler):

    def __init__(self):
        super(RulesSqlite, self).__init__(
            RulesModel,
            'rules',
            [
                'version',
                'jump_cost_min',
                'jump_cost_max',
                'jump_distance_max',
                'difficulty_fudge',
                'difficulty_start',
                'difficulty_interval',
                'difficulty_duration',
                'cartesian_digits',
                'probe_reward',
                'event_version'
            ]
        )

    # General functionality

    def write(self, model, done=None):
        connection, cursor = self.begin()
        try:
            values = (
                model.version,
                model.jump_cost_min,
                model.jump_cost_max,
                model.jump_distance_max,
                model.difficulty_fudge,
                model.difficulty_start,
                model.difficulty_interval,
                model.difficulty_duration,
                model.cartesian_digits,
                model.probe_reward,
                model.event_version
            )
            if model.id is None:
                cursor.execute('INSERT INTO rules VALUES (?,?,?,?,?,?,?,?,?,?,?)', values)
                model.id = cursor.lastrowid
            else:
                cursor.execute('UPDATE rules SET %s WHERE rowid=?' % self.column_updates, values + (model.id,))
            
            connection.commit()
            if done:
                done(CallbackResult(model))
        finally:
            connection.close()

    def read(self, model_id, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM rules WHERE rowid=?', (model_id,)).fetchone()
            if result:
                model = self.model_from_request(result)
                done(CallbackResult(model))
            else:
                done(CallbackResult('Rules with id %s not found' % model_id, False))
        finally:
            connection.close()

    # Optimized functionality

    def find_rules(self, done):
        connection, cursor = self.begin()
        try:
            result = cursor.execute('SELECT rowid, * FROM rules').fetchone()
            if result:
                model = self.model_from_request(result)
                done(CallbackResult(model))
            else:
                done(CallbackResult(None))
        finally:
            connection.close()

    # Utility

    def model_from_request(self, result):
        model = RulesModel()
        model.id = result[0]
        model.version = result[1]
        model.jump_cost_min = result[2]
        model.jump_cost_max = result[3]
        model.jump_distance_max = result[4]
        model.difficulty_fudge = result[5]
        model.difficulty_start = result[6]
        model.difficulty_interval = result[7]
        model.difficulty_duration = result[8]
        model.cartesian_digits = result[9]
        model.probe_reward = result[10]
        model.event_version = result[11]
        return model