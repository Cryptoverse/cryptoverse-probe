from models.base_model import BaseModel

class GalaxyModel(BaseModel):

    def __init__(self):
        super(GalaxyModel, self).__init__()
        self.hash = None
        self.x = 0
        self.y = 0
        self.z = 0
        self.systems = []

    def get_pretty_content(self):
        content = super(GalaxyModel, self).get_pretty_content()
        content += self.get_pretty_entry('hash', self.hash)
        content += self.get_pretty_entry('position', "( %s, %s, %s )" % (self.x, self.y, self.z))
        return content