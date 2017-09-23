from models.base_model import BaseModel
from models.fleet_model import FleetModel
from models.event_outputs.vessel_model import VesselModel

class EventOutputModel(BaseModel):

    def __init__(self):
        super(EventOutputModel, self).__init__()
        self.index = None
        self.fleet = None
        self.output_type = None
        self.key = None
        self.location = None
        self.model = None

    def get_concat(self):
        if self.fleet is None:
            raise ValueError('fleet cannot be None')
        if self.fleet.public_key is None:
            raise ValueError('fleet.public_key cannot be None')
        if self.model is None:
            raise ValueError('model cannot be None')
        if self.output_type is None:
            raise ValueError('output_type cannot be None')
        if self.key is None:
            raise ValueError('key cannot be None')
        serialized_location = '' if self.location is None else self.location
        result = '%s%s%s%s' % (self.output_type, self.fleet.get_hash(), self.key, serialized_location)
        result += self.model.get_concat()
        return result

    def get_json(self):
        return {
            'index': self.index,
            'model': self.model.get_json(),
            'fleet_hash': self.fleet.get_hash(),
            'key': self.key,
            'location': self.location,
            'type': self.output_type
        }


    def set_from_json(self, event_output_json):
        self.index = event_output_json['index']
        self.fleet = FleetModel()
        self.fleet.public_key = event_output_json['fleet_hash']
        self.output_type = event_output_json['type']
        self.key = event_output_json['key']
        self.location = event_output_json['location']
        output_model_json = event_output_json['model']
        if output_model_json is None:
            ValueError('model cannot be None')
        model_type = output_model_json['type']
        if model_type == 'vessel':
            self.model = VesselModel()
            self.model.set_from_json(output_model_json)
        else:
            ValueError('model type %s not recognized' % model_type)


    def get_pretty_content(self):
        content = super(EventOutputModel, self).get_pretty_content()
        content += self.get_pretty_entry('index', self.index)
        content += self.get_pretty_entry('fleet', self.fleet)
        content += self.get_pretty_entry('output_type', self.output_type)
        content += self.get_pretty_entry('key', self.key)
        content += self.get_pretty_entry('location', self.location)
        content += self.get_pretty_entry('model', self.model)
        return content