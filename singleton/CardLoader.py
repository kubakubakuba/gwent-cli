from typing import List, Dict, Optional
from model.Card import AbstractCard, HeroCard, SpecialCard, WeatherCard, UnitCard, Weather, Special, Faction, Ability, CombatRow
import tomllib
import os.path

class CardLoader:
    _instance: Optional['CardLoader'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.cards: Dict[str, AbstractCard] = None
        return cls._instance

    def __init__(self):
        # Only load cards once when first instance is created
        self.include_file = "cards/_cardpacks.toml"
        if self.cards is None:
            self._load_cards()

    @classmethod
    def get_instance(cls) -> 'CardLoader':
        """Proper way to get CardLoader instance"""
        if cls._instance is None:
            cls._instance = CardLoader()
        return cls._instance

    def get_all_card_ids(self):
        """Return list of all valid card IDs"""
        return list(self.cards.keys())

    def _load_cards(self):
        # open toml file and load cards
        if self.cards is not None:
            return
        
        # Initialize empty dictionary
        self.cards = {}
        
        # Load include file
        with open(self.include_file, "rb") as f:
            include_data = tomllib.load(f)
            
        # Get directory of include file for relative paths
        base_dir = os.path.dirname(self.include_file)
            
        # Load each pack
        for pack in include_data.get("pack", []):
            pack_file = os.path.join(base_dir, pack["file"])
            print(f"Loading card pack: {pack['name']}")
            
            num_cards = 0
            try:
                with open(pack_file, "rb") as f:
                    data = tomllib.load(f)
                    for card in data["cards"]:
                        # Skip cards without IDs
                        if not card.get("id"):
                            continue

                        num_cards += 1
                        try:
                            class_name = card["card_class"]
                            card_obj = globals()[class_name]()

                            # ...existing card loading code...
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
                                        ability_map = {
                                            "horn": "HORN",
                                            "bond": "TIGHT_BOND",
                                            "medic": "MEDIC",
                                            "spy": "SPY",
                                            "muster": "MUSTER",
                                            "morale": "MORALE_BOOST",
                                            "scorch": "SCORCH",
                                        }
                                        if not value:
                                            value = None
                                        else:
                                            value = ability_map.get(value.lower(), None)
                                            if value:
                                                value = Ability[value]
                                    elif key == "row" and value:
                                        if isinstance(value, list):
                                            value = [CombatRow[r] for r in value]
                                        else:
                                            continue

                                    setattr(card_obj, key, value)
                                except (KeyError, ValueError):
                                    if key == "ability":
                                        setattr(card_obj, key, Ability.NONE)
                                    else:
                                        setattr(card_obj, key, None)

                            self.cards[card["id"]] = card_obj
                        except Exception as e:
                            num_cards -= 1
                            print(f"Failed to load card: {card.get('name', 'Unknown')}, Error: {e}")
                            continue
            except Exception as e:
                print(f"Failed to load pack {pack['name']}: {e}")
                continue
            
            print(f"Loaded {num_cards} cards from {pack['name']}")
    def get_card_by_id(self, id: str) -> AbstractCard:
        self._load_cards()
        return self.cards[id]

