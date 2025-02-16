from typing import List
import random

class Deck:
    def __init__(self, deck: List[str]):
        self.deck = deck.copy()  # Changed from self.cards to self.deck
        random.shuffle(self.deck)  # Shuffle the deck
        self.hand = []
        self.graveyard = []
        
        # Draw initial hand
        self.take_cards(10)  # Draw 10 cards at start

    def take_cards(self, n: int) -> List[str]:
        if n > len(self.deck):
            n = len(self.deck)
        cards = self.deck[:n]
        self.hand.extend(cards)
        self.deck = self.deck[n:]
        return cards
    
    def play_card(self, card: str):
        self.hand.remove(card)

    def discard_card(self, card: str):
        self.graveyard.append(card)
    
    def get_hand(self) -> List[str]:
        return self.hand
    
    def get_graveyard(self) -> List[str]:
        return self.graveyard


