from base import Environment
from agents import QAPlayer, RandomPlayer, OpPlayer
class Task:

    def __init__(self, agent=QAPlayer('Agent'), opponent=OpPlayer('PC')):
        self.env = Environment(agent, opponent)
        self.agent = agent
        self.opponent = opponent

    def is_finished(self, S):
        return not S['round'].game_round
    
    def get_reward(self, S):
        
        if self.is_finished(S):
            print(S['game'].scores)
            r = S['game'].scores[S['round'].teams[self.agent]]
            if r == 0:
                return -1
            return r
        else:
            #if S['round'].count_round > 1:
            #    r = (S['round'].winners[S['round'].count_round - 2] == S['round'].teams[self.agent])*1
            #    if r == 0:
            #        return -1
            return 0

    def episode(self):
        S = self.env.initial_state()
        states = [S]
        rewards = [self.get_reward(S)]
        actions = []
        while not self.is_finished(S):
            a = self.agent.act(S)
            S = self.env.step(a, S)
            states.append(S)
            rewards.append(self.get_reward(S))
            actions.append(a)
        return states, rewards, actions
    
    def reset_env(self):
        self.env = Environment(self.agent, self.opponent)