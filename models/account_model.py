from models.base_model import BaseModel
from models.fleet_model import FleetModel
import util

class AccountModel(BaseModel):

    def __init__(self):
        super(AccountModel, self).__init__()
        self.active = None
        self.name = None
        self.private_key = None
        self.public_key = None

    def get_fleet_name(self):
        return self.get_fleet().get_fleet_name()
    
    def get_fleet(self):
        fleet = FleetModel()
        fleet.set_from_account(self)
        return fleet

    def get_pretty_content(self):
        content = super(AccountModel, self).get_pretty_content()
        content += self.get_pretty_entry('active', self.active)
        content += self.get_pretty_entry('name', self.name)
        content += self.get_pretty_entry('private_key', self.private_key) 
        content += self.get_pretty_entry('public_key', self.public_key) 
        return content