from models.base_model import BaseModel

class SystemModel(BaseModel):

    def __init__(self):
        super(SystemModel, self).__init__()
        self.hash = None
        self.galaxy_count = 0
        self.x = 0
        self.y = 0
        self.z = 0


    def get_location(self):
        return '%s-%s' % (self.galaxy_count, self.hash)


    def get_pretty_content(self):
        content = super(SystemModel, self).get_pretty_content()
        content += self.get_pretty_entry('hash', self.hash)
        content += self.get_pretty_entry('position', "( %s, %s, %s )" % (self.x, self.y, self.z))
        return content