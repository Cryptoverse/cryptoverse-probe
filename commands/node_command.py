from callback_result import CallbackResult
from commands.base_command import BaseCommand
from models.node_model import NodeModel
import util

class NodeCommand(BaseCommand):

    def __init__(self, app):
        super(NodeCommand, self).__init__(
            app, 
            'node',
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
                    current_entry = '%s\n' % node.id
                    message += current_entry
                self.app.callbacks.on_output(message)
        self.app.database.node.read_all(None, on_read_all)

    def on_add(self, url):
        model = NodeModel()
        model.url = url
        model.last_request_datetime = util.get_time()

        def on_read_rules(read_rules_result):
            if read_rules_result.is_error:
                self.app.callbacks.on_error(read_rules_result.content)
                return
            existing_rules = read_rules_result.content
            rules_set = False
            def on_get_rules(get_rules_result):
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
                        else:
                            self.app.callbacks.on_output('Added node successfully')
                    model.last_response_datetime = util.get_time()
                    model.events_limit_max = node_limits.events_limit_max
                    model.blocks_limit_max = node_limits.blocks_limit_max
                    model.blacklisted = False
                    model.blacklist_reason = None
                    self.app.database.node.write(model, on_write_node)
                if existing_rules is None:
                    rules_set = True
                    self.app.database.rules.write(node_rules, on_check_rules)
                elif existing_rules.is_match(node_rules):
                    on_check_rules(CallbackResult())
                else:
                    self.app.callbacks.on_error('Node rules and local rules do not match')
            self.app.remote.get_rules(model, on_get_rules)

        self.app.database.rules.find_rules(on_read_rules)


    def on_remove(self, node_id):
        pass

    def on_blacklist(self, node_id):
        pass

    def on_whitelist(self, node_id):
        pass

    def on_ping(self, node_id):
        pass