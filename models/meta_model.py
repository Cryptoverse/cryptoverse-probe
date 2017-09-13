from models.base_model import BaseModel

class MetaModel(BaseModel):

    def __init__(self):
        super(MetaModel, self).__init__()
        self.text_content = None

    def get_pretty_content(self):
        content = super(MetaModel, self).get_pretty_content()
        content += self.get_pretty_entry('text_content', self.text_content)
        return content