from callback_result import CallbackResult
from database_services.base_database_handler import BaseDatabaseHandler
from models.event_output_model import EventOutputModel

class EventOutputShared(BaseDatabaseHandler):

    def __init__(self, app):
        super(EventOutputShared, self).__init__(app, EventOutputModel)

    # General functionality

    # Optimized functionality

    def find_output_by_hash_fragment(self, 
                                     done, 
                                     block, 
                                     output_hash_fragment,
                                     rules=None):
        if rules is None:
            def on_find_rules(find_rules_result):
                if find_rules_result.is_error:
                    done(find_rules_result)
                    return
                if find_rules_result.content is None:
                    done(CallbackResult('No rules found', False))
                    return
                self.find_output_by_hash_fragment(done, block, output_hash_fragment, find_rules_result.content)
            self.app.database.rules.find_rules(on_find_rules)
            return

        def on_find_block_data(find_block_data_result):
            if find_block_data_result.is_error:
                done(find_block_data_result)
                return
            block.set_from_json(find_block_data_result.content.get_json())
            for event in block.events:
                for event_output in event.outputs:
                    if event_output.hash.startswith(output_hash_fragment):
                        done(CallbackResult(event_output))
                        return
            if block.is_genesis(rules):
                done(CallbackResult('No output with fragment "%s" found' % output_hash_fragment, False))
                return
            def on_find_block(find_block_result):
                if find_block_result.is_error:
                    done(find_block_result)
                    return
                self.find_output_by_hash_fragment(done, find_block_result.content, output_hash_fragment, rules)
            self.app.database.block.find_block_by_id(block.previous_id, on_find_block)
        self.app.database.block_data.find_data_by_block_id(block.id, on_find_block_data)


    def find_active_outputs(self, 
                            done, 
                            block,
                            model_types, 
                            fleet_hashes):
        self.on_find_active_outputs(done, block, model_types, fleet_hashes, [], [])

    def on_find_active_outputs(self,
                               done,
                               block,
                               model_types, 
                               fleet_hashes,
                               used_outputs, 
                               active_outputs):
        if block is None:
            done(CallbackResult(active_outputs))
            return

        def on_find_block_data(find_block_data_result):
            if find_block_data_result.is_error:
                done(find_block_data_result)
                return
            block.set_from_json(find_block_data_result.content.get_json())
            for event in block.events:
                for event_input in event.inputs:
                    used_outputs.append(event_input.hash)
                # Filter outputs that have been used.
                event_outputs = [x for x in event.outputs if x.hash not in used_outputs]
                if fleet_hashes is not None:
                    event_outputs = [x for x in event_outputs if x.fleet.get_hash() in fleet_hashes]
                if model_types is not None:
                    event_outputs = [x for x in event_outputs if x.model.model_type in model_types]
                active_outputs.extend(event_outputs)
            def on_find_previous_block(find_previous_block_result):
                if find_previous_block_result.is_error:
                    done(find_previous_block_result)
                    return
                self.on_find_active_outputs(done, find_previous_block_result.content, model_types, fleet_hashes, used_outputs, active_outputs)
            if block.previous_id is None:
                on_find_previous_block(CallbackResult(None))
            else:
                self.app.database.block.find_block_by_id(block.previous_id, on_find_previous_block)

        self.app.database.block_data.find_data_by_block_id(block.id, on_find_block_data)
