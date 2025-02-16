from Player import PlayerState
from Board import Board
from BoardView import BoardView
from Player import HumanController, AIController
from CardLoader import CardLoader
import random
import curses
from typing import List
from Card import UnitCard, WeatherCard, SpecialCard, Ability
import traceback  # Add this import

class GwentGame:
    def __init__(self, view_config=None):
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
        self.view = BoardView(view_config)
        self.player1 = HumanController(player_state)
        self.player2 = AIController(ai_state)
        
        # Give view access to player controllers
        self.view.setup_players(self.player1, self.player2)
        
        self.is_player_turn = True
        self.running = True
        self.player_score = 0
        self.opponent_score = 0

    def create_basic_deck(self) -> List[str]:
        """Create a basic deck with 22 unit cards and 5 special/weather cards"""
        all_cards = self.card_loader.get_all_card_ids()
        
        # Filter cards by type and ability
        unit_cards = []
        spy_cards = []
        special_cards = []
        weather_cards = []
        
        for card_id in all_cards:
            card = self.card_loader.get_card_by_id(card_id)
            if isinstance(card, UnitCard):
                if hasattr(card, 'ability') and card.ability == Ability.SPY:
                    spy_cards.append(card_id)
                elif card.value > 0:  # Only cards with value
                    unit_cards.append(card_id)
            elif isinstance(card, WeatherCard):
                weather_cards.append(card_id)
            elif isinstance(card, SpecialCard):
                special_cards.append(card_id)

        # Select cards for deck
        deck = []
        # Add spy cards first (at least 1 if available)
        if spy_cards:
            deck.extend(random.sample(spy_cards, min(2, len(spy_cards))))
            
        # Fill remaining unit slots
        remaining_unit_slots = 22 - len(deck)
        if len(unit_cards) >= remaining_unit_slots:
            deck.extend(random.sample(unit_cards, remaining_unit_slots))
            
        # Add special and weather cards
        if len(special_cards) >= 3:
            deck.extend(random.sample(special_cards, 3))
        if len(weather_cards) >= 2:
            deck.extend(random.sample(weather_cards, 2))
            
        return deck

    def run(self):
        try:
            self.view.init_curses()
            print("\033[6;5m") # Request monospace font mode
            self.view.draw_board(self.board, 0, 0, self.is_player_turn, self.player1.get_hand())
            
            while self.running:
                try:
                    self.player_score = self.board.get_player_value()
                    self.opponent_score = self.board.get_enemy_value()
                    
                    if self.is_player_turn:
                        self.handle_player_turn()
                    else:
                        self.handle_ai_turn()
                    
                    # Check if round should end
                    if (self.board.player_passed and self.board.enemy_passed) or \
                       (not self.player1.get_hand() and not self.player2.get_hand()):
                        self.handle_round_end()
                    
                    self.handle_input()
                        
                except Exception as e:
                    self.view.end_curses()
                    print(f"Error: {str(e)}")
                    print("Traceback:")
                    traceback.print_exc()
                    break
                    
        except Exception as e:
            self.view.end_curses()
            print(f"Error: {str(e)}")
            print("Traceback:")
            traceback.print_exc()
        finally:
            self.end_game()

    def handle_round_end(self):
        """Handle end of round logic"""
        player_score = self.board.get_player_value()
        opponent_score = self.board.get_enemy_value()
        
        # Determine round winner and update lives
        if player_score > opponent_score:
            self.player2.lose_life()
            self.view.log.append("Player 1 won the round!")
        elif opponent_score > player_score:
            self.player1.lose_life()
            self.view.log.append("Player 2 won the round!")
        else:
            # On tie, both lose a life
            self.player1.lose_life()
            self.player2.lose_life()
            self.view.log.append("Round ended in a tie!")
            
        # Check if game should end
        if self.player1.is_eliminated() or self.player2.is_eliminated():
            self.running = False
        else:
            # Reset for next round
            self.board.clear_board()
            self.player1.reset_for_round()
            self.player2.reset_for_round()
            self.view.log.append("Starting new round...")

    def handle_player_turn(self):
        self.board.set_enemy_hand(self.player2.get_hand())
        self.view.draw_board(self.board, self.player_score, self.opponent_score, 
                           self.is_player_turn, self.player1.get_hand())
                           
        if not self.player1.get_hand() or self.player1.has_passed():
            self.player1.pass_turn()
            self.board.player_passed = True
            self.is_player_turn = False
            # Refresh display after passing
            self.refresh_display()
            return

        move_result = self.player1.make_move(self.view)
        
        # Handle pass action first
        if move_result == "PASS":
            self.player1.pass_turn()
            self.board.player_passed = True
            self.view.log.append("Player 1 passed")
            self.is_player_turn = False
            # Refresh display after passing
            self.refresh_display()
            return
            
        # Only try to unpack if it's not a pass
        if isinstance(move_result, tuple):
            card, row = move_result
            if card:
                self.board.add_card_to_row(card, True, row or "CLOSE")
                self.view.log.append(f"Player 1 played {card.name}")
                self.is_player_turn = False
                # Refresh display after playing card
                self.refresh_display()

    def handle_ai_turn(self):
        if not self.player2.get_hand() or self.player2.has_passed():
            self.player2.pass_turn()
            self.board.enemy_passed = True
            self.is_player_turn = True
            # Refresh display after passing
            self.refresh_display()
            return
            
        curses.napms(1000)
        card, row = self.player2.make_move(self.view)
        if card:
            self.board.add_card_to_row(card, False, row or "CLOSE")
            self.view.log.append(f"Player 2 played {card.name}")
            self.is_player_turn = True
            # Refresh display after playing card
            self.refresh_display()

    def refresh_display(self):
        """Update the display with current game state"""
        self.player_score = self.board.get_player_value()
        self.opponent_score = self.board.get_enemy_value()
        self.board.set_enemy_hand(self.player2.get_hand())
        self.view.draw_board(self.board, self.player_score, self.opponent_score,
                           self.is_player_turn, self.player1.get_hand())

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

# Example usage:
if __name__ == "__main__":
    # Optional: customize view
    config = {
        'card_width': 12,
        'card_spacing': 15,
        'battlefield_spacing': 14,
        'max_visible_cards': 6,
        'log_lines': 4
    }
    game = GwentGame(config)
    game.run()
