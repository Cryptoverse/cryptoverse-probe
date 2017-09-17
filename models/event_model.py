from models.base_model import BaseModel
import util

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

    def get_concat(self):
        if self.fleet is None:
            raise ValueError('fleet cannot be None')
        if self.fleet.public_key is None:
            raise ValueError('fleet.public_key cannot be None')
        if self.event_type is None:
            raise ValueError('event_type cannot be None')
        result = '%s%s%s' % (self.fleet.get_hash(), self.fleet.public_key, self.event_type)
        for current_input in sorted(self.inputs, key=lambda x: x.index):
            result += current_input.get_concat()
        for current_output in sorted(self.outputs, key=lambda x: x.index):
            result += current_output.get_concat()
        return result

    def generate_signature(self, private_key):
        if self.fleet is None:
            raise ValueError('fleet cannot be None')
        if self.fleet.public_key is None:
            raise ValueError('fleet.public_key cannot be None')
        concat = self.get_concat()
        self.signature = util.rsa_sign(private_key, concat)

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