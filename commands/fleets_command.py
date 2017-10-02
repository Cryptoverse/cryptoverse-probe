from commands.base_command import BaseCommand
import util

class FleetsCommand(BaseCommand):

    COMMAND_NAME = 'fleets'

    def __init__(self, app):
        super(FleetsCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'List vessels the active account controls',
            parameter_usages = [
                'None: lists all vessels controlled by the active account in the highest chain',
                '"-s" lists all controlled vessels within a system matching the specified fragment in the highest chain',
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
        def on_find_highest_block(find_highest_block_result):
            if find_highest_block_result.is_error:
                self.app.callbacks.on_error(find_highest_block_result.content)
                return
            block = find_highest_block_result.content
            def on_find_active_outputs(find_active_outputs_results):
                if find_active_outputs_results.is_error:
                    self.app.callbacks.on_error(find_active_outputs_results.content)
                    return
                self.app.callbacks.on_output(self.concat_vessels(find_active_outputs_results.content, block.hash))
            self.app.database.event_output.find_active_outputs(on_find_active_outputs, 
                                                               block,
                                                               ['vessel'],
                                                               None)
        self.app.database.block.find_highest_block(on_find_highest_block)


    def on_list_in_system(self, system_hash_fragment):
        raise NotImplementedError


    def on_list_to_block(self, block_hash_fragment):
        raise NotImplementedError

    # Shared

    def concat_vessels(self, vessel_event_outputs, block_hash):
        result = 'Active vessels as of block %s' % util.get_shortened_hash(block_hash)
        fleet_vessels = []
        for vessel_event_output in vessel_event_outputs:
            fleet_hash = vessel_event_output.fleet.get_hash()
            existing = [x for x in fleet_vessels if x[0] == fleet_hash]
            existing = None if len(existing) == 0 else existing[0]
            if existing is None:
                fleet_vessels.append((fleet_hash, [ vessel_event_output ]))
            else:
                existing[1].append(vessel_event_output)
        
        for fleet_vessel in fleet_vessels:
            fleet_hash, event_outputs = fleet_vessel
            result += '\n - Fleet %s:' % event_outputs[0].fleet.get_fleet_name()
            for event_output in event_outputs:
                vessel_name = util.get_shortened_hash(event_output.hash, strip_zeros=False)
                result += '\n\t - %s' % vessel_name
        return result

