from typing import List, Dict
from Card import AbstractCard, HeroCard, SpecialCard, WeatherCard, UnitCard, Weather, Special, Faction, Ability, CombatRow
import tomllib

#singleton basically
class CardLoader:
    def __init__(self):
        self.cards: Dict[str, AbstractCard] = None
        self._load_cards()

    def get_all_card_ids(self):
        """Return list of all valid card IDs"""
        return list(self.cards.keys())

    def _load_cards(self):
        # open toml file and load cards
        if self.cards is not None:
            return
        
        # Initialize empty dictionary
        self.cards = {}
        
        # Open file in binary mode as required by tomllib
        with open("cards.toml", "rb") as f:
            data = tomllib.load(f)
            for card in data["cards"]:
                # Skip cards without IDs
                if not card.get("id"):
                    continue

                try:
                    class_name = card["card_class"]
                    card_obj = globals()[class_name]()

                    for key, value in card.items():
                        if key in ("card_class", "id", "filename"):
                            continue

                        # Handle enums
                        try:
                            if key == "type" and value:
                                if class_name == "WeatherCard":
                                    value = Weather[value]
                                elif class_name == "SpecialCard":
                                    value = Special[value]
                            elif key == "faction" and value:
                                value = Faction[value]
                            elif key == "ability" and value:
                                # Map some common ability names
                                ability_map = {
                                    "horn": "HORN",
                                    "bond": "TIGHT_BOND",
                                    "medic": "MEDIC",
                                    "spy": "SPY",
                                    "muster": "MUSTER",
                                    "morale": "MORALE_BOOST",
                                    "scorch": "SCORCH",
                                }
                                if not value:  # Empty string or None
                                    value = None
                                else:
                                    value = ability_map.get(value.lower(), None)
                                    if value:
                                        value = Ability[value]
                            elif key == "row" and value:
                                if isinstance(value, list):
                                    value = [CombatRow[r] for r in value]
                                else:
                                    continue  # Skip invalid rows

                            setattr(card_obj, key, value)
                        except (KeyError, ValueError):
                            # If enum conversion fails, set to None/default
                            if key == "ability":
                                setattr(card_obj, key, Ability.NONE)
                            else:
                                setattr(card_obj, key, None)

                    self.cards[card["id"]] = card_obj
                except Exception as e:
                    print(f"Failed to load card: {card.get('name', 'Unknown')}, Error: {e}")
                    continue
                
    def get_card_by_id(self, id: str) -> AbstractCard:
        self._load_cards()
        return self.cards[id]

