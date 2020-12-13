from base.player import Player
from base.card import TrucoCard
import random

class OpPlayer(Player):
    def act(self, S):
        
        state = self.observe(S)
        actions = self.actions
        
        weights = [0 for _ in range(len(actions))]
        if state['in_call']:
            if state['can_raise']:
                actions = [1, 2, 0]
                weights = [0.5, 0.4, 0.1]
                if state['manilha'] is not None:
                    weights = [0.1, 0.9, 0.0]
            else:
                actions = [1, 0]
                weights = [0.7, 0.3]
                if state['manilha'] is not None:
                    weights = [1.0, 0.0]
        else:
            if state['can_ask']:
                weights = [0.9/(len(actions)-1) for i in range(len(actions))]
                weights[-1] = 0.1
                if state['manilha'] is not None:
                    weights = [0.1 for i in range(len(actions))]
                    weights[-1] = 1-  0.1*(len(actions)-1)
            else:
                weights = [1.0/len(actions) for i in range(len(actions))]
        choice = random.choices(actions, weights=weights)
        return self.get_option(choice[0], state)

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


    def observe(self, S):
        # state = [*cartas em ordem decrescente[3], manilha, carta do outro jogador, in_call, pode trucar, pode aumentar]
        state = {}
        hand = list(self.hand)
        hand.sort(reverse=True)
        state['cards'] = hand
        if isinstance(S['options'], list):
            self.actions = S['options']
        else:
            self.actions = list(S['options'].keys()) 
        self.options = S['options']
        state['manilha'] = None
        for card in hand:
            if card.rank == S['round'].manilha:
                state['manilha'] = card
                break
        state['card_table'] = None
        if self.turn == 1 and S['round'].table:
            state['card_table'] = S['round'].table[-1]
        state['in_call'] = S['round'].in_call
        state['can_ask'] = False
        state['can_raise'] = False
        if S['round'].in_call:
            state['can_raise'] = len(self.options) == 3
        else:
            state['can_ask'] = '0' in self.options
        return state

            




