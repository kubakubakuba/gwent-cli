import asyncio
from model.Deck import Deck
from typing import List
from abc import ABC, abstractmethod
from singleton.CardLoader import CardLoader
from model.Card import UnitCard, Weather, Special, WeatherCard, SpecialCard, AbstractCard, Ability, HeroCard
from controledmodel.Board import Board

INITIAL_LIVES = 2  # Define constant here since it's player-related

class PlayerState:
    """Model class for player state"""
    def __init__(self, name: str, faction: str, deck: List[str], king: str):
        self.name: str = name
        self.faction: str = faction
        self.deck: Deck = Deck(deck)
        self.king: str = king
        self.lives: int = INITIAL_LIVES
        self.passed: bool = False

    def draw(self, n: int) -> List[str]:
        return self.deck.take_cards(n)
    
    def play_card(self, card: str):
        self.deck.play_card(card)

    def discard_card(self, card: str):
        self.deck.discard_card(card)

    def get_hand(self) -> List[str]:
        return self.deck.get_hand()

    def get_graveyard(self) -> List[str]:
        return self.deck.get_graveyard()

    def lose_life(self) -> bool:
        self.lives -= 1
        return self.lives <= 0
    
    def pass_turn(self):
        self.passed = True
    
    def has_passed(self) -> bool:
        return self.passed

    def reset_for_new_round(self):
        """Reset player state for new round"""
        self.passed = False

    def is_eliminated(self) -> bool:
        """Check if player is eliminated"""
        return self.lives <= 0

class PlayerController(ABC):
    def __init__(self, state: PlayerState, is_player: bool):
        self.state: PlayerState = state
        self.is_player: bool = is_player
        self.card_loader = CardLoader.get_instance()

    def get_hand(self) -> List[AbstractCard]:
        """Dynamically convert current hand from IDs to card objects"""
        return [self.card_loader.get_card_by_id(cid) for cid in self.state.get_hand()]

    def handle_muster_ability(self, played_card: AbstractCard) -> List[AbstractCard]:
        """Handle muster ability by finding and playing all related cards"""
        if not hasattr(played_card, 'ability') or played_card.ability != Ability.MUSTER:
            return []

        mustered_cards = []
        base_name = played_card.name.split(" - ")[0]  # Get prefix before " - " if it exists
        
        # Check hand for muster cards
        hand = self.state.get_hand()
        for card_id in hand[:]:  # Create copy to avoid modification during iteration
            card = self.card_loader.get_card_by_id(card_id)
            if card.name.startswith(base_name) and card.name != played_card.name:
                self.state.play_card(card_id)
                mustered_cards.append(card)
                
        # Check deck for muster cards
        deck = self.state.deck.deck  # Access deck directly
        for card_id in deck[:]:  # Create copy to avoid modification during iteration
            card = self.card_loader.get_card_by_id(card_id)
            if card.name.startswith(base_name):
                deck.remove(card_id)
                mustered_cards.append(card)
                
        return mustered_cards

    def play_card(self, index: int, view=None) -> AbstractCard:
        """Final implementation of card playing - should not be overridden"""
        hand = self.state.get_hand()
        if index >= len(hand):
            return None
            
        card_id = hand[index]
        self.state.play_card(card_id)
        played_card = self.card_loader.get_card_by_id(card_id)
        
        # Handle muster ability if present
        if hasattr(played_card, 'ability') and played_card.ability == Ability.MUSTER:
            return [played_card] + self.handle_muster_ability(played_card)
        
        # Handle medic ability
        if hasattr(played_card, 'ability') and played_card.ability == Ability.MEDIC and view:
            view.log.append(f"{self.state.name} using medic ability")
            revived_card = self.handle_medic_ability(view)
            if revived_card:
                return [played_card, revived_card]
            
        return played_card

    def handle_spy_ability(self):
        """Draw 2 cards when spy is played"""
        card_ids = self.state.draw(2)
        return [self.card_loader.get_card_by_id(cid) for cid in card_ids]

    def handle_medic_ability(self, view) -> AbstractCard:
        """Handle medic ability by allowing resurrection of a card from graveyard"""
        graveyard = self.get_graveyard()
        if not graveyard:
            view.log.append("Graveyard is empty - no cards to revive")
            return None

        # Filter to only show unit cards that can be revived
        revivable_cards = [(i, card) for i, card in enumerate(graveyard)
                          if isinstance(card, UnitCard) and not isinstance(card, HeroCard)]

        if not revivable_cards:
            view.log.append("No valid cards to revive in graveyard")
            return None
            
        # Let player choose card to revive
        choice = view.get_graveyard_card_choice(revivable_cards)
        if choice is None:
            return None
            
        # Get the card ID from graveyard and remove it
        graveyard_cards = self.state.get_graveyard()
        card_id = graveyard_cards[choice]
        self.state.deck.graveyard_remove(choice)  # Remove from deck's graveyard
        return self.card_loader.get_card_by_id(card_id)

    def add_to_graveyard(self, card: AbstractCard):
        """Add a card ID to the graveyard"""
        # Find card ID from the loaded cards
        for card_id, loaded_card in self.card_loader.cards.items():
            if loaded_card == card:
                self.state.discard_card(card_id)
                break

    def get_graveyard(self) -> List[AbstractCard]:
        """Get all cards in graveyard as card objects"""
        return [self.card_loader.get_card_by_id(cid) for cid in self.state.get_graveyard()]

    def lose_life(self) -> bool:
        """Make player lose a life and return True if eliminated"""
        return self.state.lose_life()

    def pass_turn(self):
        """Pass the current turn"""
        self.state.pass_turn()

    def has_passed(self) -> bool:
        """Check if player has passed"""
        return self.state.has_passed()

    def reset_for_round(self):
        """Reset player state for new round"""
        self.state.reset_for_new_round()

    def is_eliminated(self) -> bool:
        """Check if player is eliminated"""
        return self.state.is_eliminated()

    def get_lives(self) -> int:
        """Get current number of lives"""
        return self.state.lives

    @abstractmethod
    def make_move(self, view) -> tuple[AbstractCard, str]:
        card_index = view.get_user_card_choice(self.get_hand())
        if card_index is None:
            return None, None
            
        card = self.play_card(card_index)
        if not card:
            return None, None
            
        row = None
        if hasattr(card, "row"):
            row = view.get_user_row_choice(card)
            
        # For unit cards, row is required
        if hasattr(card, "row") and not row:
            return None, None
            
        row = row or "CLOSE"
        # Check for spy ability using proper attribute access
        if isinstance(card, UnitCard) and card.ability == Ability.SPY:
            drawn_cards = self.handle_spy_ability()
            view.log.append(f"Drew {len(drawn_cards)} cards from spy ability")
                
        return card, row

class HumanController(PlayerController):
    def __init__(self, state: PlayerState):
        super().__init__(state, True)

    def make_move(self, view):
        """Human player move implementation"""
        choice = view.get_user_card_choice(self.get_hand())
        
        # Handle pass action
        if choice == "PASS":
            return "PASS"
            
        # Handle normal card play
        if choice is None:
            return None, None
            
        card = self.play_card(choice, view)  # Pass view here
        if not card:
            return None, None
            
        row = None
        if hasattr(card, "row"):
            row = view.get_user_row_choice(card)
            if not row:
                return None, None
        
        row = row or "CLOSE"
        
        if hasattr(card, 'ability') and card.ability == Ability.SPY:
            drawn_cards = self.handle_spy_ability()
            view.log.append(f"Drew {len(drawn_cards)} cards from spy ability")
                
        return card, row

class AIController(PlayerController):
    def __init__(self, state: PlayerState):
        super().__init__(state, False)

    def make_move(self, view):
        """AI player move implementation"""
        if not self.state.get_hand():
            return None, None
            
        card = self.play_card(0, view)  # Pass view here
        if not card:
            return None, None
            
        row = "CLOSE"
        if hasattr(card, "row") and card.row:
            row = card.row[0].name
            
        # Handle spy ability before returning
        if hasattr(card, 'ability') and card.ability == Ability.SPY:
            drawn_cards = self.handle_spy_ability()
            view.log.append(f"Opponent drew {len(drawn_cards)} cards from spy ability")
            
        return card, row
