from traceback import print_exc
from json import dumps as json_dump
import requests
from callback_result import CallbackResult
from remote_services.base_remote import BaseRemote
from models.rules_model import RulesModel
from models.node_limits_model import NodeLimitsModel
from models.block_model import BlockModel

class WebRemote(BaseRemote):

    def get_rules(self, node, done):
        # TODO: Thread this
        result = self.get_request('%s/rules' % node.url)
        if result.is_error:
            done(result)
            return
        rules = RulesModel()
        limits = NodeLimitsModel()
        try:
            json = result.content
            rules.version = json['version']
            rules.event_version = json['event_version']
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


    def get_events(self, node, done):
        # TODO: All this
        done(CallbackResult([]))


    def post_block(self, node, done, block):
        result = self.post_request('%s/blocks' % node.url, json_dump(block.get_json()))
        done(result)


    def get_block(self,
                  node,
                  done,
                  previous_hash=None,
                  before_time=None,
                  since_time=None,
                  limit=None,
                  offset=None):
        payload = {
            'previous_hash': previous_hash,
            'before_time': before_time,
            'since_time': since_time,
            'limit': limit,
            'offset': offset
        }
        result = self.get_request('%s/blocks' % node.url, payload, True)
        if result.is_error:
            done(result)
            return
        blocks = []
        try:
            for json in result.content:
                block = BlockModel()
                block.set_from_json(json)
                blocks.append(block)
        except:
            done(CallbackResult('Parsing error on rules result', False))
            return
        done(CallbackResult(blocks))


    def get_request(self, url, payload=None, verbose=False):
        try:
            return CallbackResult(requests.get(url, payload).json())
        except:
            if verbose:
                print_exc()
            return CallbackResult('Error on get request: %s' % url, False)


    def post_request(self, url, payload=None, verbose=False):
        try:
            return CallbackResult(requests.post(url, data=payload, headers={'content-type': 'application/json', 'cache-control': 'no-cache', }).json())
        except:
            if verbose:
                print_exc()
            return CallbackResult('error on post request %s' % url, False)