from base.task import Task
from base.player import Player
from agents.op_player import OpPlayer
class RLAgent(Player):
    def __init__(self, name):
        super(RLAgent, self).__init__(name)
        self.S = {}
        self.task = Task(agent=self, opponent=OpPlayer('Opponent'))

    def observe(self, state):
        raise NotImplementedError

    def fit(self, episodes, gamma, lr):
        raise NotImplementedError
