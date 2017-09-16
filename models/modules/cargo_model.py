from models.modules.base_module_model import BaseModuleModel

class CargoModel(BaseModuleModel):

    def __init__(self, **kwargs):
        super(CargoModel, self).__init__(module_type = 'cargo', **kwargs)
        self.contents = kwargs.get('contents')
        self.mass_limit = kwargs.get('mass_limit')