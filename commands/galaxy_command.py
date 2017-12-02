from commands.base_command import BaseCommand

class GalaxyCommand(BaseCommand):

    COMMAND_NAME = 'galaxy'

    def __init__(self, app):
        super(GalaxyCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'Galaxy generation utilities',
            parameter_usages = [
                '"-g <seed>" generates location data for a galaxy with the specified seed'
            ],
            command_handlers = [
                self.get_handler('-g', self.on_generate, 1)
            ]
        )

    # Commands

    def on_generate(self, seed):
        def on_generate_galaxy(generate_galaxy_result):
            if generate_galaxy_result.is_error:
                self.app.callbacks.on_error(generate_galaxy_result.content)
                return
            galaxy = generate_galaxy_result.content
            all_systems = 'Systems:'
            for system in galaxy.systems:
                all_systems += '\n%s' % system
            self.app.callbacks.on_output(all_systems)
        self.app.galaxy_generator.generate(on_generate_galaxy, seed, 0)

    # Shared