from .rl_agent import RLAgent
from .op_player import OpPlayer
from base.task import Task
import numpy as np
import random

class QAgent(RLAgent):

    def __init__(self, name, opponent=OpPlayer('Opponent'), episodes=1, gamma=0.8, lr=0.3, epsilon=0.3, verbose=False, Q={}):
        super(QAgent, self).__init__(name)
        self.episodes = episodes
        self.gamma = gamma
        self.lr = lr
        self.epsilon = epsilon
        self.actions = []
        self.Q = Q
        self.verbose = verbose
        self.task = Task(agent=self, opponent=opponent, verbose=self.verbose)
        
    
    def act(self, S):
        _, actions = self.observe(S)
        a = self.chose_action(actions)
        action = self.action_to_option(a)
        return action

    def observe(self, state):
        # state = [cartas em ordem decrescente[ncards], manilha, carta do outro jogador na mesa[ncards], in_call, pode trucar, pode aumentar, ganhou o primeiro, ganhou o segundo]
        
        ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        self.state = state
        n_ranks = len(ranks)
        n_cards = n_ranks
        state_res = np.zeros((n_cards + n_ranks + n_cards +5,))
        hand = list(self.hand).copy()
        
        for c in hand:
            state_res[:n_cards] += c.to_array()
        manilha = ranks.index(state['round'].manilha)
        state_res[n_cards+manilha] = 1.0
        if self.turn == 1 and state['round'].table:
            state_res[n_cards+n_ranks:n_cards+n_ranks+n_cards]+= state['round'].table[-1].to_array()
        state_res[n_cards + n_ranks + n_cards] = state['round'].in_call* 1.0
        
        if 'options' in state:
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
        team = state['round'].teams[self]
        winners = state['round'].winners
        if len(winners) >= 1:
            if winners[0] is not None:
                state_res[n_cards + n_ranks + n_cards + 3] = (winners[0] == team)*1.0
            if len(winners) == 2:
                if winners[1] is not None:
                    state_res[n_cards + n_ranks + n_cards + 4] = (winners[1] == team)*1.0

                 
        return state_res, self.get_actions(state_res, actions)
    
    def get_actions(self, state, actions):
        s = tuple(state)
        if self.task.is_finished(self.state):
            return np.array([0])
        if s not in self.S:
            self.Q[s] = actions
        return self.Q[s]
    
    def epsilon_greedy(self, actions, epsilon):
        best_a =  actions.argmax()
        m = actions.shape[0]
        acs = [i for i in range(m)]
        weights = [(epsilon/m) * (1-epsilon) if i == best_a else (epsilon/m) for i in range(m)]
        choice = random.choices(acs, weights=weights)
        return choice[0]

    def epsilon_policy(self, actions, epsilon):
        rnd = np.random.rand()
        if rnd > epsilon:
            return actions.argmax()
        else:
            return np.random.randint(actions.shape[0])

    def chose_action(self, actions):
        return self.epsilon_policy(actions, self.epsilon)
        
    
    def greedy(self,s):
        return self.Q[tuple(s)].max()
    
    def reset(self):
        for s in self.Q.keys():
            self.Q[s] *= 0
        print("The agent was successfully reset!")

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


    def fit(self,  gamma=0.8, lrs=0.125, epsilon=1.0, e_decr=0.99, episodes=1000, reset=True):
        if reset:
            self.reset()
        self.epsilon = epsilon
        rewards = np.zeros((episodes,))  
        wins_episodes = np.zeros((episodes,))  
        wins_10_episodes = np.zeros((episodes,))
        lr_episodes = np.zeros((episodes,))
        epsilon_episodes = np.zeros((episodes,))
        changes = -1
        if isinstance(lrs, list):
            ep_change =  episodes/len(lrs)
            changes = 0 
        else:
            lr = lrs
        for i in range(episodes):
            if changes >= 0:
                if i % ep_change == 0:
                    lr = lrs[changes]
                    changes += 1

            self.epsilon = 1/(i+1)
            state = self.task.initial_state()
            s, actions = self.observe(state)
            R = self.task.get_reward(state)
            while not self.task.is_finished(self.state):
                a = self.chose_action(actions)
                action = self.action_to_option(a)
                state = self.task.step(action, state)
                R = self.task.get_reward(state)*5
                s1, actions = self.observe(state)
                if not self.task.is_finished(self.state):
                    self.Q[tuple(s)][a] = self.Q[tuple(s)][a] + lr*(R*self.greedy(s1) - self.Q[tuple(s)][a])
                else:
                    self.Q[tuple(s)][0] = R 
                s = s1
            #self.epsilon *= e_decr
            rewards[i] = R
            wins = ((rewards > 0).sum()/(i+1)) * 100
            
            if i >= 9:
                wins_10 = ((rewards[i-9:i+1] > 0).sum()/10) * 100 
            else:
                wins_10 = ((rewards[:i+1] > 0).sum()/(i+1)) * 100 
            if R >= 1:
                print('\rWin rate:{}% Win rate in the last 10 rounds:{}% Episode:{}/{}:{} won!         '.format(int(wins),int(wins_10), i+1, episodes, self.name), end='')
            else:
                print('\rWin rate:{}% Win rate in the last 10 rounds:{}% Episode:{}/{}:{} was defeated!'.format(int(wins),int(wins_10), i+1, episodes, self.name), end='')
            #print('reward:', R)    
            #print('-----------------------------------------------------------------------')
            wins_episodes[i] =  wins
            wins_10_episodes[i] = wins_10
            lr_episodes[i] = lr
            epsilon_episodes = self.epsilon
        wins = ((rewards > 0).sum()/episodes) * 100
        print('\nThe agent won {:.2f}% of the rounds'.format(wins))
        print('Número de estados visitados:', len(self.Q.keys()))
        return {'rewards':rewards, 'wins':wins_episodes, 'wins_10':wins_10_episodes, 'lr':lr_episodes, 'epsilon':epsilon_episodes}   


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
            



