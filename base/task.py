from .environment import Environment
from agents.query_player import QAPlayer
from agents.op_player import OpPlayer

class Task:

    def __init__(self, agent=QAPlayer('Agent'), opponent=OpPlayer('PC'), verbose=False):
        self.env = Environment(agent, opponent, verbose)
        self.agent = agent
        self.opponent = opponent

    def is_finished(self, S):
        return not S['round'].game_round
        
    
    def get_reward(self, S):
        
        if self.is_finished(S):
            r = S['game'].scores[S['round'].teams[self.agent]]
            r_opponent = S['game'].scores[S['round'].teams[self.opponent]]
            if r == 0:
                return -1*r_opponent
            return r
        else:
            return 0
            winners = S['round'].winners
            if len(winners) == 1:
              if winners[0]  == S['round'].teams[self.agent]:
                return 0.5
              else:
                return -0.5
            if len(winners) == 2:
              if winners[0]  == S['round'].teams[self.agent]:
                return 0.5
              else:
                return -0.5
            return 0

    def initial_state(self):
        return self.env.initial_state()
    
    def step(self, a, S):
        S = self.env.step(a, S)
        return S

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
        self.env.start_round()
        self.env.start_round()