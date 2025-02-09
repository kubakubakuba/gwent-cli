from typing import List
from Card import Card
import random

class Deck:
	def __init__(self, deck: List[str]):
		self.cards: List[str] = deck # List of cards in the by ID
		self.hand: List[str] = []
		self.graveyard: List[str] = []
		self.deck: List[str] = random.shuffle(deck)
	
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
	

		