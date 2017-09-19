from models.base_model import BaseModel
import util

class EventModel(BaseModel):

    def __init__(self):
        super(EventModel, self).__init__()
        self.index = 0
        self.hash = None
        self.fleet = None
        self.event_type = None
        self.inputs = []
        self.outputs = []
        self.signature = None

    def assign_hash(self):
        """Calculates and assigns the hash of this event.

        Returns:
            str: Sha256 hash of this event.
        """
        self.hash = util.sha256(self.get_concat())
        return self.hash

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

    def get_json(self):
        inputs = []
        if self.inputs is not None:
            for current_input in self.inputs:
                inputs.append(current_input.get_json())

        outputs = []
        if self.outputs is not None:
            for current_output in self.outputs:
                outputs.append(current_output.get_json())

        return {
            'index': self.index,
            'fleet_hash': self.fleet.get_hash(),
            'fleet_key': self.fleet.public_key,
            'hash': self.hash,
            'inputs': inputs,
            'outputs': outputs,
            'signature': self.signature,
            'type': self.event_type
        }


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