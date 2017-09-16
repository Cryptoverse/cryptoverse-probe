from models.base_model import BaseModel

class EventOutputModel(BaseModel):

    def __init__(self):
        super(EventOutputModel, self).__init__()
        self.index = None
        self.fleet = None
        self.output_type = None
        self.key = None
        self.location = None
        self.model = None

    def get_pretty_content(self):
        content = super(EventOutputModel, self).get_pretty_content()
        content += self.get_pretty_entry('index', self.index)
        content += self.get_pretty_entry('fleet', self.fleet)
        content += self.get_pretty_entry('output_type', self.output_type)
        content += self.get_pretty_entry('key', self.key)
        content += self.get_pretty_entry('location', self.location)
        content += self.get_pretty_entry('model', self.model)
        return content