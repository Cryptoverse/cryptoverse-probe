from models.resource_model import ResourceModel
from models.hull_model import HullModel
from models.modules.cargo_model import CargoModel
from models.modules.jump_drive_model import JumpDriveModel
from models.event_outputs.vessel_model import VesselModel

class BlueprintService(object):

    def __init__(self, app):
        self.app = app

    def get_default_hull(self):
        return HullModel(
            hash = '4a28968dc2cdcdcc4d02d891fb98b11755ee6bf027d49bb5f6c0ab249a37ab68',
            mass_limit = 5000
        )
    
    def get_default_cargo(self):
        return CargoModel(
            hash = '6b6b84a56c470a6bf598e661ac81f106b509c52e73715529311536014fbe45cf',
            health_limit = 10,
            mass = 25,
            mass_limit = 1000
        )
    
    def get_default_jump_drive(self):
        return JumpDriveModel(
            hash = '75e23c09fc113178bddb3eb695a7ade5fab6d7246c5aea71138cdd15472273a1',
            health_limit = 10,
            mass = 25,
            distance_scalar = 1.0,
            fuel_scalar = 1.0,
            mass_limit = 5000
        )

    def get_default_vessel(self):
        hull = self.get_default_hull()
        cargo = self.get_default_cargo()
        cargo.index = 0
        cargo.contents = ResourceModel()
        cargo.contents.fuel = cargo.mass_limit

        jump_drive = self.get_default_jump_drive(),
        jump_drive.index = 1

        return VesselModel(
            hash = hull.hash,
            modules = [
                cargo,
                jump_drive
            ]
        )
