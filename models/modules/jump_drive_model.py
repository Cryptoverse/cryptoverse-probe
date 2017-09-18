from models.modules.base_module_model import BaseModuleModel

class JumpDriveModel(BaseModuleModel):

    def __init__(self, **kwargs):
        super(JumpDriveModel, self).__init__(module_type = 'jump_drive', **kwargs)
        # TODO: Jump distance, etc

    def get_json(self):
        result = super(JumpDriveModel, self).get_json()
        # TODO: Add all the important stuff
        return result