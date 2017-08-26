from models.base_model import BaseModel

class CommandHistoryModel(BaseModel):

    def __init__(self):
        super(CommandHistoryModel, self).__init__()
        self.command = None
        self.time = None
        self.session_order = None

    def get_pretty_content(self):
        content = super(CommandHistoryModel, self).get_pretty_content()
        content += self.get_pretty_entry('command', self.command)
        content += self.get_pretty_entry('time', self.time)
        content += self.get_pretty_entry('session_order', self.session_order) 
        return content