from models.base_model import BaseModel

# Introducing: The silliest name for a model.
class BaseModelModel(BaseModel):

    def __init__(self, model_type):
        super(BaseModelModel, self).__init__()
        self.model_type = model_type


    def get_concat(self):
        raise NotImplementedError


    def get_json(self):
        return { 'type': self.model_type }


    def set_from_json(self, model_json):
        raise NotImplementedError


    def get_pretty_content(self):
        content = super(BaseModelModel, self).get_pretty_content()
        content += self.get_pretty_entry('model_type', self.model_type)
        return content