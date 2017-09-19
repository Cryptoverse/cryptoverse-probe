from models.base_model import BaseModel

class ResourceModel(BaseModel):

    def __init__(self):
        super(ResourceModel, self).__init__()
        self.fuel = None

    def get_concat(self):
        result = ''
        if 0 < self.fuel:
            result += str(self.fuel)
        return result

    def get_json(self):
        return {
            'fuel': self.fuel
        }

    def get_pretty_content(self):
        content = super(ResourceModel, self).get_pretty_content()
        content += self.get_pretty_entry('fuel', self.fuel)
        return content