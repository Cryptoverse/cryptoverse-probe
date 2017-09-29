import commands
from callback_result import CallbackResult
from commands.base_command import BaseCommand

class SyncCommand(BaseCommand):

    COMMAND_NAME = 'sync'

    def __init__(self, app):
        super(SyncCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'Synchronizes the local blockchain with new blocks from recent nodes',
            parameter_usages = [
                'None: synchronizes with all of the recent nodes'
            ],
            command_handlers = [
                self.get_handler(None, self.on_sync)
            ]
        )

    # Command

    def on_sync(self):
        def on_synchronize(synchronize_result):
            if synchronize_result.is_error:
                self.app.callbacks.on_error(synchronize_result.content)
                return
            self.app.callbacks.on_output('Syncronized %s blocks from recent nodes' % synchronize_result.content)
        self.synchronize(on_synchronize)

    # Shared

    def synchronize(self, done):
        def on_get_rules(get_rules_result):
            if get_rules_result.is_error:
                done(get_rules_result)
                return
            rules = get_rules_result.content
            def on_get_block(get_block_result):
                if get_block_result.is_error:
                    done(get_block_result)
                    return
                blocks = sorted(get_block_result.content, key=lambda x: x.height)
                def on_cache_blocks(cache_blocks_result):
                    if cache_blocks_result.is_error:
                        done(cache_blocks_result)
                        return
                    done(CallbackResult(len(blocks)))
                self.app.commands.get_command(commands.probe_command.ProbeCommand.COMMAND_NAME).cache_blocks(on_cache_blocks, blocks, rules)
            self.get_block(on_get_block)
        self.app.database.rules.find_rules(on_get_rules)

    # Synchronizing

    def get_block(self, done):
        def on_recent_nodes(recent_nodes_result):
            if recent_nodes_result.is_error:
                done(recent_nodes_result)
                return
            self.on_get_block(done, recent_nodes_result.content)
        self.app.database.node.find_recent_nodes(on_recent_nodes)


    def on_get_block(self, done, nodes, blocks=None):
        if blocks is None:
            blocks = []

        if len(nodes) == 0:
            done(CallbackResult(blocks))
            return

        current_node = nodes[0]
        nodes = nodes[1:]

        def on_get(get_result):
            self.on_get_block(done, nodes, blocks if get_result.is_error else blocks + get_result.content)
        self.on_get_block_offset(on_get, current_node, 0, blocks)


    def on_get_block_offset(self, done, node, offset, blocks):
        if offset == -1:
            done(CallbackResult(blocks))
            return

        def on_get(get_result):
            if get_result.is_error or len(get_result.content) == 0:
                self.on_get_block_offset(done, node, -1, blocks)
                return
            unique_results = [x for x in get_result.content if x.hash not in [y.hash for y in blocks]]
            self.on_get_block_offset(done, node, offset + node.blocks_limit_max, blocks + unique_results)
            
        self.app.remote.get_block(node,
                                  on_get,
                                  limit = node.blocks_limit_max,
                                  offset = offset)
