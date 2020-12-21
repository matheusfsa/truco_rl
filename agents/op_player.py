from base.player import Player
from base.card import TrucoCard
import random
import numpy as np

class OpPlayer(Player):

    def has_manilha(self, s, manilha=10):
      return (s[:3] == manilha).any()
    
    def cards_gt(self, s, n):
      return (s[:3] >= n).any()

    def act(self, S):
        def normalize(weights):
            tot = np.sum(weights)
            for i in range(len(weights)):
              weights[i] = weights[i]/tot
            return weights
        #state_res = [0->maior carta (-1 - 11), 1->carta do meio(-1 - 3), 2->menor carta (-1 - 3), 3->carta na mesa(-1 - 3),
        # 4->in_call(0-1), 5->pode trucar(0-1), 6->pode aumentar(0-1), 7->ganhou o primeiro(0-1), 8->ganhou o segundo(0-1)]
        #ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        state = self.observe(S)
        actions = self.actions
        manilha = self.has_manilha(state, 10)
        weights = [0 for _ in range(len(actions))]
        if state[4]:# in call?
            if state[6]: # pode aumentar
                actions = [1, 2, 0]
                weights = [0.5, 0.4, 0.1]
                if manilha:
                  weights = [0.1, 0.9, 0.0]
                elif self.cards_gt(state, 7):
                  weights = [0.3, 0.7, 0.0]
                elif self.cards_gt(state, 4):
                  weights = [0.7, 0.3, 0.0]
                else:
                  weights = [0.7, 0.2, 0.1]
            else:
                actions = [1, 0]
                weights = [0.7, 0.3]
                if manilha:
                  weights = [1.0, 0.0]
                elif self.cards_gt(state, 7):
                  weights = [1.0, 0.0]
                elif self.cards_gt(state, 4):
                  weights = [0.9, 0.1]
                else:
                  weights = [0.8, 0.2]
        else:
          
            if state[5]:#pode trucar
                weights = [0.9/(len(actions)-1) for i in range(len(actions))]
                weights[-1] = 0.1
                n = len(actions)-1
                if manilha:
                  weights[-1] = 2.0
                elif self.cards_gt(state, 7):
                  weights[-1] = 0.6
                elif self.cards_gt(state, 4):
                  weights[-1] = 0.3
                else:
                  weights[-1] = 0.1  
            else:
                weights = [1.0/len(actions) for i in range(len(actions))]
                n = len(actions)
            for i in range(n):
                  if state[3] == -1:
                    if state[i] == 11:
                        weights[i] = 1.0
                    elif state[i] >= 7:
                        weights[i] = 0.8
                    elif state[i] >= 4:
                        weights[i] = 0.4
                    else:
                        weights[i] = 0.2
                  else:
                    if state[i] > state[3]:
                        weights[i] = 1.0
                    else:
                        weights[i] = 0.2
            weights = normalize(weights)
        #print("Sua mão,", self, ":", [card.name for card in self.hand])
        #print("Actions:", actions)
        #print("Weights:", weights)

        choice = random.choices(actions, weights=weights)
        return choice[0]

    def get_option(self, a, state):
        if isinstance(a, int):
            return a
        if isinstance(a, str):
            if a == '0':
                return a
            else:
                card = state['cards'][int(a) - 1]
                for k in self.options.keys():
                    if self.options[k] == card:
                        return k


    def card_to_number(self, card, manilha):
        ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        i = ranks.index(card.rank)
        j = (card.suit - 1)
        if i == manilha:
            return 30.
        return i
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
        
        return state_res
            




