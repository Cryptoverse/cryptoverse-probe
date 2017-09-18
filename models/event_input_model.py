from models.base_model import BaseModel

class EventInputModel(BaseModel):

    def __init__(self):
        super(EventInputModel, self).__init__()
        self.index = None
        self.key = None

    def get_concat(self):
        if self.key is None:
            raise ValueError('key cannot be None')
        return self.key

    def get_json(self):
        return {
            'index': self.index,
            'key': self.key
        }

    def get_pretty_content(self):
        content = super(EventInputModel, self).get_pretty_content()
        content += self.get_pretty_entry('index', self.index)
        content += self.get_pretty_entry('key', self.key)
        return content