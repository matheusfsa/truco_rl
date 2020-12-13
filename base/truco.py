import pyCardDeck
from typing import List
from .card import generate_deck, ranks_names
from .player import Player
from .game_round import GameRound



class TrucoGame:

    def __init__(self, players: List[Player], sujo=True, verbose=True):
        self.deck = pyCardDeck.Deck(generate_deck(sujo),name="Truco Sujo", reshuffle=False)
        self.sujo = sujo
        self.deck_size = len(self.deck)
        # Not supposed to be here... but where?:
        if len(players) not in [2,4,6]:
            raise("Erro: Precisa de 2, 4 ou 6 jogadores")
        self.players = players
        self.teams, self.team1, self.team2 = {}, [], []
        self._teams()
        self.scores = {1: 0, 2: 0} #team: score
        self.ranks_names = ranks_names()
        self.verbose = verbose
        #self.show_table()

    def createGameRound(self, dealer):
        return GameRound(self, dealer, verbose=self.verbose)

    def show_table(self):
        if self.verbose:
            print("Jogo criado com {} jogadores. \n\t Mesa disposta:".format(len(self.players)))
            print("\t", *self.players[:int(len(self.players)/2)][::-1], sep="\t")
            print("\n")
            print("\t", *self.players[int(len(self.players)/2):], sep="\t")

    def _teams(self):
        team = 1
        for player in self.players:
            self.teams[player] = team
            if team == 1:
                self.team1.append(player.name)
            else:
                self.team2.append(player.name)
            team += 1
            if team > 2:
                team = 1

    def pick_dealer(self):
        self.deck.shuffle()
        dealer = None
        max_card = self.deck.draw_specific("Quatro de Ouros") # Lowest card for comparison
        cards = []
        cards.append(max_card)
        if self.verbose:
            print("\nQuem sortear a maior carta e naipe começa embaralhando...")
        for player in self.players:
            card = self.deck.draw_random()
            if self.verbose:
                print("\t{} \ttirou a carta: {}".format(player, card))
            if card >= max_card:
                if card.rank == max_card.rank:
                    if card.suit > max_card.suit:
                        dealer = player
                        max_card = card
                else:
                    dealer = player
                    max_card = card
            cards.append(card)
        # Give cards back to the deck:
        self.dischard_cards(cards)
        self.deck.shuffle_back()
        if self.verbose:
            print("\nQuem começa é o {}".format(dealer))
        return dealer

    def dischard_cards(self,cards):
        for card in cards:
            self.deck.discard(card)

    def truco(self):
        """
        """

        game = True
        if self.verbose:
            print("\nPreparando...")
        initial_dealer = self.pick_dealer()
        self.change_player_order(initial_dealer)
        all_dealers = []
        while game:
            self.deck.shuffle_back()
            if self.verbose:
                print("Distribuindo as cartas ")
            all_dealers.append(initial_dealer.name)
            game_round = self.createGameRound(initial_dealer)
            game_round.deal()
            game_round.start()
            if self.verbose:
                print("======================")
            initial_dealer = self.change_player_order()  # move deck to next player
            if self.verbose:
                print("Placar: \n")
                print("\tTime 1\t x\t Time 2")
                print(" \t{}\t x\t {}".format(self.scores[1],self.scores[2]))
                print("======================")

                print(all_dealers) # Debuging help
            if self.scores[1] >= 12:
                game = False
                if self.verbose:
                    print("Fim de Jogo!!")
                    print("Vitória do time 1: ", [*self.team1])
                    print("Adeus!")
            if self.scores[2] >= 12:
                game = False
                if self.verbose:
                    print("Fim de Jogo!!")
                    print("Vitória do time 2: ", [*self.team2])
                    print("Adeus!")

    def change_player_order(self, initial=None):
        self.players.append(self.players.pop(0))
        if initial: # This is only for GameRound
            while self.players[0] != initial:
                self.players.append(self.players.pop(0))
        return self.players[0]

    


