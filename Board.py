from Card import *

class Board:

    def __init__(self, rows = ("CLOSE", "RANGED", "SIEGE")):
        self.player = {row: [] for row in rows}
        self.enemy = {row: [] for row in rows}
        self.row_multiplier_player = {row: 1 for row in rows}
        self.row_multiplier_enemy = {row: 1 for row in rows}
        self.weather = []
    
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
    
    def get_player_row_

            