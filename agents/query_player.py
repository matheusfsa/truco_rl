from base import Player

class QAPlayer(Player):
    def act(self, S):
        #print('Table:', self.table)
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
