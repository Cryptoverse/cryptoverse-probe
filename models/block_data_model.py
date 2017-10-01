import json
from models.base_model import BaseModel

class BlockDataModel(BaseModel):

    def __init__(self):
        super(BlockDataModel, self).__init__()
        self.block_id = None
        self.previous_block_id = None
        self.uri = None
        # This will probably be replaced eventually...
        self.data = None

    def get_json(self):
        if self.uri == 'data_json':
            return json.loads(self.data)
        else:
            raise NotImplementedError

    def get_pretty_content(self):
        content = super(BlockDataModel, self).get_pretty_content()
        content += self.get_pretty_entry('block_id', self.block_id)
        content += self.get_pretty_entry('previous_block_id', self.previous_block_id)
        content += self.get_pretty_entry('uri', self.uri)
        content += self.get_pretty_entry('data', self.data)
        
        return content