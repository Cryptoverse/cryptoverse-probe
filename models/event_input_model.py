from models.base_model import BaseModel

class EventInputModel(BaseModel):

    def __init__(self):
        super(EventInputModel, self).__init__()
        self.index = None
        self.hash = None


    def get_concat(self):
        if self.hash is None:
            raise ValueError('hash cannot be None')
        return self.hash


    def get_json(self):
        return {
            'index': self.index,
            'hash': self.hash
        }


    def set_from_json(self, event_input_json):
        self.index = event_input_json['index']
        self.hash = event_input_json['hash']


    def get_pretty_content(self):
        content = super(EventInputModel, self).get_pretty_content()
        content += self.get_pretty_entry('index', self.index)
        content += self.get_pretty_entry('hash', self.hash)
        return content