from .truco import TrucoGame
from .game_round import GameRound, ranks_names
from typing import List
from agents import QAPlayer, RandomPlayer

class Environment:

    def __init__(self, agent=QAPlayer('Agent'), opponent=RandomPlayer('PC')):
        self.agent = agent
        self.opponent = opponent
        self.game = TrucoGame([agent, opponent])
        self.round = None
        #self.start_round()
    
    def start_round(self):
        initial_dealer = self.game.pick_dealer()
        self.game.change_player_order(initial_dealer)
        
        self.round = self.game.createGameRound(initial_dealer)
        self.round.last_bet_call = -1
        
        self.round.deal()
        self.round.send_turn()
        self.round.table = []
        self.round.count_round = 1
        

    
    def get_options(self, player):
        if self.round.in_call:
            options = []
            if self.round.round_score < 6:
                options = [1, 2, 0]
            else:
                options = [1, 0]
        else:
            options = {}
            for i, card in enumerate(player.hand):
                    options[str(i + 1)] = card
            card = None
            bet = self.round.bet()
            # Give possibility to raise the bet, if not asked by the team before:
            if self.round.last_bet_call != self.round.teams[player] and self.round.round_score != 12:
                options['0'] = bet[0]
        return options

    def get_state(self, player):
        if self.round.turn == player.turn:
            return {'game': self.game, 'round': self.round, 'options': self.get_options(player), 'in_call':self.round.in_call}
    
    def perform_action(self, player, choice, S):
        
        if self.round.turn == player.turn:
            round_over = False
            if self.round.in_call:
                choice = int(choice)
                if choice == 1:
                    
                    played = {'round_over': False,'call':False, 'accept':True}
                elif choice == 2:
                    
                    played = {'round_over': False, 'call':True, 'accept':True}
                else:
                    played = {'round_over': False, 'call':False, 'accept':False}
            else:
                if choice == '0':  # Raise Bet!
                    
                    played = {'round_over': False, 'call': True}
                else:
                    if len(choice) == 1:
                        print("{} escolheu uma carta...".format(player))
                        card = player.hand.draw_specific(S['options'][choice[0]])
                        visible = True
                    elif choice[1] == str(choice[0]):
                        print("{} ESCONDEU uma carta...".format(player))
                        card = player.hand.draw_specific(S['options'][choice[0]])
                        visible = False
                    else:
                        valid = True
                    print("{}, jogou: {}".format(player, card if visible else None))
                    played = {'card': card, 'visible': visible, 'round_over': round_over, 'call': False}
            self.update(player, played)

    def update(self, player, played):
        if self.round.turn == player.turn:
            if self.round.in_call:
                if played['accept']:
                    self.round.round_score = self.round.bet()[1]
                    print("Valendo:", self.round.round_score, "tentos")
                    if played['call']:
                        print("{} grita: {}!!! {}, MARRECO!!!".format(player, str(self.round.bet()[0]).upper(), str(player).upper()))
                    else:
                        print("{} Aceitou o Truco!!!".format(player))
                        self.round.in_call = False
                else:
                    print("Fugiu!!")
                    print("Valeu:", self.round.round_score, "tentos")
                    self.round.game_round = False
                    self.round.in_call = False
                    winner = self.round.last_bet_call  # Last one to challange wins.
                    self.game.scores[winner] += self.round.round_score
            else:
                if played['call'] and not self.round.last_bet_call == self.round.teams[player]:
                    print("{} grita: {}!!! {}, MARRECO!!!".format(player, str(self.round.bet()[0]).upper(), str(player).upper()))
                    self.round.in_call = True
                    self.round.last_bet_call = self.round.teams[player]
                else:
                    self.round.table.append(played['card']) if played['card'] != None else None
                    self.round.cards_round[player] = played
                    if played['round_over'] == True:
                        self.round.game_round = False
                    if self.round.turn == len(self.round.players) - 1:
                        winner = self.round.find_winner()
                        self.round.game_round = self.round.check_round_alive(winner)
                        self.round.count_round += 1
            if not self.round.game_round:
                self.round.dischard_cards()
            print()
            self.round.turn  = (self.round.turn + 1)%2

    def initial_state(self): 
        self.start_round()  
        if self.agent.turn == 0:
            S = self.get_state(self.agent)
        else:
            S_o = self.get_state(self.opponent)
            a_o = self.opponent.act(S_o)
            self.perform_action(self.opponent, a_o, S_o)
            S = self.get_state(self.agent)
        return S
        
    def step(self, a, S):
        self.perform_action(self.agent, a, S)
        if self.round.game_round:
            S_o = self.get_state(self.opponent)
            a_o = self.opponent.act(S_o)
            self.perform_action(self.opponent, a_o, S_o)
            S = self.get_state(self.agent)
        else:
            S = {'game': self.game, 'round': self.round}
        return S
