class BaseDatabaseHandler(object):

    def __init__(self, model_type):
        self.model_type = model_type

    def initialize(self, done, rebuild=False):
        raise NotImplementedError

    def write(self, model, done=None):
        raise NotImplementedError

    def read(self, model_id, done):
        raise NotImplementedError

    def read_all(self, ids, done):
        """Reads all models with matching ids, or all models if None is provided for ids.

        Args:
            ids (list): List of all ids to search for, or None if all models should be retrieved.
            done (lambda): Callback once records have been retrieved.
        """
        raise NotImplementedError

    def drop(self, model, done=None):
        raise NotImplementedError

    def sync(self, model, done):
        raise NotImplementedError

    def count(self, done):
        raise NotImplementedError