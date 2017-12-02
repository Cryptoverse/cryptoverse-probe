from commands.base_command import BaseCommand

class JRangeCommand(BaseCommand):

    COMMAND_NAME = 'jrange'

    def __init__(self, app):
        super(JRangeCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'Renders the range of jumps in an external plotter',
            parameter_usages = [
                '"-r <vessel hash fragment>" renders systems within reach of that vessel'
            ],
            command_handlers = [
                self.get_handler('-r', self.on_render, 1)
            ]
        )

    # Commands

    def on_render(self, vessel_hash_fragment):
        def on_find_highest_block(find_highest_block_result):
            if find_highest_block_result.is_error:
                self.app.callbacks.on_error(find_highest_block_result.content)
                return
            def on_find_event_output(find_event_output_result):
                if find_event_output_result.is_error:
                    self.app.callbacks.on_error('Unable to find a vessel hash beginning with "%s"' % vessel_hash_fragment)
                    return
                # vessel = find_event_output_result.
                # def on_generate_galaxy
                # TODO: Get all systems in the galaxy and render them...
                self.app.callbacks.on_output(find_event_output_result.content.hash)
            self.app.database.event_output.find_output_by_hash_fragment(on_find_event_output,
                                                                        find_highest_block_result.content,
                                                                        vessel_hash_fragment)
        self.app.database.block.find_highest_block(on_find_highest_block)

    # Shared