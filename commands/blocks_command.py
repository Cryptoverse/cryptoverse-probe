from commands.base_command import BaseCommand

class BlocksCommand(BaseCommand):

    COMMAND_NAME = 'blocks'

    def __init__(self, app):
        super(BlocksCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'List and manage locally stored blocks',
            parameter_usages = [
                'None: Lists the longest chain of blocks stored locally',
                '"-r" resets the local block database permanently'
            ],
            command_handlers = [
                self.get_handler(None, self.on_list_blocks),
                self.get_handler('-r', self.on_reset_blocks)
            ]
        )

    def on_list_blocks(self):
        raise NotImplementedError

    def on_reset_blocks(self):
        def on_count(count_result):
            if count_result.is_error:
                self.app.callbacks.on_error(count_result.content)
                return
            def on_drop_blocks(drop_blocks_result):
                if drop_blocks_result.is_error:
                    self.app.callbacks.on_error(drop_blocks_result.content)
                    return
                def on_drop_block_data(drop_block_data_result):
                    if drop_block_data_result.is_error:
                        self.app.callbacks.on_error(drop_block_data_result.content)
                    else:
                        self.app.callbacks.on_output('A total of %s blocks were deleted' % count_result.content)
                self.app.database.block_data.drop_all(on_drop_block_data)
            self.app.database.block.drop_all(on_drop_blocks)
        self.app.database.block.count(on_count)