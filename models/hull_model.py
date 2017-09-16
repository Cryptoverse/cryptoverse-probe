from models.base_model import BaseModel

class HullModel(BaseModel):

    def __init__(self, **kwargs):
        super(HullModel, self).__init__()
        self.hash = kwargs.get('hash')
        self.fleet = kwargs.get('fleet')
        self.mass_limit = kwargs.get('mass_limit')

    def get_pretty_content(self):
        content = super(HullModel, self).get_pretty_content()
        content += self.get_pretty_entry('hash', self.hash)
        content += self.get_pretty_entry('fleet', self.fleet) 
        content += self.get_pretty_entry('mass_limit', self.mass_limit) 
        return content