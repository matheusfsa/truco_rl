from .rl_agent import RLAgent
from .op_player import OpPlayer
from base.task import Task
import numpy as np
import random

class QAgentBase(RLAgent):

    def __init__(self, name, opponent=OpPlayer('Opponent'), verbose=False, Q={}, N_s={}, N_sa={},is_copy=False):
        super(QAgentBase, self).__init__(name)
        self.opponent = opponent
        self.actions = []
        self.Q = Q
        self.T = np.zeros((7,))
        self.N_s = N_s
        self.N_sa = N_sa
        self.verbose = verbose
        if is_copy:
          self.task = None
        else:
          self.task = Task(agent=self, opponent=opponent, verbose=self.verbose)
        
    
    def act(self, S):
        _, actions = self.observe(S)
        a = self.chose_action(actions, None)
        action = self.action_to_option(a)
        return action

    def observe(self, state):
        raise NotImplementedError
    
    def get_actions(self, state, actions):
        s = tuple(state)
        if not self.state['round'].game_round:
            self.Q[s] = np.array([0])
            self.N[s] = 0
        if s not in self.Q:
            self.Q[s] = np.zeros(len(actions))
            self.N_s[s] = 0
            self.N_sa[s] = np.zeros(len(actions))
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

    def chose_action(self, actions, epsilon, policy='epsilon_greedy'):
        #print('Actions:', actions)
        #print('Epsilon:',epsilon)
        if epsilon is not None:
          if policy == 'epsilon_greedy':
            return self.epsilon_greedy(actions, epsilon)
          else:
            return self.epsilon_policy(actions, epsilon)
        else:
          return actions.argmax()

    def action_to_option(self, a):
        if self.in_call:
            self.T[4 + a] += 1 
            return self.actions[a]
        else:
            hand = list(self.hand).copy()
            hand.sort(reverse=True)
            if '0' in self.actions:
                if a == len(self.actions)-1:
                    self.T[3] += 1
                    return '0'
                
            self.T[a] += 1
            c = hand[a]
            for i in range(len(self.hand)):
                if c == self.hand[i]:
                    return str(i + 1)
            
            return self.actions[a]
    
    def greedy(self,s):
        return self.Q[tuple(s)].max()
    
    def reset(self):
        self.T = np.zeros((7,))
        self.Q = {}
        self.N = {}
        print("The agent was successfully reset!")

    


    def fit(self,  gamma=0.8, lrs=0.125, epsilon=1.0, e_decr=0.99, episodes=1000, sample_rounds=100, reset=True ,policy='epsilon_greedy', n0=1):
        if reset:
            self.reset()
        print("\nTreinamento contra", self.opponent)
        print('Estados visitados antes do treinamento:', len(self.Q.keys()))
        e_decr = epsilon/episodes
        epsilon = epsilon
        rewards = np.zeros((episodes,))  
        wins_episodes = np.zeros((episodes,))  
        wins_last_episodes = np.zeros((episodes,))
        wins_test_episodes = np.zeros((episodes,))
        wins_test = 0
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
            state = self.task.initial_state()
            s, actions = self.observe(state)
            while not self.task.is_finished(self.state):
                self.N_s[tuple(s)] += 1
                epsilon=(n0/(n0 + self.N_s[tuple(s)]))
                
                a = self.chose_action(actions, epsilon)
                action = self.action_to_option(a)
                state = self.task.step(action, state)
                s1, actions = self.observe(state)
                R = self.task.get_reward(state)
                target = R + self.greedy(s1)
                predict = self.Q[tuple(s)][a]
                lr = 1/(1+self.N_sa[tuple(s)][a])
                self.Q[tuple(s)][a] = predict + lr*(target - predict)
                s = s1
            self.Q[tuple(s)][0] = 0
            #epsilon -= e_decr
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
            lr_episodes[i] = lr
            epsilon_episodes[i] = epsilon
        wins = ((rewards > 0).sum()/episodes) * 100
        print('')
        print('===================================================')
        print('The agent won {:.2f}% of the rounds'.format(wins))
        print('Número de estados visitados:', len(self.Q.keys()))
        print('Reforço Médio:', rewards.mean())
        print('Jogou a maior carta:{}, Jogou a carta do meio:{}, Jogou a menor carta:{},\nPediu Truco:{}, Aceitou Truco:{}, Aumentou Aposta:{}, Fugiu:{}'.format(*self.T))
        print('===================================================')
        
        return {'rewards':rewards, 'wins':wins_episodes, 'wins_test':wins_test_episodes,'wins_last':wins_last_episodes, 'lr':lr_episodes, 'epsilon':epsilon_episodes} 
          
    def test(self, n, v=True, opponent=OpPlayer('Opponent'), reset_t=False):
        if v:
            print("\nTeste contra", opponent)
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
            print('')
            print('===================================================')              
            print('The agent won {:.2f}% of the rounds'.format(wins))
            print('Reforço Médio:', rewards.mean())
            print('Jogou a maior carta:{}, Jogou a carta do meio:{}, Jogou a menor carta:{},\nPediu Truco:{}, Aceitou Truco:{}, Aumentou Aposta:{}, Fugiu:{}'.format(*self.T))
            print('===================================================')     
          return rewards, wins
        return [], 1.0


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
            



