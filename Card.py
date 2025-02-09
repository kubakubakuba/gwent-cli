from enum import Enum

class Weather(Enum):
	CLEAR = 0
	FROST = 1
	FOG = 2
	RAIN = 3
	SKELLIGE_STORM = 4

class CombatRow(Enum):
	CLOSE = 0
	RANGED = 1
	SIEGE = 2

class Faction(Enum):
	ANY = -1
	NILFGAARD = 0
	NORTHERN_REALMS = 1
	MONSTERS = 2
	SCOIA_TAEL = 3
	SKELLIGE = 4

class Ability(Enum):
	MEDIC = 0
	MORALE_BOOST = 1
	MUSTER = 2
	SPY = 3
	TIGHT_BOND = 4
	SCORCH = 5
	BERSERKER = 6
	MADROEME = 7
	SUMMON_AVENGER = 8

class Special(Enum):
	COMMANDERS_HORN = 0
	DECOY = 1
	SCORCH = 2
	MADROEME = 3

class AbstractCard:
	def __init__(self):
		self.name : str = ""
		self.description : str = ""
		
class WeatherCard(AbstractCard):
	def __init__(self):
		super().__init__(self)
		self.type : Weather = None

class UnitCard(AbstractCard):
	def __init__(self):
		super().__init__(self)
		self.row : list[CombatRow] = None
		self.faction : Faction = None
		self.value : int = 0
		self.ability : Ability = None

class HeroCard(UnitCard):
	def __init__(self):
		super().__init__(self)

class SpecialCard(AbstractCard):
	def __init__(self):
		super().__init__(self)
		self.type : Special = None