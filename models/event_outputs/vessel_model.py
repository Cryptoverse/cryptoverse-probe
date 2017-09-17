from models.base_model import BaseModel

class VesselModel(BaseModel):

    def __init__(self, **kwargs):
        super(VesselModel, self).__init__()
        self.blueprint = kwargs.get('blueprint')
        self.modules = kwargs.get('modules')

    def get_concat(self):
        if self.blueprint is None:
            raise ValueError('blueprint cannot be None')
        result = self.blueprint
        for current_module in sorted(self.modules, key=lambda x: x.index):
            result += current_module.get_concat()
        return result

    def get_pretty_content(self):
        content = super(VesselModel, self).get_pretty_content()
        content += self.get_pretty_entry('blueprint', self.blueprint)
        content += self.get_pretty_entry('modules', self.modules)
        return content