from Player import PlayerState
from Board import Board
from BoardView import BoardView
from Player import HumanController, AIController
from CardLoader import CardLoader
import random
import curses
from typing import List
from Card import UnitCard, WeatherCard, SpecialCard

class GwentGame:
    def __init__(self):
        # Get singleton instance
        self.card_loader = CardLoader.get_instance()
        
        # Create basic decks
        player_deck = self.create_basic_deck()
        ai_deck = self.create_basic_deck()
        
        # Create player states
        player_state = PlayerState("Player", "NEUTRAL", player_deck, None)
        ai_state = PlayerState("AI", "NEUTRAL", ai_deck, None)
        
        # Initialize game components
        self.board = Board()
        self.view = BoardView()
        self.human = HumanController(player_state)
        self.ai = AIController(ai_state)
        self.is_player_turn = True
        self.running = True
        self.player_score = 0
        self.opponent_score = 0

    def create_basic_deck(self) -> List[str]:
        """Create a basic deck with 22 unit cards and 5 special/weather cards"""
        all_cards = self.card_loader.get_all_card_ids()
        
        # Filter cards by type
        unit_cards = []
        special_cards = []
        weather_cards = []
        
        for card_id in all_cards:
            card = self.card_loader.get_card_by_id(card_id)
            if isinstance(card, UnitCard) and card.value > 0:  # Only cards with value
                unit_cards.append(card_id)
            elif isinstance(card, WeatherCard):
                weather_cards.append(card_id)
            elif isinstance(card, SpecialCard):
                special_cards.append(card_id)

        # Select cards for deck
        deck = []
        if len(unit_cards) >= 22:
            deck.extend(random.sample(unit_cards, 22))
        if len(special_cards) >= 3:
            deck.extend(random.sample(special_cards, 3))
        if len(weather_cards) >= 2:
            deck.extend(random.sample(weather_cards, 2))
            
        return deck

    def run(self):
        try:
            self.view.init_curses()
            self.view.draw_board(self.board, 0, 0, self.is_player_turn, self.human.get_hand())
            
            while self.running:
                try:
                    self.player_score = self.board.get_player_value()
                    self.opponent_score = self.board.get_enemy_value()
                    
                    if self.is_player_turn:
                        self.handle_player_turn()
                    else:
                        self.handle_ai_turn()
                    
                    if not self.human.get_hand() and not self.ai.get_hand():
                        self.running = False
                        break
                    
                    self.handle_input()
                        
                except curses.error:
                    continue
                    
        except Exception as e:
            self.view.end_curses()
            print(f"Error: {str(e)}")
        finally:
            self.end_game()

    def handle_player_turn(self):
        self.view.draw_board(self.board, self.player_score, self.opponent_score, 
                           self.is_player_turn, self.human.get_hand())
        card, row = self.human.make_move(self.view)  # Changed from play_card to make_move
        if card:
            self.board.add_card_to_row(card, True, row or "CLOSE")
            self.view.log.append(f"Player played {card.name}")
            self.is_player_turn = False

    def handle_ai_turn(self):
        curses.napms(1000)
        card, row = self.ai.make_move(self.view)  # Changed from play_card to make_move
        if card:
            self.board.add_card_to_row(card, False, row or "CLOSE")
            self.view.log.append(f"Opponent played {card.name}")
            self.is_player_turn = True

    def handle_input(self):
        self.view.stdscr.timeout(100)
        key = self.view.stdscr.getch()
        if key == curses.KEY_RESIZE:
            self.view.max_y, self.view.max_x = self.view.stdscr.getmaxyx()

    def end_game(self):
        try:
            self.view.end_curses()
        except:
            pass
        winner = "Player" if self.player_score >= self.opponent_score else "Opponent"
        print(f"Game Over! Winner: {winner}")

if __name__ == "__main__":
    game = GwentGame()
    game.run()
