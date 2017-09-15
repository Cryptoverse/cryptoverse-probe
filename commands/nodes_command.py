from callback_result import CallbackResult
from commands.base_command import BaseCommand
from models.node_model import NodeModel
import util

class NodesCommand(BaseCommand):

    COMMAND_NAME = 'nodes'

    def __init__(self, app):
        super(NodesCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'Lists all cached nodes',
            parameter_usages = [
                'None: Lists all active and inactive cached nodes',
                '"-a <url>" adds a new node',
                '"-r <id>" removes an existing node',
                '"-b <id>" blacklists a node',
                '"-w <id>" whitelists a node',
                '"-p <id>" pings a node'
            ],
            command_handlers = [
                self.get_handler(None, self.on_list),
                self.get_handler('-a', self.on_add, 1),
                self.get_handler('-r', self.on_remove, 1),
                self.get_handler('-b', self.on_blacklist, 1),
                self.get_handler('-w', self.on_whitelist, 1),
                self.get_handler('-p', self.on_ping, 1)
            ]
        )

    # Events

    def on_list(self):
        def on_read_all(read_all_result):
            if read_all_result.is_error:
                self.app.callbacks.on_error('Error reading nodes: %s' % read_all_result.content)
            elif read_all_result.content is None or len(read_all_result.content) == 0:
                self.app.callbacks.on_error('No nodes to list')
            else:
                message = 'All Nodes\n'
                for node in read_all_result.content:
                    current_entry = '[%s] %s\n' % (node.id, node.url)
                    current_entry += '\tActive: %s\n' % ('True' if node.get_active() else 'False')
                    if node.blacklisted:
                        current_entry += '\tBlacklisted: %s' % (node.blacklist_reason if node.blacklist_reason else 'unknown')
                    message += current_entry
                self.app.callbacks.on_output(message)
        self.app.database.node.read_all(None, on_read_all)

    def on_add(self, url):
        def on_check_duplicate(check_duplicate_result):
            if check_duplicate_result.is_error:
                model = NodeModel()
                model.url = url
                model.last_request_datetime = util.get_time()
                model.blacklisted = False
                model.blacklist_reason = None

                def on_find_rules(find_rules_result):
                    if find_rules_result.is_error:
                        self.app.callbacks.on_error(find_rules_result.content)
                        return
                    existing_rules = find_rules_result.content
                    def on_get_rules(get_rules_result):
                        rules_set = False
                        if get_rules_result.is_error:
                            self.app.callbacks.on_error(get_rules_result.content)
                            return
                        node_rules, node_limits = get_rules_result.content
                        def on_check_rules(check_rules_result):
                            if check_rules_result.is_error:
                                self.app.callbacks.on_error(check_rules_result.content)
                                return
                            
                            def on_write_node(write_node_result):
                                if write_node_result.is_error:
                                    self.app.callbacks.on_error(write_node_result.content)
                                elif rules_set:
                                    self.app.callbacks.on_output('Added node and set rules successfully')
                                elif model.blacklisted:
                                    self.app.callbacks.on_error('Added node, but blacklisted with reason "%s"' % model.blacklist_reason)
                                else:
                                    self.app.callbacks.on_output('Added node successfully')
                            model.last_response_datetime = util.get_time()
                            model.events_limit_max = node_limits.events_limit_max
                            model.blocks_limit_max = node_limits.blocks_limit_max
                            self.app.database.node.write(model, on_write_node)
                        if existing_rules is None:
                            rules_set = True
                            self.app.database.rules.write(node_rules, on_check_rules)
                        elif existing_rules.is_match(node_rules):
                            on_check_rules(CallbackResult())
                        else:
                            model.blacklisted = True
                            model.blacklist_reason = 'Node rules and local rules do not match'
                            on_check_rules(CallbackResult())
                    self.app.remote.get_rules(model, on_get_rules)

                self.app.database.rules.find_rules(on_find_rules)
            else:
                self.app.callbacks.on_error('A node with url "%s" already exists' % url)
        self.app.database.node.find_by_url(url, on_check_duplicate)

    def on_remove(self, node_id):
        pass

    def on_blacklist(self, node_id):
        pass

    def on_whitelist(self, node_id):
        pass

    def on_ping(self, node_id):
        def on_find_node(find_node_result):
            if find_node_result.is_error:
                self.app.callbacks.on_error(find_node_result.content)
                return
            node = find_node_result.content
            node.blacklisted = False
            node.blacklist_reason = None

            def on_find_rules(find_rules_result):
                if find_rules_result.is_error:
                    self.app.callbacks.on_error(find_rules_result.content)
                    return
                existing_rules = find_rules_result.content
                def on_get_rules(get_rules_result):
                    rules_set = False
                    if get_rules_result.is_error:
                        self.app.callbacks.on_error(get_rules_result.content)
                        return
                    node_rules, node_limits = get_rules_result.content
                    def on_check_rules(check_rules_result):
                        if check_rules_result.is_error:
                            self.app.callbacks.on_error(check_rules_result.content)
                            return
                        
                        def on_write_node(write_node_result):
                            if write_node_result.is_error:
                                self.app.callbacks.on_error(write_node_result.content)
                            elif rules_set:
                                self.app.callbacks.on_output('Pinged node and set rules')
                            elif node.blacklisted:
                                self.app.callbacks.on_error('Pinged node, but blacklisted with reason "%s"' % node.blacklist_reason)
                            else:
                                self.app.callbacks.on_output('Pinged node successfully')
                        node.last_response_datetime = util.get_time()
                        node.events_limit_max = node_limits.events_limit_max
                        node.blocks_limit_max = node_limits.blocks_limit_max
                        self.app.database.node.write(node, on_write_node)
                    if existing_rules is None:
                        rules_set = True
                        self.app.database.rules.write(node_rules, on_check_rules)
                    elif existing_rules.is_match(node_rules):
                        on_check_rules(CallbackResult())
                    else:
                        node.blacklisted = True
                        node.blacklist_reason = 'Node rules and local rules do not match'
                        on_check_rules(CallbackResult())
                self.app.remote.get_rules(node, on_get_rules)
            self.app.database.rules.find_rules(on_find_rules)
        self.app.database.node.find_by_id(node_id, on_find_node)