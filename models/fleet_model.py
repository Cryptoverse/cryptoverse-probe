from models.base_model import BaseModel
import util

class FleetModel(BaseModel):

    def __init__(self):
        super(FleetModel, self).__init__()
        self.name = None
        self.public_key = None

    def set_from_account(self, account):
        self.name = account.name
        self.public_key = account.public_key

    def get_hash(self):
        return util.sha256(self.public_key)

    def get_fleet_name(self):
        return '(%s)' % util.get_shortened_hash(self.get_hash(), strip_zeros=False)

    def get_pretty_content(self):
        content = super(FleetModel, self).get_pretty_content()
        content += self.get_pretty_entry('name', self.name)
        content += self.get_pretty_entry('public_key', self.public_key) 
        return content
