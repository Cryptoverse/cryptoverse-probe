from models.base_model import BaseModel

class NodeModel(BaseModel):

    def __init__(self):
        super(NodeModel, self).__init__()
        self.url = None
        self.last_response_datetime = None
        self.last_request_datetime = None
        self.events_limit_max = None
        self.blocks_limit_max = None
        self.blacklisted = None
        self.blacklist_reason = None

    def get_active(self):
        return (self.last_response_datetime != 0 and 
                self.last_request_datetime <= self.last_response_datetime)

    def get_pretty_content(self):
        content = super(NodeModel, self).get_pretty_content()
        content += self.get_pretty_entry('url', self.url)
        content += self.get_pretty_entry('last_response_datetime', self.last_response_datetime)
        content += self.get_pretty_entry('last_request_datetime', self.last_request_datetime)
        content += self.get_pretty_entry('events_limit_max', self.events_limit_max)
        content += self.get_pretty_entry('blocks_limit_max', self.blocks_limit_max)
        content += self.get_pretty_entry('blacklisted', self.blacklisted)
        content += self.get_pretty_entry('blacklist_reason', self.blacklist_reason)
        return content