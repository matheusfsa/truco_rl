import pyCardDeck
from typing import List
from pyCardDeck.cards import BaseCard
import numpy as np

class TrucoCard(BaseCard):
    def __init__(self, suit: str, rank: str, name: str):
        # Define self.name through BaseCard Class
        super().__init__("{} de {}".format(name, suit[1][0]))
        self.suit = suit[0]
        self.suit_name = suit[1][0]
        self.suit_symbol = suit[1][1]
        self.rank = rank
    def __str__(self):
        return "[{}{}] {}".format(self.rank, self.suit_symbol, self.name)
    def __eq__(self, other):
        return self.name == other
    def __ge__(self, other):
        ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        # Compare Ranks
        if ranks.index(self.rank) < ranks.index(other.rank):
            return False
        elif ranks.index(self.rank) >= ranks.index(other.rank):
            return True
        else:
            return 0
    def __gt__(self, other):
        ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        # Compare Ranks
        if ranks.index(self.rank) < ranks.index(other.rank):
            return False
        elif ranks.index(self.rank) > ranks.index(other.rank):
            return True
        else:
            return 0
    
    def to_array(self):
        ranks = ['4', '5', '6', '7', 'Q', 'J', 'K', 'A', '2', '3']
        i = ranks.index(self.rank)
        j = (self.suit - 1)
        res = np.zeros((len(ranks)*4,))
        res[j*len(ranks) + i] = 1
        return res

def ranks_names(rank= None):
    ranks = {'4': 'Quatro', '5': 'Cinco', '6': 'Seis', '7': 'Sete', 'Q': 'Dama', 'J': 'Valete',
     'K': 'Rei', 'A': 'Ás', '2': 'Dois', '3': 'Três'}
    if rank:
        return ranks[rank]
    return ranks

def generate_deck(sujo=True) -> List[TrucoCard]:
    """
    Function that generates the deck, instead of writing down all cards, we use iteration
    to generate the cards for use
    :return:    List with all (24/40) cards for truco playing cards
    :rtype:     List[TrucoCard]
    """
    if sujo:
        # ♠♣♥♦
        suits = {1: ['Ouros', '♦'] , 2: ['Espadas', "♠"], 3: ['Copas', "♥"], 4: ['Paus',"♣"]}
        # suits = {1: 'Ouros ♦', 2: 'Espadas ♠', 3: 'Copas ♥', 4: 'Paus ♣'}
        ranks = ranks_names()
    if not sujo:
        suits = {1: 'Ouros', 2: 'Espadas', 3: 'Copas', 4: 'Paus'}
        ranks = {'Q': 'Dama',
                 'J': 'Valete',
                 'K': 'Rei',
                 'A': 'Ás',
                 '2': 'Dois',
                 '3': 'Três'}
    cards = []
    for suit in suits.items():
        for rank, name in ranks.items():
            cards.append(TrucoCard(suit=suit,rank=rank,name=name))
    return cards