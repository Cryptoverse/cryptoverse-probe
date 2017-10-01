from commands.base_command import BaseCommand
from callback_result import CallbackResult

class FleetsCommand(BaseCommand):

    COMMAND_NAME = 'fleets'

    def __init__(self, app):
        super(FleetsCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'List vessels the active account controls',
            parameter_usages = [
                'None: lists all vessels controlled by the active account',
                '"-s" lists all controlled vessels within a system matching the specified fragment',
                '"-b" lists all controlled vessels up to the specified block flagment hash'
            ],
            command_handlers = [
                self.get_handler(None, self.on_list_all),
                self.get_handler('-s', self.on_list_in_system),
                self.get_handler('-b', self.on_list_to_block)
            ]
        )

    # Commands

    def on_list_all(self):
        pass


    def on_list_in_system(self, system_hash_fragment):
        raise NotImplementedError


    def on_list_to_block(self, block_hash_fragment):
        raise NotImplementedError

    # Shared

    def get_vessels(self, done, block, used_outputs, vessels, fleets):
        if block is None:
            done(CallbackResult(vessels))
            return

        def on_find_block_data(find_block_data_result):
            if find_block_data_result.is_error:
                done(find_block_data_result)
                return
            block.set_from_json(find_block_data_result.content.get_json())
            for event in block.events:
                for event_input in event.inputs:
                    # used_outputs.append(event_input.)
                    pass
                
        self.app.database.block_data.find_data_by_block_id(block.id, on_find_block_data)
