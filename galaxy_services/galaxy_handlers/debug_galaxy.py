from galaxy_services.base_galaxy_handler import BaseGalaxyHandler
import util

class DebugGalaxy(BaseGalaxyHandler):
    
    def __init__(self):
        super(DebugGalaxy, self).__init__(
            'debug'
        )

    def generate_system(self, system):
        system_cartesian = util.sha256("cartesian+%s" % system.hash)
        system.x = int(system_cartesian[:2], 16)
        system.y = int(system_cartesian[2:4], 16)
        system.z = int(system_cartesian[4:6], 16)

    # def get_cartesian(system_hash):
    #     """Gets the (x, y, z) position of the specified system.
    #     Args:
    #         system_hash (str): The system's Sha256 hash.
        
    #     Returns:
    #         numpy.array: A list containing the (x, y, z) position.
    #     """
    #     cartesian_hash = sha256('%s%s' % ('cartesian', system_hash))
    #     digits = cartesianDigits()
    #     total_digits = digits * 3
    #     cartesian = cartesian_hash[-total_digits:]
    #     return numpy.array([int(cartesian[:digits], 16), int(cartesian[digits:-digits], 16), int(cartesian[(2*digits):], 16)])
