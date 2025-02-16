import asyncio
from Deck import Deck
from typing import List
from abc import ABC, abstractmethod
from CardLoader import CardLoader
from Card import UnitCard, Weather, Special, WeatherCard, SpecialCard
from Board import Board

INITIAL_LIVES = 2

class PlayerState():
    def __init__(self, name: str, faction: str, deck: List[str], king: str):
        self.name: str = name
        self.faction: str = faction
        self.deck: Deck = Deck(deck)
        self.king: str = king
        self.lives: int = INITIAL_LIVES
        self.skiped_move: bool = False


    def draw(self, n: int):
        return self.deck.take_cards(n)
    
    def play_card(self, card: str):
        self.deck.play_card(card)

    def discard_card(self, card: str):
        self.deck.discard_card(card)

    def get_hand(self):
        return self.deck.get_hand()

    def get_graveyard(self):
        return self.deck.get_graveyard()

    def lose_life(self):
        self.lives -= 1
        if self.lives <= 0:
            return True
        return False
    
    def __str__(self):
        return self.name
    
class PlayerController(ABC):
    def __init__(self, state: PlayerState, is_player: bool):
        self.state: PlayerState = state
        self.skiped_move: bool = False
        self.is_player: bool = is_player


    def get_hand(self):
        return self.state.get_hand()
    
    def get_graveyard(self):
        return self.state.get_graveyard()
    @abstractmethod
    async def play(self, board: Board):
        raise NotImplemented
    
    def skip_move(self):
        self.skiped_move = True

    def get_skiped_move(self):
        return self.skiped_move
    
    
    def play_card(self, card: str, board: Board, row: int):
        self.state.play_card(card)
        card_obj = CardLoader.get_card_by_id(card)
        
        if issubclass(type(card_obj), WeatherCard):
            board.play_weather(card_obj.type)

        if issubclass(type(card_obj), UnitCard):
            board.add_card_to_row(card_obj, self.is_player, row)
        
        if issubclass(type(card_obj), SpecialCard):
            if card_obj.type == Special.COMMANDERS_HORN:
                board.add_value_multiplier_card(card_obj, self.is_player, row)
            if card_obj.type == Special.SCORCH:
                board.destroy_strongest_card()

class HumanController(PlayerController):
    def __init__(self, state: PlayerState):
        super().__init__(state)
        self.action_taken: bool = False
        self._action_event = asyncio.Event()
    
    def set_action_taken(self):
        self.action_taken = True
        self._action_event.set()

    async def play(self, card: str):
        if self.get_hand().count(card) == 0 or self.get_skiped_move():
            return
        self.action_taken = False
        await self._action_event.wait()
        self._action_event.clear()

    def play_card(self, card: str):
        self.state.play_card(card)
        self.set_action_taken()

    

class AIController(PlayerController):
    def __init__(self, state: PlayerState):
        super().__init__(state)
    
    async def play(self, board: Board):
        await asyncio.sleep(1)
        hand = self.get_hand()
        if len(hand) == 0:
            return
        card = hand[0]
        self.state.play_card(card)
        board.play_card(self.state, card)
