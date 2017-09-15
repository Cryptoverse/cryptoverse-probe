from commands.base_command import BaseCommand
from models.rules_model import RulesModel

class RulesCommand(BaseCommand):

    COMMAND_NAME = 'rules'

    def __init__(self, app):
        super(RulesCommand, self).__init__(
            app, 
            self.COMMAND_NAME,
            description = 'Retrieves the active ruleset',
            parameter_usages = [
                'None: Retrieves the current rules',
                '"-r" resets the rules to nothing'
            ],
            command_handlers = [
                self.get_handler(None, self.on_current_rules),
                self.get_handler('-r', self.on_remove_rules)
            ]
        )

    def on_current_rules(self):
        def on_find(find_result):
            if find_result.is_error or find_result.content is None:
                self.app.callbacks.on_output('No rules set, add a node to set them')
            else:
                self.app.callbacks.on_output('Rules:\n%s' % find_result.content)
        self.app.database.rules.find_rules(on_find)

    def on_remove_rules(self):
        def on_find(find_result):
            if find_result.is_error or find_result.content is None:
                self.app.callbacks.on_output('Rules already set to nothing')
                return
            def on_drop(drop_result):
                if drop_result.is_error:
                    self.app.callbacks.on_error(drop_result.content)
                    return
                self.app.callbacks.on_output('Rules set to nothing')
            self.app.database.rules.drop(find_result.content, on_drop)
        self.app.database.rules.find_rules(on_find)