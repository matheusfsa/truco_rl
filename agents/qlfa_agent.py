import torch
import torch.optim as optim
import torch.nn as nn
from agents.query_player import QAPlayer
from agents.rl_agent import RLAgent
from agents.op_player import OpPlayer
from base.task import Task
import numpy as np
import random

class QAgentLFA(RLAgent):

    def __init__(self, name, opponent=OpPlayer('Opponent'), verbose=False, state_shape=40, actions_shape=7, is_copy=False):
        super(QAgentLFA, self).__init__(name)
        self.actions = []
        self.T = np.zeros((7,))
        self.actions_shape = actions_shape
        self.state_shape = state_shape
        self.Q = self.build_q(state_shape + actions_shape, 1)
        self.N = {}
        self.verbose = verbose
        if is_copy:
          self.task = None
        else:
          self.task = Task(agent=self, opponent=opponent, verbose=self.verbose)

    def build_q(self, input_shape, output_shape):
        '''
        model = nn.Sequential(
          nn.Linear(input_shape, 64),
          nn.Linear(64, 1)
        )
        return model
        '''
        return nn.Linear(input_shape, output_shape)

    def card_to_number(self, card, manilha):
        ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        i = ranks.index(card.rank)
        j = (card.suit - 1)
        if i == manilha:
            return 3. + j
        if i < 4:
          return 0
        if i < 7:
            return 1.
        return 2.

    def observe(self, state):
        # state_res = [0->maior carta (-1 - 3), 1->carta do meio(-1 - 3), 2->menor carta (-1 - 3), 3->carta na mesa(-1 - 3),
        # 4->in_call(0-1), 5->pode trucar(0-1), 6->pode aumentar(0-1), 7->ganhou o primeiro(0-1), 8->ganhou o segundo(0-1)]
        self.state = state
        card_size = 7
        ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        state_res = torch.zeros(1, 4*card_size + 3*2 + 2*3)
        cards = [-1, -1, -1]
        manilha = ranks.index(state['round'].manilha)
        i = 0
        hand = list(self.hand).copy()
        hand.sort(reverse=True)
        for c in hand:
            cards[i] = self.card_to_number(c, manilha)
            state_res[0, i*card_size + int(cards[i])] = 1.
            i += 1
        
        if self.turn == 1 and state['round'].table:
            card = self.card_to_number(state['round'].table[-1], manilha)
            state_res[0, 3*card_size + int(card)] = 1.0 # 3->carta na mesa(-1 - 3)
        if 'options' in state:
            self.in_call = state['round'].in_call
            state_res[0, 4*card_size + int(self.in_call)] = 1.0
            if not isinstance(state['options'], list):
                self.actions = list(state['options'].keys()) 
                state_res[0, 4*card_size +  2 + int(('0' in self.actions))] = 1.0
                actions = [i for i in range(len(self.actions))]
            else:
                self.actions = state['options']
                actions = [i + 4 for i in range(len(self.actions))]
                state_res[0, 4*card_size +  4 + int((2 in self.actions))] = 1.0

        else:
            actions = [0]

        team = state['round'].teams[self]
        winners = state['round'].winners
        if len(winners) >= 1:
            if winners[0] is not None:
                state_res[0, 4*card_size +  6 + int((winners[0] == team))] = 1.0
            if len(winners) == 2:
                if winners[1] is not None:
                    state_res[0, 4*card_size +  8 + int((winners[1] == team))] = 1.0
            else:
              state_res[0, 4*card_size +  9 + 2] = 1.0
        else:
            state_res[0, 4*card_size +  6 + 2] = 1.0
        
        return state_res, actions

    def qs(self, s, actions):
        with torch.no_grad():
            qs = torch.zeros(len(actions))
            for i in range(len(actions)):
                a = torch.zeros(1, self.actions_shape)
                a[0, actions[i]] = 1
                x = torch.cat((s, a), dim=1)
                qs[i] = self.Q(x)
                
        return qs

    def epsilon_greedy(self, s, actions, epsilon):
        qs = self.qs(s, actions)
        best_a =  qs.argmax()
        m = len(actions)
        acs = [i for i in range(m)]
        weights = [(epsilon/m) * (1-epsilon) if i == best_a else (epsilon/m) for i in range(m)]
        choice = random.choices(acs, weights=weights)
        return choice[0]

    def chose_action(self, s, actions, epsilon, policy='epsilon_greedy'):
        #print('Actions:', actions)
        #print('Epsilon:',epsilon)
        if epsilon is not None:
          if policy == 'epsilon_greedy':
            return self.epsilon_greedy(s, actions, epsilon)
          else:
            return self.epsilon_policy(actions, epsilon)
        else:
          qs = self.qs(s, actions)
          return qs.argmax()

    def action_to_option(self, a):
        if self.in_call:
            return self.actions[a]
        else:
            hand = list(self.hand).copy()
            hand.sort(reverse=True)
            if '0' in self.actions:
                if a == len(self.actions)-1:
                    return '0'
            c = hand[a]
            for i in range(len(self.hand)):
                if c == self.hand[i]:
                    return str(i + 1)
            return self.actions[a]

    
    def act(self, S):
        s, actions = self.observe(S)
        a = self.chose_action(s, actions, None)
        action = self.action_to_option(a)
        return action

    def predict(self, s, a, actions): 
        acs = torch.zeros(1, self.actions_shape)
        acs[0, actions[a]] = 1
        x = torch.cat((s, acs), dim=1)
        return self.Q(x)

    def target(self, s, actions, R, gamma):
        qs = self.qs(s, actions)
        return R + gamma*qs.max()
    
    def loss(self, predict, target):
        return predict - target
    
    def update(self, s, a, actions, s1, actions1, R, gamma, lr, is_finished):
        if is_finished:
            t = torch.tensor(R)
            
        else:
            t = self.target(s1, actions, R, gamma)
        optimizer = optim.SGD(self.Q.parameters(), lr=lr, momentum=0.9)
        optimizer.zero_grad()
        pred = self.predict(s, a, actions)
        loss = self.loss(pred, t)
        loss.backward()
        optimizer.step()

    def fit(self,  gamma=0.8, lr=0.125, epsilon=1.0, e_decr=0.99, episodes=1000, sample_rounds=100, reset=True ,policy='epsilon_greedy', n0=1):
        
        #print('Estados visitados antes do treinamento:', len(self.Q.keys()))
        e_decr = epsilon/episodes
        rewards = np.zeros((episodes,))
        wins_episodes = np.zeros((episodes,))  
        wins_last_episodes = np.zeros((episodes,))
        wins_test_episodes = np.zeros((episodes,))
        for i in range(episodes):
            state = self.task.initial_state()
            s, actions = self.observe(state)
            while not self.task.is_finished(self.state):
                s_list = tuple(s.tolist()[0])
                if tuple(s.tolist()[0]) not in self.N:
                    self.N[tuple(s.tolist()[0])] = 0
                self.N[tuple(s.tolist()[0])] += 1
                epsilon=(n0/(n0 + self.N[tuple(s.tolist()[0])]))
                a = self.chose_action(s, actions, epsilon)
                action = self.action_to_option(a)
                state = self.task.step(action, state)
                s1, actions1 = self.observe(state)
                R = self.task.get_reward(state)
                pred = self.predict(s, a, actions)
                is_finished = self.task.is_finished(self.state)
                self.update(s, a, actions, s1, actions1, R, gamma, lr, is_finished)
                s = s1
                actions = actions1

            epsilon -= e_decr
            #self.epsilon *= e_decr
            rewards[i] = R
            wins = ((rewards > 0).sum()/(i+1)) * 100
            wins_last = 0
            if i % 1000 == 0:
              _, wins_test = self.test(opponent=self.task.opponent, n=sample_rounds, v=False)
            if sample_rounds >= 1:
              if i >= sample_rounds -1:
                  wins_last = ((rewards[i-sample_rounds -1:i+1] > 0).sum()/sample_rounds) * 100 
              else:
                  wins_last = ((rewards[:i+1] > 0).sum()/(i+1)) * 100 
            else:
              wins_last = 0
            if R >= 1:
                print('\rWin rate:{}% Win rate in the last rounds:{}% Win rate in test:{}% Episode:{}/{}:{} won!         '.format(int(wins),
                                                                                                                                  int(wins_last),
                                                                                                                                  int(wins_test),
                                                                                                                                  i+1, episodes,
                                                                                                                                  self.name),
                       end='')
            else:
                print('\rWin rate:{}% Win rate in the last rounds:{}% Win rate in test:{}% Episode:{}/{}:{} was defeated!'.format(int(wins),
                                                                                                                                  int(wins_last),
                                                                                                                                  int(wins_test),
                                                                                                                                  i+1, episodes,
                                                                                                                                  self.name),
                       end='')
            #print('reward:', R)    
            #print('-----------------------------------------------------------------------')
            wins_episodes[i] =  wins
            wins_last_episodes[i] = wins_last
            wins_test_episodes[i] = wins_test
        wins = ((rewards > 0).sum()/episodes) * 100
        print('\nThe agent won {:.2f}% of the rounds'.format(wins))
        return {'rewards':rewards, 'wins':wins_episodes, 'wins_test':wins_test_episodes,'wins_last':wins_last_episodes} 

    def test(self, n, v=True, opponent=OpPlayer('Opponent'), reset_t=False):

        if n:
          if reset_t:
            self.T = self.T = np.zeros((7,))
          rewards = np.zeros((n,))
          self.task = Task(agent=self, opponent=opponent, verbose=False)
          for i in range(n):
              state = self.task.initial_state()
              R = self.task.get_reward(state)
              while not self.task.is_finished(state):
                  a = self.act(state)
                  state = self.task.step(a, state)
                  R = self.task.get_reward(state)
              rewards[i] = R
              if v:
                if R >= 1:
                    print('\rEpisode:{}/{}:{} won!         '.format(i+1, n, self.name), end='')
                else:
                    print('\rEpisode:{}/{}:{} was defeated!'.format(i+1, n, self.name), end='')
          wins = ((rewards > 0).sum()/n) * 100
          if v:
            print('\nThe agent won {:.2f}% of the rounds'.format(wins))
          return rewards, wins
        return [], 1.0

def train_test(train_episodes=10000, test_episodes=1000, gamma=1.0, lr=0.15, epsilon=1.0, sample_rounds=1000, n0=1):
    qlfa_agent = QAgentLFA('QAgentLFA', verbose=False)
    history_qlfa = qlfa_agent.fit(gamma=gamma, lr=lr, epsilon=epsilon, episodes=train_episodes, sample_rounds=sample_rounds, n0=n0)
    qlfa_agent.test(test_episodes)
    return qlfa_agent