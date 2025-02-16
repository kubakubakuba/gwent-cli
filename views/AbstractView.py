from abc import ABC, abstractmethod
from typing import List, Optional
from model.Card import AbstractCard

class AbstractView(ABC):
    """Abstract base class for all view implementations"""
    
    @abstractmethod
    def init_display(self):
        """Initialize the display system"""
        pass
        
    @abstractmethod
    def cleanup_display(self):
        """Clean up the display system"""
        pass
        
    @abstractmethod
    def setup_players(self, player1, player2):
        """Set up player references"""
        pass
        
    @abstractmethod
    def draw_board(self, board, player_score, opponent_score, is_player_turn, player_hand: List[AbstractCard]):
        """Draw the main game board"""
        pass
        
    @abstractmethod
    def get_user_card_choice(self, hand) -> Optional[int]:
        """Get user's card selection"""
        pass
        
    @abstractmethod
    def get_user_row_choice(self, card) -> Optional[str]:
        """Get user's row selection"""
        pass
        
    @abstractmethod
    def get_graveyard_card_choice(self, revivable_cards) -> Optional[int]:
        """Get user's graveyard card selection"""
        pass
        
    @abstractmethod
    def add_log_message(self, message: str):
        """Add message to game log"""
        pass
        
    @abstractmethod
    def handle_resize(self):
        """Handle display resize events"""
        pass

    @abstractmethod
    def handle_events(self, timeout: int = 100):
        """Handle any pending input events with optional timeout"""
        pass
