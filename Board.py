from Card import UnitCard, HeroCard, WeatherCard, Weather, Ability, WeatherEffect, AbstractCard  # Add explicit import
from typing import List
class Board:

    def __init__(self, rows = ("CLOSE", "RANGED", "SIEGE")):
        self.player = {row: [] for row in rows}
        self.enemy = {row: [] for row in rows}
        self.row_multiplier_player = {row: 1 for row in rows}
        self.row_multiplier_enemy = {row: 1 for row in rows}
        self.weather = []
        self.player_passed = False
        self.enemy_passed = False
        self._enemy_hand_reference = None  # Initialize reference in __init__

    def clear_board(self):
        """Clear the battlefield for next round"""
        rows = self.player.keys()
        self.player = {row: [] for row in rows}
        self.enemy = {row: [] for row in rows}
        self.row_multiplier_player = {row: 1 for row in rows}
        self.row_multiplier_enemy = {row: 1 for row in rows}
        self.weather = []
        self.player_passed = False
        self.enemy_passed = False
    
    def get_value_of_row(self, player, row_multiplier, row):
        # Returns the total value of the player's rows calculates the weather effect. If regular cards and weather cards are in the same row, the value of the card is 1 if not a hero
        
        value = 0
        affected_rows = [ WeatherEffect[weather] for weather in self.weather]
        affected_by_weather = False
        multiplier = row_multiplier[row]
        if row in affected_rows:
            affected_by_weather = True
        for card in player[row]:
            if issubclass(type(card), UnitCard):
                if affected_by_weather and not card.is_hero():
                    value += 1 * multiplier
                else:
                    value += card.value * multiplier
            elif issubclass(type(card), HeroCard):
                value += card.value

        return value
    
    def get_player_value(self):
        return sum([self.get_value_of_row(self.player, self.row_multiplier_player, row) for row in self.player])
    
    def get_enemy_value(self):
        return sum([self.get_value_of_row(self.enemy, self.row_multiplier_enemy, row) for row in self.enemy])
    
    def get_player_row_Value(self, row):
        return self.get_value_of_row(self.player, self.row_multiplier_player, row)
    
    def get_enemy_row_Value(self, row):
        return self.get_value_of_row(self.enemy, self.row_multiplier_enemy, row)
    
    def get_value(self, is_player):
        return self.get_player_value() if is_player else self.get_enemy_value()
    
    def get_row_value(self, is_player, row):
        return self.get_player_row_Value(row) if is_player else self.get_enemy_row_Value(row)

    def add_card_to_row(self, card, is_player, row):
        # Check for spy using proper attribute access
        if isinstance(card, UnitCard) and card.ability == Ability.SPY:
            if is_player:
                self.enemy[row].append(card)
            else:
                self.player[row].append(card)
            return True
            
        # Normal card placement
        if is_player:
            self.player[row].append(card)
        else:
            self.enemy[row].append(card)
        return False
    
    def add_value_multiplier_card(self, card, is_player, row):
        if is_player:
            self.row_multiplier_player[row] = card.value
        else:
            self.row_multiplier_enemy[row] = card.value

    def play_weather(self, weather: WeatherCard):
        if weather.type == Weather.CLEAR:
            self.clear_weather()
        else:
            self.weather.append(weather.type)
    
    def clear_weather(self):
        self.weather = []

    def destroy_strongest_card(self):

        players = [self.player, self.enemy]

        # get largest value
        largest = 0
        for player in players:
            for row in player:
                for card in player[row]:
                    if issubclass(type(card), UnitCard):
                        if card.value > largest:
                            largest = card.value

        # remove cards with largest value
        for player in players:
            for row in player:
                for card in player[row]:
                    if issubclass(type(card), UnitCard):
                        if card.value == largest:
                            player[row].remove(card)
                            break
    
    def destroy_strongest_card_in_row(self, is_player, row):
        player = self.player if is_player else self.enemy
        largest = 0
        for card in player[row]:
            if issubclass(type(card), UnitCard):
                if card.value > largest:
                    largest = card.value
        
        for card in player[row]:
            if issubclass(type(card), UnitCard):
                if card.value == largest:
                    player[row].remove(card)
                    break

    def get_enemy_hand(self) -> List[AbstractCard]:
        """Get reference to enemy hand for display only"""
        return self._enemy_hand_reference or []

    def set_enemy_hand(self, hand: List[AbstractCard]):
        """Temporarily store reference to enemy hand for display"""
        self._enemy_hand_reference = hand

