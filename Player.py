import asyncio
from Deck import Deck
from typing import List
from abc import ABC, abstractmethod
from CardLoader import CardLoader
from Card import UnitCard, Weather, Special, WeatherCard, SpecialCard, AbstractCard
from Board import Board

INITIAL_LIVES = 2

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

class PlayerController(ABC):
    def __init__(self, state: PlayerState, is_player: bool):
        self.state: PlayerState = state
        self.is_player: bool = is_player
        self.card_loader = CardLoader.get_instance()

    def get_hand(self) -> List[AbstractCard]:
        """Dynamically convert current hand from IDs to card objects"""
        return [self.card_loader.get_card_by_id(cid) for cid in self.state.get_hand()]

    def play_card(self, index: int) -> AbstractCard:
        """Final implementation of card playing - should not be overridden"""
        hand = self.state.get_hand()
        if index >= len(hand):
            return None
            
        card_id = hand[index]
        self.state.play_card(card_id)
        return self.card_loader.get_card_by_id(card_id)

    @abstractmethod
    def make_move(self, view) -> tuple[AbstractCard, str]:
        """Abstract method that each controller must implement for their specific move logic"""
        pass

class HumanController(PlayerController):
    def __init__(self, state: PlayerState):
        super().__init__(state, True)

    def make_move(self, view):
        """Human player move implementation"""
        card_index = view.get_user_card_choice(self.get_hand())
        if card_index is None:
            return None, None
            
        card = self.play_card(card_index)
        if not card:
            return None, None
            
        row = None
        if hasattr(card, "row"):
            row = view.get_user_row_choice(card)
            if not row:
                return None, None
                
        return card, row or "CLOSE"

class AIController(PlayerController):
    def __init__(self, state: PlayerState):
        super().__init__(state, False)

    def make_move(self, view):
        """AI player move implementation"""
        if not self.state.get_hand():
            return None, None
            
        card = self.play_card(0)  # Play first card
        if not card:
            return None, None
            
        row = "CLOSE"
        if hasattr(card, "row") and card.row:
            row = card.row[0].name
            
        return card, row
