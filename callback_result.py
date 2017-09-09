class CallbackResult(object):

    GENERIC_ERROR = 'Something went wrong'

    def __init__(self, content=None, is_success=True):
        self.content = content
        self.is_success = is_success
        self.is_error = not is_success
