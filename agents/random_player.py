from base.player import Player
from agents.op_player import OpPlayer
from base.task import Task
import numpy as np
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

    def test(self, n):
        rewards = np.zeros((n,))
        self.task = Task(agent=self, opponent=OpPlayer('Opponent'), verbose=False)
        for i in range(n):
            state = self.task.initial_state()
            R = self.task.get_reward(state)
            while not self.task.is_finished(state):
                a = self.act(state)
                state = self.task.step(a, state)
                R = self.task.get_reward(state)
            rewards[i] = R
            if R >= 1:
                print('\rEpisode:{}/{}:{} won!         '.format(i+1, n, self.name), end='')
            else:
                print('\rEpisode:{}/{}:{} was defeated!'.format(i+1, n, self.name), end='')
        wins = ((rewards > 0).sum()/n) * 100
        print('\nThe agent won {:.2f}% of the rounds'.format(wins))
        return rewards   