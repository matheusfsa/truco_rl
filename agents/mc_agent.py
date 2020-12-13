from .rl_agent import RLAgent
from .op_player import OpPlayer
from base.task import Task
import numpy as np

class MCAgent(RLAgent):

    def __init__(self, name, episodes=1, gamma=0.8, lr=0.3, epsilon=1, verbose=True):
        super(MCAgent, self).__init__(name)
        self.episodes = episodes
        self.gamma = gamma
        self.lr = lr
        self.epsilon = epsilon
        self.actions = []
        self.Q = {}
        self.N = {}  # num_visits
        self.task = Task(agent=self, opponent=OpPlayer('Opponent'), verbose=verbose)

    def observe(self, state):
        # state = [cartas em ordem decrescente[ncards], manilha, carta do outro jogador na mesa[ncards], in_call, pode trucar, pode aumentar]
        
        ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        self.state = state
        n_ranks = len(ranks)
        n_cards = n_ranks*4
        state_res = np.zeros((n_cards + n_ranks + n_cards +1 + 1 + 1,))
        hand = list(self.hand).copy()
        
        for c in hand:
            state_res[:n_cards] += c.to_array()
        manilha = ranks.index(state['round'].manilha)
        state_res[n_cards+manilha] = 1.0
        if self.turn == 1 and state['round'].table:
            state_res[n_cards+n_ranks:n_cards+n_ranks+n_cards]+= state['round'].table[-1].to_array()
        state_res[n_cards + n_ranks + n_cards] = state['round'].in_call* 1.0
        
        if not self.task.is_finished(state):
            if isinstance(state['options'], list):
                self.actions = state['options']
                state_res[n_cards + n_ranks + n_cards + 2] = ('2' in self.actions)* 1.0
            else:
                self.actions = list(state['options'].keys()) 
                state_res[n_cards + n_ranks + n_cards + 1] = ('0' in self.actions)* 1.0
            self.in_call = state['round'].in_call
            actions = np.zeros(len(self.actions))
        else:
            actions = [0]
        
        return state_res, self.get_actions(state_res, actions)
    
    def get_actions(self, state, actions):
        s = tuple(state)
        if self.task.is_finished(self.state):
            return np.array([0])
        if s not in self.S:
            self.Q[s] = actions
        return self.Q[s]
    
    def chose_action(self, actions):
        rnd = np.random.rand()
        if rnd > self.epsilon:
            return actions.argmax()
        else:
            return np.random.randint(actions.shape[0])
    
    def greedy(self,s):
        return self.Q[tuple(s)].max()
    
    def action_to_option(self, a):
        if self.in_call:
            return self.actions[a]
        else:
            hand = list(self.hand).copy()
            hand.sort(reverse=True)
            if '0' in self.actions:
                if a == 0:
                    return '0'
                c = hand[a-1]
            else:
                c = hand[a]
            for i in range(len(self.hand)):
                if c == self.hand[i]:
                    return str(i + 1)
            
            return self.actions[a]


    def fit(self):
        rewards = np.zeros((self.episodes,))
        return_value = 0
        for i in range(self.episodes):

            states, ep_rewards, actions = self.task.episode()

            for t in range(len(ep_rewards)):
                s = states[t]
                a = actions[t]

                self.N[s][a] = self.N[s][a] + 1
                return_value = return_value + self.gamma * ep_rewards[t]
                cur_error = return_value - self.Q[s][a]
                self.Q[s][a] = self.Q[s][a] + 1 / self.N[s][a] * cur_error

                self.epsilon = 1 / i

            rewards[i] = return_value
            if return_value >= 1:
                print('\rEpisode:{}/{}:{} won!         '.format(i+1, self.episodes, self.name), end='')
            else:
                print('\rEpisode:{}/{}:{} was defeated!'.format(i+1, self.episodes, self.name), end='')
            #print('reward:', R)    
            #print('-----------------------------------------------------------------------')
        wins = ((rewards > 0).sum()/self.episodes) * 100
        print('\nThe agent won {:.2f}% of the rounds'.format(wins))
        return rewards   


'''
from agents.q_agent import QAgent
q = QAgent('Agent') 
state = q.task.initial_state()
s, actions = q.observe(state)  
a = q.chose_action(actions)
action = q.action_to_option(a)
state = q.task.step(action, state)
s1, actions = q.observe(state)

'''    
            



