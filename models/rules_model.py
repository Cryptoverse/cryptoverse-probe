from models.base_model import BaseModel

class RulesModel(BaseModel):

    def __init__(self):
        super(RulesModel, self).__init__()
        self.jump_cost_min = None
        self.jump_cost_max = None
        self.jump_distance_max = None
        self.difficulty_fudge = None
        self.difficulty_start = None
        self.difficulty_interval = None
        self.difficulty_duration = None
        self.cartesian_digits = None
        self.probe_reward = None

    def get_pretty_content(self):
        content = super(RulesModel, self).get_pretty_content()
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