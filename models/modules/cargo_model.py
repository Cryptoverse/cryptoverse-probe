from models.modules.base_module_model import BaseModuleModel

class CargoModel(BaseModuleModel):

    def __init__(self, **kwargs):
        super(CargoModel, self).__init__(module_type = 'cargo', **kwargs)
        self.contents = kwargs.get('contents')
        self.mass_limit = kwargs.get('mass_limit')

    def get_json(self):
        result = super(CargoModel, self).get_json()
        result['contents'] = self.contents.get_json()
        result['mass_limit'] = self.mass_limit
        return result

    def get_concat(self):
        if self.contents is None:
            raise ValueError('contents cannot be None')
        result = super(CargoModel, self).get_concat()
        result += self.contents.get_concat()
        return result
