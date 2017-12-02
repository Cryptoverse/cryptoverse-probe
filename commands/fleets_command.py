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
        def on_find_account(find_account_result):
            if find_account_result.is_error:
                self.app.callbacks.on_error(find_account_result.content)
                return
            fleets = [ find_account_result.content.get_fleet().get_hash() ]
            def on_find_highest_block(find_highest_block_result):
                if find_highest_block_result.is_error:
                    self.app.callbacks.on_error(find_highest_block_result.content)
                    return
                block = find_highest_block_result.content
                def on_find_active_outputs(find_active_outputs_results):
                    if find_active_outputs_results.is_error:
                        self.app.callbacks.on_error(find_active_outputs_results.content)
                        return
                    def on_find_root(find_root_result):
                        if find_root_result.is_error:
                            self.app.callbacks.on_error(find_root_result.content)
                            return
                        root_block = find_root_result.content
                        def on_generate_root_galaxy(generate_root_galaxy_result):
                            if generate_root_galaxy_result.is_error:
                                self.app.callbacks.on_error(generate_root_galaxy_result.content)
                                return
                            root_system = generate_root_galaxy_result.content.systems[0]
                            self.app.callbacks.on_output(
                                self.concat_vessels(find_active_outputs_results.content, 
                                                    root_system.get_location(),
                                                    block.hash))
                        self.app.galaxy_generator.generate(on_generate_root_galaxy, root_block.hash, 0)
                    self.app.database.block.find_block_by_id(block.root_id, on_find_root)
                self.app.database.event_output.find_active_outputs(on_find_active_outputs, 
                                                                   block,
                                                                   ['vessel'],
                                                                   fleets)
            self.app.database.block.find_highest_block(on_find_highest_block)
        self.app.database.account.find_account_active(on_find_account)

    def on_list_in_system(self, system_hash_fragment):
        raise NotImplementedError


    def on_list_to_block(self, block_hash_fragment):
        raise NotImplementedError

    # Shared

    def concat_vessels(self, vessel_event_outputs, default_location, block_hash):
        result = 'Active vessels as of block %s' % util.get_shortened_hash(block_hash)
        fleet_vessels = []
        for vessel_event_output in vessel_event_outputs:
            location = default_location if vessel_event_output.location is None else vessel_event_output.location
            fleet = vessel_event_output.fleet
            fleet_hash = fleet.get_hash()
            existing = [x for x in fleet_vessels if x[0].get_hash() == fleet_hash]
            existing = None if len(existing) == 0 else existing[0]
            if existing is None:
                # Sorry about this tuple array hell, it's roughly this:
                # (
                #   fleet: fleet
                #   fleet_locations: [
                #     (
                #       location: system_hash
                #       vessels: [
                #          vessel_hash0
                #          vessel_hash1
                #          ...
                #       ]
                #     )
                #   ]
                # )
                fleet_vessels.append((fleet, [ (location, [ vessel_event_output ]) ]))
            else:
                locations = existing[1]
                existing_location = [x for x in locations if x[0] == location]
                existing_location = None if len(existing_location) == 0 else existing_location[0]
                if existing_location is None:
                    locations[1].append((location, [ vessel_event_output]))
                else:
                    existing_location[1].append(vessel_event_output)
        
        for fleet_vessel in fleet_vessels:
            fleet, fleet_locations = fleet_vessel
            result += '\n - Fleet %s:' % fleet.get_fleet_name()
            for fleet_location in fleet_locations:
                system_hash, vessels = fleet_location
                result += '\n\t - System %s:' % util.get_shortened_hash(system_hash, strip_zeros=False)
                for vessel in vessels:
                    vessel_name = util.get_shortened_hash(vessel.hash, strip_zeros=False)
                    result += '\n\t\t - %s' % vessel_name
        
        return result
