from models.base_model import BaseModel

class BlockModel(BaseModel):

    def __init__(self):
        super(BlockModel, self).__init__()
        self.hash = None
        self.previous_hash = None
        self.previous_id = None
        self.height = None
        self.size = None
        self.version = None
        self.difficulty = None
        self.time = None
        self.interval_id = None
        self.root_id = None
        self.chain = None

    def get_pretty_content(self):
        content = super(BlockModel, self).get_pretty_content()
        content += self.get_pretty_entry('hash', self.hash)
        content += self.get_pretty_entry('previous_hash', self.previous_hash)
        content += self.get_pretty_entry('previous_id', self.previous_id)
        content += self.get_pretty_entry('height', self.height)
        content += self.get_pretty_entry('size', self.size)
        content += self.get_pretty_entry('version', self.version)
        content += self.get_pretty_entry('difficulty', self.difficulty)
        content += self.get_pretty_entry('time', self.time)
        content += self.get_pretty_entry('interval_id', self.interval_id)
        content += self.get_pretty_entry('root_id', self.root_id)
        content += self.get_pretty_entry('chain', self.chain)
        
        return content