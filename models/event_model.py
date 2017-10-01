from models.base_model import BaseModel
from models.event_input_model import EventInputModel
from models.event_output_model import EventOutputModel
from models.fleet_model import FleetModel
import util

class EventModel(BaseModel):

    def __init__(self):
        super(EventModel, self).__init__()
        self.index = 0
        self.hash = None
        self.key = None
        self.version = None
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
        if self.key is None:
            raise ValueError('key cannot be None')
        if self.version is None:
            raise ValueError('version cannot be None')
        result = '%s%s%s%s%s' % (self.version, self.key, self.fleet.get_hash(), self.fleet.public_key, self.event_type)
        for current_input in sorted(self.inputs, key=lambda x: x.index):
            # Unless more than just an input hash is used, there's no need to assign hashes.
            result += current_input.get_concat()
        for current_output in sorted(self.outputs, key=lambda x: x.index):
            # Outputs are more complicated, so we hash them first.
            result += current_output.assign_hash()
        return result

    def generate_signature(self, private_key):
        if self.fleet is None:
            raise ValueError('fleet cannot be None')
        if self.fleet.public_key is None:
            raise ValueError('fleet.public_key cannot be None')
        if self.hash is None:
            raise ValueError('hash cannot be None')
        self.signature = util.rsa_sign(private_key, self.hash)

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
            'key': self.key,
            'version': self.version,
            'inputs': inputs,
            'outputs': outputs,
            'signature': self.signature,
            'type': self.event_type
        }


    def set_from_json(self, event_json):
        self.index = event_json['index']
        self.hash = event_json['hash']
        self.key = event_json['key']
        self.version = event_json['version']
        self.fleet = FleetModel()
        self.fleet.public_key = event_json['fleet_key']
        self.event_type = event_json['type']
        self.signature = event_json['signature']
        self.inputs = []
        for event_input in event_json['inputs']:
            current_input = EventInputModel()
            current_input.set_from_json(event_input)
            self.inputs.append(current_input)
        self.outputs = []
        for event_output in event_json['outputs']:
            current_output = EventOutputModel()
            current_output.set_from_json(event_output)
            self.outputs.append(current_output)


    def get_pretty_content(self):
        content = super(EventModel, self).get_pretty_content()
        content += self.get_pretty_entry('index', self.index)
        content += self.get_pretty_entry('hash', self.hash)
        content += self.get_pretty_entry('key', self.key)
        content += self.get_pretty_entry('version', self.version)
        content += self.get_pretty_entry('fleet', self.fleet)
        content += self.get_pretty_entry('event_type', self.event_type)
        content += self.get_pretty_entry('inputs', self.inputs)
        content += self.get_pretty_entry('outputs', self.outputs)
        content += self.get_pretty_entry('signature', self.signature)
        return content