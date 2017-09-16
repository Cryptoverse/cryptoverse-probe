from models.base_model import BaseModel

class BaseModuleModel(BaseModel):

    def __init__(self, **kwargs):
        super(BaseModuleModel, self).__init__()
        self.blueprint = kwargs.get('blueprint', None)
        self.index = kwargs.get('index', None)
        self.module_type = kwargs.get('module_type', None)
        self.delta = kwargs.get('delta', None)
        self.health = kwargs.get('health', None)
        

    def get_pretty_content(self):
        content = super(BaseModuleModel, self).get_pretty_content()
        content += self.get_pretty_entry('blueprint', self.blueprint)
        content += self.get_pretty_entry('index', self.index)
        content += self.get_pretty_entry('module_type', self.module_type)
        content += self.get_pretty_entry('delta', self.delta)
        content += self.get_pretty_entry('health', self.health)
        return content