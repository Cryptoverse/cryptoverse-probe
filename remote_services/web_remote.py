from traceback import print_exc
import requests
from callback_result import CallbackResult
from remote_services.base_remote import BaseRemote
from models.rules_model import RulesModel

class WebRemote(BaseRemote):

    def get_rules(self, node, done):
        result = self.get_request('%s/rules' % node.url)
        if result.is_error:
            done(result)
            return
        model = RulesModel()
        try:
            model.jump_cost_min = result['jump_cost_min']
            model.jump_cost_max = result['jump_cost_max']
            model.jump_distance_max = result['jump_distance_max']
            model.difficulty_fudge = result['difficulty_fudge']
            model.difficulty_start = result['difficulty_start']
            model.difficulty_interval = result['difficulty_interval']
            model.difficulty_duration = result['difficulty_duration']
            model.cartesian_digits = result['cartesian_digits']
            model.probe_reward = result['probe_reward']
        except:
            done(CallbackResult('Parsing error on rules result', False))
            return
        done(CallbackResult(model))

    def get_request(self, url, payload=None, verbose=False):
        try:
            return CallbackResult(requests.get(url, payload).json())
        except:
            if verbose:
                print_exc()
            return CallbackResult('Error on get request: %s' % url, False)