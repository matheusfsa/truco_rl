from base.player import Player

class QAPlayer(Player):
    def act(self, S):
        print("Sua mão,", self, ":", [card.name for card in self.hand])
        print("Manilha:", S['round'].manilha)
        if isinstance(S['options'], list):
            self.options = S['options']
        else:
            self.options = list(S['options'].keys())
        #print('Options:', self.options)
        if self.in_call:
            choice = int(input("{} {}? >>".format(self.name, self.options)))
        else:
            choice = input(self.name + " escolha " + str(self.options) + ">> ")
        
        return choice
