from traceback import print_exc
import requests
from callback_result import CallbackResult
from remote_services.base_remote import BaseRemote
from models.rules_model import RulesModel
from models.node_limits_model import NodeLimitsModel

class WebRemote(BaseRemote):

    def get_rules(self, node, done):
        result = self.get_request('%s/rules' % node.url)
        if result.is_error:
            done(result)
            return
        rules = RulesModel()
        limits = NodeLimitsModel()
        try:
            json = result.content
            rules.jump_cost_min = json['jump_cost_min']
            rules.jump_cost_max = json['jump_cost_max']
            rules.jump_distance_max = json['jump_distance_max']
            rules.difficulty_fudge = json['difficulty_fudge']
            rules.difficulty_start = json['difficulty_start']
            rules.difficulty_interval = json['difficulty_interval']
            rules.difficulty_duration = json['difficulty_duration']
            rules.cartesian_digits = json['cartesian_digits']
            rules.probe_reward = json['probe_reward']

            limits.blocks_limit_max = json['blocks_limit_max']
            limits.events_limit_max = json['events_limit_max']
        except:
            done(CallbackResult('Parsing error on rules result', False))
            return
        done(CallbackResult((rules,limits)))

    def get_request(self, url, payload=None, verbose=False):
        try:
            return CallbackResult(requests.get(url, payload).json())
        except:
            if verbose:
                print_exc()
            return CallbackResult('Error on get request: %s' % url, False)