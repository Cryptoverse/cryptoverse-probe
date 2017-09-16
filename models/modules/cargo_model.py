from models.modules.base_module_model import BaseModuleModel

class CargoModel(BaseModuleModel):

    def __init__(self):
        super(CargoModel, self).__init__('cargo')
        self.contents = None