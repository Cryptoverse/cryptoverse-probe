from commands.base_command import BaseCommand
from models.rules_model import RulesModel

class RulesCommand(BaseCommand):

    def __init__(self, app):
        super(RulesCommand, self).__init__(
            app, 
            'rules',
            description = 'Retrieves the active ruleset',
            parameter_usages = [
                'None: Retrieves the current rules'
            ],
            command_handlers = [
                self.get_handler(None, self.on_current_rules)
            ]
        )

    def on_current_rules(self):
        def on_find(find_result):
            if find_result.is_error or find_result.content is None:
                self.app.callbacks.on_output('No rules set, add a node to set them')
            else:
                self.app.callbacks.on_output('Rules:\n%s' % find_result.content)
        self.app.database.rules.find_rules(on_find)