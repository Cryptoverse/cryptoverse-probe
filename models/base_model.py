class BaseModel(object):

    PRETTY_WRAPPER = '%s : {\n%s}'

    def __init__(self):
        self.id = None

    def __str__(self):
        return self.get_pretty()

    def get_pretty_entry(self, field, value, indent=1):
        indents = '\t' * indent
        return '%s%s : %s\n' % (indents, field, value)

    def get_pretty_content(self):
        return self.get_pretty_entry('id', self.id)

    def get_pretty(self):
        return self.PRETTY_WRAPPER % (self.__class__.__name__, self.get_pretty_content())