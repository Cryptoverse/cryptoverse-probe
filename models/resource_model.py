from models.base_model import BaseModel

class ResourceModel(BaseModel):

    def __init__(self):
        super(ResourceModel, self).__init__()
        self.fuel = None


    def get_pretty_content(self):
        content = super(ResourceModel, self).get_pretty_content()
        content += self.get_pretty_entry('fuel', self.fuel)
        return content