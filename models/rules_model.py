from models.base_model import BaseModel

class RulesModel(BaseModel):

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