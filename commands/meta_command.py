from commands.base_command import BaseCommand
from models.meta_model import MetaModel

class MetaCommand(BaseCommand):

    def __init__(self, app):
        super(MetaCommand, self).__init__(
            app, 
            'meta',
            description = 'Retrieves or sets the meta content included in probed blocks',
            parameter_usages = [
                'None: Retrieves the current meta content being included with probed blocks',
                '"-s <text>" sets a new meta content',
                '"-r" resets the meta content to nothing'
            ]
        )

    def on_command(self, *args):
        parameter_count = len(args)
        if parameter_count == 0:
            self.on_current_meta()
        elif args[0] == '-s':
            if parameter_count == 2:
                self.on_set_meta_text(args[1])
            else:
                raise ValueError('Invalid number of parameters for "-s"')
        elif args[0] == '-r':
            self.on_reset_meta()
        else:
            self.app.callbacks.on_error('Command "meta" does not recognize parameter "%s"' % args[0])
    # Events

    def on_current_meta(self):
        def on_find(find_result):
            if find_result.is_error or find_result.content.text_content is None:
                self.app.callbacks.on_output('No meta content set, use "meta -s <text>" to set one')
            else:
                self.app.callbacks.on_output('Meta content is "%s"' % find_result.content.text_content)
        self.app.database.meta.find_meta(on_find)

    def on_set_meta_text(self, text):
        def on_find(find_result):
            if find_result.is_error:
                model = MetaModel()
            else:
                model = find_result.content
            model.text_content = text

            def on_write(write_result):
                if write_result.is_error:
                    self.app.callbacks.on_error('Error writing meta: %s' % write_result.content)
                else:
                    self.app.callbacks.on_output('Meta content set to "%s"' % text)
            
            self.app.database.meta.write(model, on_write)

        self.app.database.meta.find_meta(on_find)
    
    def on_reset_meta(self):
        def on_find(find_result):
            if find_result.is_error:
                model = MetaModel()
            else:
                model = find_result.content
            model.text_content = None

            def on_write(write_result):
                if write_result.is_error:
                    self.app.callbacks.on_error('Error writing meta: %s' % write_result.content)
                else:
                    self.app.callbacks.on_output('Meta content reset to nothing')
            
            self.app.database.meta.write(model, on_write)

        self.app.database.meta.find_meta(on_find)