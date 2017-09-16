from models.base_model import BaseModel

class EventModel(BaseModel):

    def __init__(self):
        super(EventModel, self).__init__()
        self.index = 0
        self.hash = None
        self.fleet = None
        self.event_type = None
        self.inputs = None
        self.outputs = None
        self.signature = None

    def get_pretty_content(self):
        content = super(EventModel, self).get_pretty_content()
        content += self.get_pretty_entry('index', self.index)
        content += self.get_pretty_entry('hash', self.hash)
        content += self.get_pretty_entry('fleet', self.fleet)
        content += self.get_pretty_entry('event_type', self.event_type)
        content += self.get_pretty_entry('inputs', self.inputs)
        content += self.get_pretty_entry('outputs', self.outputs)
        content += self.get_pretty_entry('signature', self.signature)
        return content