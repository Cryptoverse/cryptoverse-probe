from models.base_model import BaseModel
from models.event_model import EventModel
import util

class BlockModel(BaseModel):

    def __init__(self):
        super(BlockModel, self).__init__()
        self.hash = None
        self.nonce = None
        self.previous_hash = None
        self.previous_id = None
        self.height = None
        self.size = None
        self.version = None
        self.difficulty = None
        self.time = None
        self.interval_id = None
        self.root_id = None
        self.chain = None
        self.events = []
        self.events_hash = None
        self.meta = None
        self.meta_hash = None

    def is_genesis(self, rules):
        return rules.is_genesis_block(self.previous_hash)

    def is_valid(self, difficulty_fudge=0, difficulty_target_stripped=None, leading_zeros=None):
        """Takes the unpacked form of difficulty and verifies that the hash is less than it.
        Args:
            unpacked_stripped (str): Unpacked target difficulty the provided SHA256 hash must meet.
            sha (str): Hex target to test, stripped of its leading 0x.
        """
        if difficulty_target_stripped is None:
            difficulty_target_stripped = self.get_difficulty_target(difficulty_fudge, True)

        if leading_zeros is None:
            leading_zeros = len(difficulty_target_stripped) - len(difficulty_target_stripped.lstrip('0'))

        try:
            for i in range(0, leading_zeros):
                if self.hash[i] != '0':
                    # Hash is greater than packed target
                    return False
            significant = self.hash[:len(difficulty_target_stripped)]
            if int(difficulty_target_stripped, 16) <= int(significant, 16):
                # Hash is greater than packed target
                return False
        except:
            raise Exception('Unable to cast to int from hexidecimal')
        return True

    def get_difficulty_hex(self):
        """Converts a packed int representation of difficulty to its packed hex format.
        
        Returns:
            str: Packed hex format of difficulty, stripped of its leading 0x.
        """
        if not isinstance(self.difficulty, (int, long)):
            raise TypeError('difficulty is not int')
        return hex(self.difficulty)[2:]

    def get_difficulty_target(self, difficulty_fudge=0, strip=False):
        """Unpacks difficulty into a target hex.
        
        Args:
            difficulty_fudge (int): The difficulty fudge that determines fudging of the target.
            string (bool): Strips trailing zeros from the result if True.

        Returns:
            str: Hex value of a target hash equal to this difficulty, stripped of its leading 0x.
        """
        if not isinstance(self.difficulty, (int, long)):
            raise TypeError('difficulty is not int')
        sha = self.get_difficulty_hex()
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

        if 0 < difficulty_fudge:
            base256 = base256[difficulty_fudge:] + base256[:difficulty_fudge]
        return base256.rstrip('0') if strip else base256

    def assign_events_hash(self):
        """Calculates and assigns the hash of events in this block.

        Returns:
            str: Sha256 hash of the provided events.
        """
        result = ''
        for event in sorted(self.events, key=lambda x: x.index):
            result += event.assign_hash()
        self.events_hash = util.sha256(result)
        return self.events_hash

    def assign_hash(self, nonce=None, header_prefix=None):
        """Calculates the hash of this block without assigning it.
        
        Args:
            headr (str): The header to hash instead, instead of concatenating a new one.

        Returns:
            str: Resulting hash of the header.
        """
        self.nonce = self.nonce if nonce is None else nonce
        if self.nonce is None:
            raise ValueError('nonce cannot be None')
        header = None
        if header_prefix is None:
            header = self.get_concat()
        else:
            header = header_prefix + str(self.nonce)
        self.hash = util.sha256(header)
        return self.hash

    def get_concat(self, include_nonce=True):
        """Calculates and assigns required hashes, then concats the header information of this block.
        
        Args:
            include_nonce (bool): Includes the nonce at the end of the header if True.

        Returns:
            str: Resulting header.
        """
        if self.version is None:
            raise ValueError('version cannot be None')
        if self.previous_hash is None:
            raise ValueError('previous_hash cannot be None')
        if self.difficulty is None:
            raise ValueError('difficulty cannot be None')
        if self.events is None:
            raise ValueError('events cannot be None, try assigning an empty array')
        if self.time is None:
            raise ValueError('time cannot be None')
        
        result = ''
        result += str(self.version)
        result += self.previous_hash
        result += str(self.difficulty)
        result += self.assign_events_hash()
        result += util.sha256(self.meta)
        result += str(self.time)

        if include_nonce:
            if self.nonce is None:
                raise ValueError('nonce cannot be None')
            result += str(self.nonce)
        
        return result

    def get_json(self):
        json_events = []
        if self.events is not None:
            for event in self.events:
                json_events.append(event.get_json())

        return {
            'nonce': self.nonce,
            'height': self.height,
            'hash': self.hash,
            'difficulty': self.difficulty,
            'events': json_events,
            'version': self.version,
            'time': self.time,
            'previous_hash': self.previous_hash,
            'events_hash': self.events_hash,
            'meta': self.meta,
            'meta_hash': self.meta_hash
        }


    def set_from_json(self, block_json):
        self.hash = block_json.get('hash')
        self.nonce = block_json.get('nonce')
        self.previous_hash = block_json.get('previous_hash')
        self.height = block_json.get('height')
        self.size = block_json.get('size')
        self.version = block_json.get('version')
        self.difficulty = block_json.get('difficulty')
        self.time = block_json.get('time')
        self.events_hash = block_json.get('events_hash')
        self.meta = block_json.get('meta')
        self.meta_hash = block_json.get('meta_hash')
        
        self.events = []
        for event in block_json.get('events', []):
            current_event = EventModel()
            current_event.set_from_json(event)
            self.events.append(current_event)


    def get_pretty_content(self):
        content = super(BlockModel, self).get_pretty_content()
        content += self.get_pretty_entry('hash', self.hash)
        content += self.get_pretty_entry('nonce', self.nonce)
        content += self.get_pretty_entry('previous_hash', self.previous_hash)
        content += self.get_pretty_entry('previous_id', self.previous_id)
        content += self.get_pretty_entry('height', self.height)
        content += self.get_pretty_entry('size', self.size)
        content += self.get_pretty_entry('version', self.version)
        content += self.get_pretty_entry('difficulty', self.difficulty)
        content += self.get_pretty_entry('time', self.time)
        content += self.get_pretty_entry('interval_id', self.interval_id)
        content += self.get_pretty_entry('root_id', self.root_id)
        content += self.get_pretty_entry('chain', self.chain)
        content += self.get_pretty_entry('events', self.events)
        content += self.get_pretty_entry('events_hash', self.events_hash)
        content += self.get_pretty_entry('meta', self.meta)
        content += self.get_pretty_entry('meta_hash', self.meta_hash)
        
        return content