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

WeatherEffect = {
	Weather.CLEAR: None,
	Weather.FROST: CombatRow.CLOSE,
	Weather.FOG: CombatRow.RANGED,
	Weather.RAIN: CombatRow.SIEGE,
	Weather.SKELLIGE_STORM: CombatRow.CLOSE
}
class Faction(Enum):
	ANY = -1
	NILFGAARD = 0
	NORTHERN_REALMS = 1
	MONSTERS = 2
	SCOIA_TAEL = 3
	SKELLIGE = 4

class Ability(Enum):
    NONE = 0
    MEDIC = 1          # Can revive a card from graveyard
    MORALE_BOOST = 2   # Adds +1 to all units in row
    MUSTER = 3         # Summons all cards with same name from deck
    SPY = 4            # Played on opponent's side, draws 2 cards
    TIGHT_BOND = 5     # Doubles strength if another copy in same row
    SCORCH = 6         # Destroys strongest card(s) on the field
    HORN = 7           # Doubles the strength of all cards in row

class Special(Enum):
	COMMANDERS_HORN = 0
	DECOY = 1
	SCORCH = 2
	MADROEME = 3

class AbstractCard:
	def __init__(self):
		self.name = ""
		self.description = ""
		
	def __str__(self):
		return self.name

class WeatherCard(AbstractCard):
	def __init__(self):
		super().__init__()
		self.type : Weather = None

class UnitCard(AbstractCard):
	def __init__(self):
		super().__init__()
		self.row : list[CombatRow] = None
		self.faction : Faction = None
		self.value : int = 0
		self.ability : Ability = None

	def is_hero(self):
		return False

class HeroCard(UnitCard):
	def __init__(self):
		super().__init__()
		
	def is_hero(self):
		return True

class SpecialCard(AbstractCard):
	def __init__(self):
		super().__init__()
		self.type : Special = None