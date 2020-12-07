from base import Player
import random

class RandomPlayer(Player):
    def act(self, S):
        if isinstance(S['options'], list):
            self.options = S['options']
        else:
            self.options = list(S['options'].keys())
        if self.in_call:
            return 1
        return random.choice(self.options)
