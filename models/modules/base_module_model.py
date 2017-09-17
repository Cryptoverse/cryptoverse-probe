from models.base_model import BaseModel

class BaseModuleModel(BaseModel):

    def __init__(self, **kwargs):
        super(BaseModuleModel, self).__init__()
        self.blueprint = kwargs.get('blueprint')
        self.index = kwargs.get('index')
        self.module_type = kwargs.get('module_type')
        self.delta = kwargs.get('delta')
        self.health = kwargs.get('health')

    def get_concat(self):
        if self.blueprint is None:
            raise ValueError('blueprint cannot be None')
        if self.delta is None:
            raise ValueError('delta cannot be None')
        if self.health is None:
            raise ValueError('health cannot be None')
        return '%s%s%s' % (self.blueprint, self.delta, self.health)

    def get_pretty_content(self):
        content = super(BaseModuleModel, self).get_pretty_content()
        content += self.get_pretty_entry('blueprint', self.blueprint)
        content += self.get_pretty_entry('index', self.index)
        content += self.get_pretty_entry('module_type', self.module_type)
        content += self.get_pretty_entry('delta', self.delta)
        content += self.get_pretty_entry('health', self.health)
        return content