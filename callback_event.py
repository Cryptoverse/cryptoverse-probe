class CallbackEvent():

    def __init__(self):
        self.handlers = set()

    def add(self, handler):
        self.handlers.add(handler)
        return self

    def remove(self, handler):
        try:
            self.handlers.remove(handler)
        except:
            raise ValueError('Unable to find existing handler')
        return self

    def call(self, *args, **kargs):
        for handler in self.handlers:
            handler(*args, **kargs)

    def count(self):
        return len(self.handlers)

    __iadd__ = add
    __isub__ = remove
    __call__ = call
    __len__  = count