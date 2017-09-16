from models.modules.base_module_model import BaseModuleModel

class JumpDriveModel(BaseModuleModel):

    def __init__(self):
        super(JumpDriveModel, self).__init__('jump_drive')
        # TODO: Jump distance, etc