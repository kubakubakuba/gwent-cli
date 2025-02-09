from typing import List, Dict
from Card import Card, HeroCard, SpecialCard, WeatherCard, UnitCard
import tomllib

#singleton basically
class CardLoader():
	cards: Dict[str,Card] = None

	def _load_cards(self):
		# open toml file and load cards
		if self.cards is not None:
			return
		with open("cards.toml") as f:
			data = tomllib.load(f)
			self.cards = []
			for card in data["cards"]:
				class_name = card["card_class"]
				card_obj = globals()[class_name]()

				for key in card:
					if key in ("card_class", "id", "filename"):
						continue

					setattr(card_obj, key, card[key])
				self.cards[card["id"]] = card_obj
				
	def get_card_by_id(self, id: str) -> Card:
		self._load_cards()
		return self.cards[id]

