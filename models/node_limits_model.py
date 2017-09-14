from models.base_model import BaseModel

class NodeLimitsModel(BaseModel):

    def __init__(self):
        super(NodeLimitsModel, self).__init__()
        self.events_limit_max = None
        self.blocks_limit_max = None

    def get_pretty_content(self):
        content = super(NodeLimitsModel, self).get_pretty_content()
        content += self.get_pretty_entry('events_limit_max', self.events_limit_max)
        content += self.get_pretty_entry('blocks_limit_max', self.blocks_limit_max)
        return content