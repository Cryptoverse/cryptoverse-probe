from galaxy_services.galaxy_handlers.debug_galaxy import DebugGalaxy
import util

class GalaxyGenerator(object):

    def __init__(self):
        self.weighted_handlers = [
            (255, DebugGalaxy())
        ]
    
    def generate(self, done, block_hash, count):
        galaxy_type = int(util.sha256("galaxy_type+%s" % block_hash)[:2], 16)
        for weighted_handler in self.weighted_handlers:
            weight, handler = weighted_handler
            if weight < galaxy_type:
                continue
            handler.generate(done, block_hash, count, count + 1)
            break