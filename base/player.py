import pyCardDeck

class Player:
#
    def __init__(self, name: str):
        self.hand = pyCardDeck.Deck(name=name, reshuffle=False)
        self.name = name
        self.manilha = None
        self.flop = None
        self.options = None
        self.current_score = None
        self.last_bet_call = None
        self.scores = None
        self.state = None
        self.in_call = False
        self.table = None
        self.turn = 0
#
    def __str__(self):
        return self.name

    def sense(self, game, game_round, options, in_call=False):
        self.options = options
        self.flop = game_round.flop
        self.manilha = game_round.manilha
        self.round_score = game_round.round_score
        self.last_bet_call = game_round.last_bet_call
        self.scores = game.scores
        self.table = game_round.cards_round
        self.in_call = in_call

    def build_state(self):
        raise NotImplementedError


    def act(self, S):
        raise NotImplementedError

