import util
from callback_result import CallbackResult

# TODO: Figure out if we need this, I think we will for versioned APIs.
class BaseRemote(object):

    def __init__(self, app):
        self.app = app
        self.node_success_count = 0
        self.on_initialized = None

    def initialize(self, done):
        if done is None:
            raise TypeError('"done" cannot be None')
        self.on_initialized = done
        self.app.database.node.find_recent_nodes(self.on_recent_nodes)

    def on_recent_nodes(self, result):
        if result.is_error:
            self.on_initialized(result)
            return
        if result.content is None or len(result.content) == 0:
            self.on_initialized(CallbackResult('Unable to syncronize, no recent nodes'))
            return
        
        def on_find_rules(find_rules_result):
            if find_rules_result.is_error:
                self.on_initialized(find_rules_result)
                return
            self.check_rules(find_rules_result.content, result.content)
        self.app.database.rules.find_rules(on_find_rules)

    def check_rules(self, local_rules, remaining_nodes):
        current_node = remaining_nodes[0]
        remaining_nodes = remaining_nodes[1:]
        if len(remaining_nodes) == 0:
            on_continue = self.on_checked_rules
        else:
            on_continue = lambda: self.check_rules(local_rules, remaining_nodes)
        
        def on_get_rules(get_rules_result):
            if get_rules_result.is_error:
                on_continue()
            else:
                node_rules, node_limits = get_rules_result.content
                current_node.last_response_datetime = util.get_time()
                
                def on_check_local_rules(check_local_rules_result):
                    if check_local_rules_result.is_error:
                        self.on_initialized(check_local_rules_result)
                        return
                    local_rules = check_local_rules_result.content
                    if local_rules.is_match(node_rules):
                        current_node.events_limit_max = node_limits.events_limit_max
                        current_node.blocks_limit_max = node_limits.blocks_limit_max
                        self.node_success_count += 1
                    else:
                        current_node.blacklisted = True
                        current_node.blacklist_reason = 'Rules do not match local rules'
                    def on_write_node(write_node_result):
                        if write_node_result.is_error:
                            self.on_initialized(write_node_result)
                            return
                        on_continue()
                    self.app.database.node.write(current_node, on_write_node)
                if local_rules is None:
                    self.app.database.rules.write(node_rules, on_check_local_rules)
                else:
                    on_check_local_rules(CallbackResult(local_rules))
        current_node.last_request_datetime = util.get_time()
        self.get_rules(current_node, on_get_rules)

    def on_checked_rules(self):
        if 0 < self.node_success_count:
            self.on_initialized(CallbackResult('Remote services initialized, pinged %s nodes successfully' % self.node_success_count))
        else:
            self.on_initialized(CallbackResult('Remote services initialized, but no nodes could be synchronized'))

    def get_rules(self, node, done):
        raise NotImplementedError

    def get_events(self, node, done):
        raise NotImplementedError

    def post_block(self, node, block, done):
        raise NotImplementedError