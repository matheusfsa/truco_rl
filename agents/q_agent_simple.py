from agents.query_player import QAPlayer
from agents.rl_agent import RLAgent
from agents.q_agent import QAgentBase
from agents.op_player import OpPlayer
from base.task import Task
import numpy as np

class QAgentSimple(QAgentBase):

    def __init__(self, name, opponent=OpPlayer('Opponent'), verbose=False, Q={}, is_copy=False):
        super(QAgentSimple, self).__init__(name, opponent=opponent, verbose=verbose, Q=Q, is_copy=is_copy)
        self.actions = []
        self.Q = Q
        self.T = np.zeros((7,))
        self.verbose = verbose
        if is_copy:
          self.task = None
        else:
          self.task = Task(agent=self, opponent=opponent, verbose=self.verbose)
  
    def observe(self, state):
        # state = [cartas em ordem decrescente[ncards], manilha, carta do outro jogador na mesa[ncards], in_call, pode trucar, pode aumentar, ganhou o primeiro, ganhou o segundo]
        
        ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        self.state = state
        n_ranks = len(ranks)
        n_cards = n_ranks*4
        state_res = np.zeros((n_cards + n_ranks + n_cards +5,))
        hand = list(self.hand).copy()
        #hand.sort(key=lambda c: 100 if c.rank == self.state['round'].manilha else ranks.index(c.rank), reverse=True)
        hand.sort(reverse=True)
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
                state_res[n_cards + n_ranks + n_cards + 2] = (2 in self.actions)* 1.0
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