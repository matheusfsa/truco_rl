from .player import Player
from .card import generate_deck, ranks_names

class GameRound: #also known as Rodada ou Partida.
    def __init__(self, game, dealer: Player):
        self.game = game
        self.dealer = dealer
        self.flop = None
        self.manilha = None
        self.round_score = 1
        self.last_bet_call = None
        self.deck = game.deck
        self.all_cards = generate_deck(game.sujo)
        self.players = game.players.copy()
        self.teams = game.teams
        self.cards_round = {}
        self.turn = 0
        self.in_call = False
        self.winners = [] # Who won each turn of the round 3/3
        self.game_round = True

    def send_turn(self):
        for i in range(len(self.players)):
            self.players[i].turn = (i + 1)%2

    def bet(self, current_score=None):
        if not current_score:
            current_score = self.round_score
        if current_score == 1:
            return "Truco!", 3
        if current_score == 3:
            return "Seis!", 6
        if current_score == 6:
            return "Nove!", 9
        if current_score == 9:
            return "Doze!", 12
        if current_score == 12:
            return "", 0

    def deal(self):
        """
        The dealer gets the deck and deals 3 cards to each player.
        Starting to the player at his right hand.
        The dealer is the last to receive the card.
        """
        self.give_deck_to(self.dealer)
        # Three cards to each player:
        for _ in range(3):
            for player in self.players:
                newcard = self.deck.draw()
                player.hand.add_single(newcard)
                # This will not be here in the future!
            #     print("Jogador {} \trecebeu uma carta \t--SEGREDO:({}).".format(player.name, str(newcard)))
            # print("\n")
        self.flop = self.deck.draw()
        self.shackles(self.flop)
        # print("Vira: {}".format(self.flop))
        # print("Manilha: ", self.manilha, " - ", ranks_names(self.manilha))

    def give_deck_to(self, initial=None):
        if initial:  # This is only for GameRound
            while self.players[-1] != initial:
                self.players.append(self.players.pop(0))

    def next_to_play(self, player):
        if player:  # This is only for GameRound
            while self.players[0] != player:
                self.players.append(self.players.pop(0))

    def find_winner(self):  # This also should be part of a new Class GameRound
        """
        Finds the highest card, then finds which player won, gives points to the team.
        """
        # Todo
        winner = None
        manilhas = {}
        cards = []
        print("Manilha: ", self.manilha)
        player_by_card = {}
        for player, play in self.cards_round.items():
            if play['visible'] == True:
                cards.append(play['card'])
                player_by_card[play['card'].name] = player
                print("Jogador: {} jogou {}".format(player, play['card']))  # if play['visible'] == True else None
                # Looking for shackles in the current table
                if play['card'].rank == self.manilha:
                    print("Opá!! Temos uma manilha! {} jogada por {}".format(play['card'].suit_name, player))
                    manilhas[player] = play['card']

        if manilhas != {}:
            high_suit = 0 #max(manilhas.values()) # Todo: Bug in max() -> order of manilhas matters in the pile.
            high_card = None
            winner = None
            for player, manilha in manilhas.items():
                if manilha.suit > high_suit:
                    high_suit = manilha.suit
                    high_card = manilha
                    winner = player
            # winner = player_by_card[high_card.name]
            print("\n\n\tVencedor da rodada: {} com {}".format(winner,high_card))
            return winner
        else:
            tied = []
            if not cards:
                return None
            high_rank = max(cards).rank
            for card in cards:
                if card.rank == high_rank:
                    tied.append(card)
            if len(tied) > 1:
                print("\n\n\tEmpate!")
                return None
            else:
                winner = player_by_card[tied[0].name]
                print("\n\t{} jogou a maior carta {}".format(winner, tied[0]))
                return winner


    def shackles(self, card):
        ranks = []
        shackles = []
        for current_card in self.all_cards:
            for rank in current_card.rank:
                ranks.append(rank) if rank not in ranks else None
                shackles.append(rank) if rank not in shackles else None
        shackles.append(shackles.pop(0))
        dictionary = dict(zip(ranks, shackles))
        self.manilha = dictionary[card.rank]
        return dictionary[card.rank]

    def start(self):
        # print("Vamos jogar!")

        game_round = True
        self.table = []
        self.count_round = 1
        while self.game_round == True:
            # Turn of the player:
            for i in range(len(self.players)):
                player =  self.players[i]
                played = self.play(player) # Todo: Who should play is the PLAYER!!!
                # Player, Put the cart on the table:
                self.table.append(played['card']) if played['card'] != None else None
                # This card belongs to the player.
                self.cards_round[player] = played
                # Does anybody run away of this match? Example: when increasing the bet?
                if played['round_over'] == True:
                    print("Fim dessa partida!")
                    self.game_round = False
                    break
            else:  # No more players...
                print("\nTodos jogaram!?")
                winner = self.find_winner()
                self.game_round = self.check_round_alive(winner)
                self.count_round += 1
                # print("\n")
        self.dischard_cards()

    def check_round_alive(self, winner):
        # The round (rodada) keeps alive? No team winner?
        if winner:
            self.winners.append(self.teams[winner])
            self.next_to_play(winner)
        else:
            self.winners.append(winner)
        #print(self.winners) # debug helping..
        if self.count_round == 1:
            return True # Keep playing guys.

        if self.count_round == 2:
            if self.winners[0] == self.winners[1] and self.winners[0]:
                winner = self.winners[1]
                self.game.scores[winner] += self.round_score
                print("Vencedor da rodada: Time {}: +{} tentos".format(winner,self.round_score))
                return False
            if self.winners[1] and not self.winners[0]: # Tied first but not second.
                winner = self.winners[1]
                self.game.scores[winner] += self.round_score
                print("Vencedor da rodada: Time {}: +{} tentos".format(winner,self.round_score))
                return False
            if self.winners[0] and not self.winners[1]: # Won first but tied second.
                winner = self.winners[0]
                self.game.scores[winner] += self.round_score
                print("A primeira é caminhão de boi! Venceu time {}: +{} tentos".format(winner,self.round_score))
                return False
            return True # both are Tied. Play last one!

        if self.count_round == 3:
            if not self.winners[0] and not self.winners[1] and not self.winners[2]:
                print("EMPATE 3/3!!!!")
                return False
            if self.winners[2]:
                winner = self.winners[2]
                self.game.scores[winner] += self.round_score
                print("Rodada disputada e vencida pelo time {}: +{} tentos".format(winner,
                                                                                    self.round_score))
                return False

    def dischard_cards(self):
        # All Players give all cards back to the deck:
        for player in self.players:
            while not player.hand.empty:
                card = player.hand.draw()
                self.deck.discard(card)
        # Remove any empty entry in self.table:
        self.table = [x for x in self.table if x is not None]
        # Get cards on the table:
        for card in self.table:
            self.deck.discard(card)
        # Get the Flop and put in the deck:
        self.deck.discard(self.flop)
        # Reset Table and etc
        self.flop = None
        self.table = []
        self.winners = []
        self.count_round = 1

    
    def play(self, player):
        """
        """
        valid = True
        while valid:
            self.in_call = False
            options = {}
            round_over = False
            for i, card in enumerate(player.hand):
                options[str(i + 1)] = card
            card = None
            bet = self.bet()
            # Give possibility to raise the bet, if not asked by the team before:
            if self.last_bet_call != self.teams[player] and self.round_score != 12:
                # increase_bet = input("\nPedir {}?".format(bet[0]))
                options['0'] = bet[0]
            else:
                print("Você não pode pedir {}...".format(bet[0]))

            print("\n\tVira: {}\n\tManilhas: {}: {}".format(self.flop, self.manilha, ranks_names(self.manilha)))
            print("{}, sua vez...".format(player.name,))
            print("Opções:")
            for key, value in options.items():
                print("\t{}: {} ".format(key,value))
                # Todo: If it is not first round.
                print("\t \t{}{}: Esconde a carta {}".format(key, key, value)) if key != '0' else None

            # I BET THERE IS A BETTER WAY TO SOLVE THIS ISSUE: (Error when pressing just Enter)
            player.sense(self.game, self, options=options)
            valid_choice = False
            while not valid_choice:
                choice = player.act()
                if choice in ['0','1','2','3','4','11','22','33']: valid_choice = True # '4' is random card.
            # Todo: Bug if empty input!!

            
            if choice[0] in options.keys():
                if choice == '0':  # Raise Bet!
                    call = self.call_by(player)  # Ask other player
                    if not call:  # Challange not accepted. End round!
                        self.in_call = False
                        winner = self.last_bet_call  # Last one to challange wins.
                        self.game.scores[winner] += self.round_score
                        points = self.game.scores[winner]
                        print("Vencedor da rodada time: {} total: {} ".format(winner, points))
                        return {'card': None, 'visible': False, 'round_over': True}

                    valid = True
                else:
                    if len(choice) == 1:
                        print("{} escolheu uma carta...".format(player))
                        card = player.hand.draw_specific(options[choice[0]])
                        valid = False
                        visible = True
                    elif choice[1] == str(choice[0]):
                        print("{} ESCONDEU uma carta...".format(player))
                        card = player.hand.draw_specific(options[choice[0]])
                        valid = False
                        visible = False
                    else:
                        valid = True

            else: # Option '4'
                print("Vou jogar qualquer uma...")
                card = player.hand.draw_random()
                visible = True
                valid = False
        print("{}, jogou: {}".format(player, card if visible else None))
        return {'card': card, 'visible': visible, 'round_over': round_over}

    def call_by(self, player):
        self.in_call = True
        index = self.players.index(player) + 1
        if index >= len(self.players):
            index = 0
        called = self.players[index]
        # ToDo: Show only to the player...
        self.last_bet_call = self.teams[player]
        # Todo : Put different phrases when challanging... :)
        # challange_by(player, worth, who)
        print("{} grita: {}!!! {}, MARRECO!!!".format(player, str(self.bet()[0]).upper(), str(called).upper()))

        print("Sua mão,", called, ":", [card.name for card in called.hand])

        print("Opções:")

        if self.round_score < 9:
            print("\t1: Aceitar - Partida: {} tentos\n\t2: Pedir: {}\n\t0: Fugir - Perde: {} tento(s)".format(
                self.bet()[1], self.bet(current_score=self.bet()[1])[0], self.round_score))
            options = [1, 2, 0]
        else:
            options = [1, 0]
            print("\t1: Aceitar - Partida: {} tentos\n\t0: Fugir - Perde: {} tentos\n".format(self.bet()[1],
                                                                                            self.round_score))
        valid = True
        while valid:
            try:
                called.sense(self.game, self, options, in_call=True)
                calling = called.act()
            except:
                continue
            if calling in options:
                if calling == 1:
                    self.round_score = self.bet()[1]
                    print("Valendo:", self.round_score, "tentos")
                    return True  # Todo WTF??
                elif calling == 2:
                    self.round_score = self.bet()[1]
                    print("Valendo:", self.round_score, "tentos")
                    return self.call_by(called)
                else:
                    print("Fugiu!!")
                    print("Valeu:", self.round_score, "tentos")
                    return False