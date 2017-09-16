from models.base_model import BaseModel

class VesselModel(BaseModel):

    def __init__(self):
        super(VesselModel, self).__init__()
        self.blueprint = None
        self.modules = None

    def get_pretty_content(self):
        content = super(VesselModel, self).get_pretty_content()
        content += self.get_pretty_entry('blueprint', self.blueprint)
        content += self.get_pretty_entry('modules', self.modules)
        return content