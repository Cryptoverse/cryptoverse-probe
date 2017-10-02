from models.event_outputs.base_model_model import BaseModelModel
from models.modules.cargo_model import CargoModel
from models.modules.jump_drive_model import JumpDriveModel
import util

class VesselModel(BaseModelModel):

    MODEL_TYPE = 'vessel'

    def __init__(self, **kwargs):
        super(VesselModel, self).__init__(self.MODEL_TYPE)
        self.blueprint = kwargs.get('blueprint')
        self.modules = kwargs.get('modules')


    def get_concat(self):
        if self.blueprint is None:
            raise ValueError('blueprint cannot be None')
        result = self.blueprint
        for current_module in sorted(self.modules, key=lambda x: x.index):
            result += current_module.get_concat()
        return result


    def get_json(self):
        result = super(VesselModel, self).get_json()
        modules = []
        if self.modules is not None:
            for module in self.modules:
                modules.append(module.get_json())
        result['blueprint'] = self.blueprint
        result['modules'] = modules
        return result


    def set_from_json(self, vessel_json):
        self.blueprint = vessel_json['blueprint']
        self.modules = []
        for module_json in vessel_json['modules']:
            module_type = module_json['type']
            module = None
            if module_type == 'cargo':
                module = CargoModel()
            elif module_type == 'jump_drive':
                module = JumpDriveModel()
            else:
                ValueError('unrecognized module type %s' % module_type)
            module.set_from_json(module_json)
            self.modules.append(module)


    def get_pretty_content(self):
        content = super(VesselModel, self).get_pretty_content()
        content += self.get_pretty_entry('blueprint', self.blueprint)
        content += self.get_pretty_entry('modules', self.modules)
        return content