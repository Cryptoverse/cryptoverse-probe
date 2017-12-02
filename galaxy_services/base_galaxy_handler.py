from models.galaxy_model import GalaxyModel
from models.system_model import SystemModel
from callback_result import CallbackResult
import util

class BaseGalaxyHandler(object):

    def __init__(self, galaxy_name):
        self.galaxy_name = galaxy_name

    def generate(self, done, seed, distance_multiplier):
        galaxy = GalaxyModel()
        galaxy.hash = util.sha256(seed)
        galaxy_cartesian = util.sha256("cartesian+%s" % seed)
        galaxy.x = int(galaxy_cartesian[:2], 16) * distance_multiplier
        galaxy.y = int(galaxy_cartesian[2:4], 16) * distance_multiplier
        galaxy.z = int(galaxy_cartesian[4:6], 16) * distance_multiplier
        system_count = 2 + int(util.sha256("system_count+%s" % seed)[:1], 16)
        for x in range(0, system_count):
            system = SystemModel()
            system.hash = util.sha256("system+%s+%s" % (x, seed))
            self.generate_system(system)
            galaxy.systems.append(system)
        done(CallbackResult(galaxy))

    def generate_system(self, system):
        raise NotImplementedError