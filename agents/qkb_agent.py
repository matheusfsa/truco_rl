from agents.query_player import QAPlayer
from agents.rl_agent import RLAgent
from agents.q_agent import QAgentBase
from agents.op_player import OpPlayer
from agents.random_player import RandomPlayer
from base.task import Task
import numpy as np

class QAgentKB(QAgentBase):

    def __init__(self, name, opponent=OpPlayer('Opponent'), verbose=False, Q={}, N_s={}, N_sa={}, is_copy=False):
        super(QAgentKB, self).__init__(name, opponent=opponent, verbose=verbose, Q=Q, N_s=N_s, N_sa=N_sa, is_copy=is_copy)
        self.actions = []
        self.Q = Q
        self.T = np.zeros((7,))
        self.verbose = verbose
        if is_copy:
          self.task = None
        else:
          self.task = Task(agent=self, opponent=opponent, verbose=self.verbose)
    
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
        ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        state_res = np.zeros((9,))
        cards = [-1, -1, -1]
        manilha = ranks.index(state['round'].manilha)
        i = 0
        
        for c in self.hand:
            cards[i] = self.card_to_number(c, manilha)
            i += 1
        cards.sort(reverse=True)
        state_res[:3] = cards # [0->maior carta (-1 - 3), 1->carta do meio(-1 - 3), 2->menor carta (-1 - 3)]
        if self.turn == 1 and state['round'].table:
            state_res[3] = self.card_to_number(state['round'].table[-1], manilha) # 3->carta na mesa(-1 - 3)
        else:
            state_res[3] = -1
        if 'options' in state:
            self.in_call = state['round'].in_call
            state_res[4] = self.in_call * 1.0 # 4->in_call(0-1)
            if not isinstance(state['options'], list):
                self.actions = list(state['options'].keys()) 
                state_res[5] = ('0' in self.actions)* 1.0 # 5->pode trucar(0-1)
            else:
                self.actions = state['options']
                state_res[6] = (2 in self.actions)* 1.0 # 6->pode aumentar(0-1)
            actions = np.zeros(len(self.actions))

        else:
            actions = [0]

        team = state['round'].teams[self]
        winners = state['round'].winners
        if len(winners) >= 1:
            if winners[0] is not None:
                state_res[7] = (winners[0] == team)*1.0 # 7->ganhou o primeiro(0-1)
            
            if len(winners) == 2:
                if winners[1] is not None:
                    state_res[8] = (winners[1] == team)*1.0 # 8->ganhou o segundo(0-1)
            else:
              state_res[8] = -1
        else:
            state_res[7] = -1
        actions = self.get_actions(state_res, actions)
        
        return state_res, actions

def train_test(train_episodes=10000, test_episodes=1000, gamma=1.0, lr=0.15, epsilon=1.0, sample_rounds=1000, n0=1):
    qkb_agent = QAgentKB('QAgentLFA', verbose=False)
    history_qkb = qkb_agent.fit(gamma=gamma, lrs=lr, epsilon=epsilon, episodes=train_episodes, sample_rounds=sample_rounds,n0=n0)
    qkb_agent.test(test_episodes, reset_t=True)
    qkb_agent.test(test_episodes, opponent=RandomPlayer(name='Randômico'), reset_t=True)
    return qkb_agent