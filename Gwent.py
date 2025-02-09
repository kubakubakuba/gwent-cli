from Player import PlayerState

class Gwent:
	def __init__(self, player: PlayerState, enemy: PlayerState):
		self.player: PlayerState = player
		self.enemy: PlayerState = enemy
	
