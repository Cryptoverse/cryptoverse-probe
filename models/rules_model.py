import math
import numpy
from models.base_model import BaseModel
import util

class RulesModel(BaseModel):

    maximum_nonce = 2147483647
    empty_target = '0000000000000000000000000000000000000000000000000000000000000000'

    def __init__(self):
        super(RulesModel, self).__init__()
        self.version = None
        self.jump_cost_min = None
        self.jump_cost_max = None
        self.jump_distance_max = None
        self.difficulty_fudge = None
        self.difficulty_start = None
        self.difficulty_interval = None
        self.difficulty_duration = None
        self.cartesian_digits = None
        self.probe_reward = None


    def get_maximum_target(self):
        maximum_target = '00000000ffffffffffffffffffffffffffffffffffffffffffffffffffffffff'
        if self.difficulty_fudge == 0:
            return maximum_target
        if not 0 <= self.difficulty_fudge <= 8:
            raise Exception('DIFFICULTY_FUDGE must be a value from 0 to 8 (inclusive)')
        return maximum_target[self.difficulty_fudge:] + maximum_target[:self.difficulty_fudge]


    def is_genesis_block(self, sha):
        """Checks if the provided hash could only belong to the parent of the genesis block.

        Args:
            sha (str): Hash to check.

        Results:
            bool: True if equal to the hash of the parent of the genesis block's parent.
        """
        return sha == self.empty_target

    def difficulty_to_hex(self, difficulty):
        """Converts a packed int representation of difficulty to its packed hex format.
        
        Args:
            difficulty (int): Packed int format of difficulty.
        
        Returns:
            str: Packed hex format of difficulty, stripped of its leading 0x.
        """
        return hex(difficulty)[2:]


    def difficulty_from_hex(self, difficulty):
        """Takes a hex string of difficulty, missing the 0x, and returns the integer from of difficulty.
        
        Args:
            difficulty (str): Packed hex format of difficulty.
        
        Returns:
            int: Packed int format of difficulty.
        """
        return int(difficulty, 16)


    def difficulty_from_target(self, target):
        """Calculates the difficulty this target is equal to.
        
        Args:
            target (str): Hex target, stripped of its leading 0x.
        
        Returns:
            str: Packed hex difficulty of the target, stripped of its leading 0x.
        """
        # TODO: Cleanup shitwise operators that use string transformations, they're ugly... though they do work...
        stripped = target.lstrip('0')

        # If we stripped too many zeros, add one back.
        if len(stripped) % 2 == 0:
            stripped = '0' + stripped

        count = len(stripped) / 2
        stripped = stripped[:6]

        # If we're past the max value allowed for the mantissa, truncate it further and increase the exponent.
        if 0x7fffff < int(stripped, 16):
            stripped = '00' + stripped[0:4]
            count += 1

        result = hex(count)[2:] + stripped

        # Negative number switcharoo
        if 0x00800000 & int(result, 16):
            result = hex(count + 1)[2:] + '00' + stripped[:4]
        # # Lazy max number check...
        # if 0x1d00ffff < int(result, 16):
        #     result = '1d00ffff'
        return result

    def is_difficulty_changing(self, height):
        """Checks if it's time to recalculate difficulty.
        
        Args:
            height (int): Height of an entry in the chain.
        
        Returns:
            bool: True if a difficulty recalculation should take place.
        """
        return (height % self.difficulty_interval) == 0

    def calculate_difficulty(self, difficulty, duration):
        """Takes the packed integer difficulty and the duration of the last interval to calculate the new difficulty.
        
        Args:
            difficulty (int): Packed int format of the last difficulty.
            duration (int): Seconds elapsed since the last time difficulty was calculated.
        
        Returns:
            int: Packed int format of the next difficulty.
        """
        if duration < self.difficulty_duration / 4:
            duration = self.difficulty_duration / 4
        elif duration > self.difficulty_duration * 4:
            duration = self.difficulty_duration * 4

        limit = long(self.get_maximum_target(), 16)
        result = long(self.unpack_bits(difficulty), 16)
        result *= duration
        result /= self.difficulty_duration

        if limit < result:
            result = limit

        return self.difficulty_from_hex(self.difficulty_from_target(hex(result)[2:]))


    def unpack_bits(self, difficulty, strip=False):
        """Unpacks int difficulty into a target hex.

        Args:
            difficulty (int): Packed int representation of a difficulty.
        
        Returns:
            str: Hex value of a target hash equal to this difficulty, stripped of its leading 0x.
        """
        if not isinstance(difficulty, (int, long)):
            raise TypeError('difficulty is not int')
        sha = self.difficulty_to_hex(difficulty)
        digit_count = int(sha[:2], 16)

        if digit_count == 0:
            digit_count = 3

        digits = []
        if digit_count == 29:
            digits = [sha[4:6], sha[6:8]]
        else:
            digits = [sha[2:4], sha[4:6], sha[6:8]]

        digit_count = min(digit_count, 28)
        significant_count = len(digits)

        leading_padding = 28 - digit_count
        trailing_padding = 28 - (leading_padding + significant_count)

        base256 = ''

        for i in range(0, leading_padding + 4):
            base256 += '00'
        for i in range(0, significant_count):
            base256 += digits[i]
        for i in range(0, trailing_padding):
            base256 += '00'

        if 0 < self.difficulty_fudge:
            base256 = base256[self.difficulty_fudge:] + base256[:self.difficulty_fudge]
        return base256.rstrip('0') if strip else base256

    def get_jump_cost(self, origin_hash, destination_hash, count=None):
        """Gets the floating point scalar for the number of ships that will be lost in this jump.

        Args:
            origin_hash (str): The starting hash of the jump.
            destination_hash (str): The ending hash of the jump.
            count (int): The number of ships in the jump.
        
        Returns:
            float: A scalar value of the ships lost in the jump.
        """
        distance = self.get_distance(origin_hash, destination_hash)
        if self.jump_distance_max <= distance:
            return self.jump_cost_max if count is None else int(math.ceil(self.jump_cost_max * count))
        # Scalar is x^2
        scalar = math.sqrt(distance / self.jump_distance_max)
        cost_range = 1.0 - ((1.0 - self.jump_cost_max) + self.jump_cost_min)
        scalar = self.jump_cost_min + (cost_range * scalar)
        return scalar if count is None else int(math.ceil(scalar * count))

    def get_cartesian_minimum(self):
        """Gets the (x, y, z) position of the minimum possible system.
        
        Returns:
            array: A list containing the (x, y, z) position.
        """
        return numpy.array([0, 0, 0])


    def get_cartesian_maximum(self):
        """Gets the (x, y, z) position of the maximum possible system.
        
        Returns:
            array: A list containing the (x, y, z) position.
        """
        max_value = pow(16, self.cartesian_digits)
        return numpy.array([max_value, max_value, max_value])

    def get_cartesian(self, system_hash):
        """Gets the (x, y, z) position of the specified system.

        Args:
            system_hash (str): The system's Sha256 hash.
        
        Returns:
            numpy.array: A list containing the (x, y, z) position.
        """
        cartesian_hash = util.sha256('%s%s' % ('cartesian', system_hash))
        digits = self.cartesian_digits
        total_digits = digits * 3
        cartesian = cartesian_hash[-total_digits:]
        return numpy.array([int(cartesian[:digits], 16), int(cartesian[digits:-digits], 16), int(cartesian[(2*digits):], 16)])


    def get_distance(self, origin_hash, destination_hash):
        """Gets the distance between the specified systems in cartesian space.

        Args:
            origin_hash (str): The origin system's Sha256 hash.
            destination_hash (str): The destination system's Sha256 hash.
        
        Returns:
            float: The distance between the two systems.
        """
        origin_pos = self.get_cartesian(origin_hash)
        destination_pos = self.get_cartesian(destination_hash)
        return int(math.ceil(numpy.linalg.norm(origin_pos - destination_pos)))

    def is_match(self, other):
        return (self.version == other.version and
                self.jump_cost_min == other.jump_cost_min and
                self.jump_cost_max == other.jump_cost_max and
                self.jump_distance_max == other.jump_distance_max and
                self.difficulty_fudge == other.difficulty_fudge and
                self.difficulty_start == other.difficulty_start and
                self.difficulty_interval == other.difficulty_interval and
                self.difficulty_duration == other.difficulty_duration and
                self.cartesian_digits == other.cartesian_digits and
                self.probe_reward == other.probe_reward)

    def get_pretty_content(self):
        content = super(RulesModel, self).get_pretty_content()
        content += self.get_pretty_entry('version', self.version)
        content += self.get_pretty_entry('jump_cost_min', self.jump_cost_min)
        content += self.get_pretty_entry('jump_cost_max', self.jump_cost_max)
        content += self.get_pretty_entry('jump_distance_max', self.jump_distance_max)
        content += self.get_pretty_entry('difficulty_fudge', self.difficulty_fudge)
        content += self.get_pretty_entry('difficulty_start', self.difficulty_start)
        content += self.get_pretty_entry('difficulty_interval', self.difficulty_interval)
        content += self.get_pretty_entry('difficulty_duration', self.difficulty_duration)
        content += self.get_pretty_entry('cartesian_digits', self.cartesian_digits)
        content += self.get_pretty_entry('probe_reward', self.probe_reward)
        return content