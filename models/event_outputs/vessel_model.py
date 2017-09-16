from models.base_model import BaseModel

class VesselModel(BaseModel):

    def __init__(self, **kwargs):
        super(VesselModel, self).__init__()
        self.blueprint = kwargs.get('blueprint')
        self.modules = kwargs.get('modules')

    def get_pretty_content(self):
        content = super(VesselModel, self).get_pretty_content()
        content += self.get_pretty_entry('blueprint', self.blueprint)
        content += self.get_pretty_entry('modules', self.modules)
        return content