import curses
from typing import List, Optional
from model.Card import AbstractCard, Ability, HeroCard, UnitCard, WeatherCard, SpecialCard, Weather, Special
from controller.Player import INITIAL_LIVES  # Import the constant
from .AbstractView import AbstractView

class BoardView(AbstractView):  # Inherit from AbstractView
    # Default view configuration
    DEFAULT_CONFIG = {
        'card_width': 10,          # Width of card content (excluding borders)
        'card_spacing': 14,        # Space between cards in hand
        'battlefield_spacing': 12,  # Space between cards on battlefield
        'max_visible_cards': 5,    # Maximum number of visible cards in hand
        'log_lines': 3,           # Number of visible log lines
        'log_width': 30,  # Width of the log section
    }

    def __init__(self, config=None):
        self.stdscr = None
        self.log = []
        self.hand_offset = 0  # For scrolling hand cards
        self.max_y = 0
        self.max_x = 0
        self.command_line = ""
        self.hand_selected = 0  # Currently selected card in hand
        self.board = None
        self.player_score = 0
        self.opponent_score = 0
        self.is_player_turn = True
        self.weather = []  # Default weather state
        self.player1 = None
        self.player2 = None
        self.current_line = 0  # Add line tracker
        self.pad = None  # Add pad for double buffering
        self.screen_too_small = False  # Add flag for screen size warning
        
        # Initialize configuration
        self.config = self.DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)

    def init_curses(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        self.stdscr.keypad(True)
        
        # Force the terminal to use a monospace font
        curses.use_default_colors()
        
        # Initialize colors after starting curses
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)    # Selected card
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Hero card
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_RED)     # Close combat
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_GREEN)   # Ranged
        curses.init_pair(5, curses.COLOR_BLACK, curses.COLOR_CYAN) # Siege
        
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        
        # Check screen size but don't crash
        self.screen_too_small = (self.max_y < 30 or self.max_x < 80)
        
        # Create pad slightly larger than screen
        self.pad = curses.newpad(self.max_y + 1, self.max_x + 1)
        self.pad.keypad(True)

    def end_curses(self):
        if self.pad:
            del self.pad
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def setup_players(self, player1, player2):
        """Set up references to player controllers"""
        self.player1 = player1
        self.player2 = player2

    def draw_board(self, board, player_score, opponent_score, is_player_turn, player_hand: List[AbstractCard]):
        try:
            if self.screen_too_small:
                self.pad.clear()
                warning = "Terminal window too small. Minimum size: 80x30"
                size_info = f"Current size: {self.max_x}x{self.max_y}"
                self.safe_addstr(0, 0, warning)
                self.safe_addstr(1, 0, size_info)
                self.safe_addstr(3, 0, "Press any key to try again or q to quit")
                self.refresh_screen()
                
                key = self.pad.getch()
                if key in [ord('q'), ord('Q')]:
                    raise KeyboardInterrupt
                    
                # Check if window has been resized
                self.max_y, self.max_x = self.stdscr.getmaxyx()
                self.screen_too_small = (self.max_y < 30 or self.max_x < 80)
                if not self.screen_too_small:
                    # Recreate pad with new size
                    self.pad = curses.newpad(self.max_y + 1, self.max_x + 1)
                    self.pad.keypad(True)
                return
            
            # Store the board reference and scores
            self.board = board
            self.player_score = player_score
            self.opponent_score = opponent_score
            self.is_player_turn = is_player_turn
            
            self.pad.clear()  # Clear pad instead of screen
            
            # Calculate game area width and log area width
            game_area_width = self.max_x - self.config['log_width'] - 3  # -3 for borders and separator
            log_area_start = game_area_width + 2  # +2 for border and separator
            
            # Draw vertical separator
            for y in range(0, self.max_y):
                self.safe_addstr(y, game_area_width + 1, "│")
            
            # Draw main game area (left side)
            self.safe_addstr(0, 0, "+" + "-" * (game_area_width) + "+")
            self.safe_addstr(self.max_y-1, 0, "+" + "-" * (game_area_width) + "+")

            # Draw log area (right side)
            self.safe_addstr(0, log_area_start, "+" + "-" * (self.config['log_width'] - 1) + "+")
            self.safe_addstr(self.max_y-1, log_area_start, "+" + "-" * (self.config['log_width'] - 1) + "+")
            
            # Title
            title = "GWENT CLI"
            self.safe_addstr(1, (game_area_width - len(title)) // 2, title)
            
            # Weather and turn info
            weather_str = ", ".join([w.name for w in (board.weather if board else [])]) or "Clear"
            self.safe_addstr(2, 2, f"Weather: [{weather_str}]")
            turn_str = "Player" if is_player_turn else "Opponent"
            self.safe_addstr(2, game_area_width - 20, f"Turn: {turn_str}")
            
            # Scores
            player1_lives = "O" * self.player1.get_lives() + "X" * (INITIAL_LIVES - self.player1.get_lives())
            player2_lives = "O" * self.player2.get_lives() + "X" * (INITIAL_LIVES - self.player2.get_lives())
            self.safe_addstr(3, 2, f"Player 2 Score: {opponent_score} Lives: [{player2_lives}] (Cards: {len(self.board.get_enemy_hand())})")
            self.safe_addstr(3, game_area_width - 45, f"Player 1 Score: {player_score} Lives: [{player1_lives}] (Cards: {len(player_hand)})")
            
            # Reset line tracker
            self.current_line = 4  # Start after header area
            
            # Draw Player 2's battlefield (top)
            self.current_line = self.draw_battlefield(self.current_line + 1, board.enemy, False, 
                                                    ["SIEGE", "RANGED", "CLOSE"], 
                                                    curses.color_pair(3), game_area_width)
            
            # Add separator space
            self.current_line += 1
            
            # Draw Player 1's battlefield (bottom)
            self.current_line = self.draw_battlefield(self.current_line + 1, board.player, True,
                                                    ["CLOSE", "RANGED", "SIEGE"],
                                                    curses.color_pair(4), game_area_width)
            
            # Draw game log in right panel
            self.draw_log(1, log_area_start)
            
            # Draw hand at dynamic position with remaining space
            hand_position = min(self.current_line + 2, self.max_y - 10)  # Ensure space for hand
            self.draw_hand(hand_position, player_hand, game_area_width)
            
            # Draw bottom frame
            self.safe_addstr(self.max_y-1, 0, "+" + "-" * (game_area_width) + "+")
            
            self.refresh_screen()  # Single refresh at the end
            
        except curses.error:
            pass  # Ignore curses errors from writing outside window

    def safe_addstr(self, y, x, string, color_pair=0):
        """Safely add a string to the screen with optional color"""
        try:
            if y < self.max_y and x < self.max_x:
                remaining_space = self.max_x - x - 1
                if remaining_space > 0:
                    self.pad.addstr(y, x, string[:remaining_space], color_pair)
        except curses.error:
            pass

    def refresh_screen(self):
        """Refresh the screen using the pad"""
        try:
            self.pad.refresh(0, 0, 0, 0, self.max_y - 1, self.max_x - 1)
        except curses.error:
            pass

    def draw_battlefield(self, start_line: int, rows: dict, is_player: bool, row_order: List[str], base_color_pair, max_width: int) -> int:
        """Draw battlefield and return the next available line number"""
        current_line = start_line
        
        owner = "Your" if is_player else "Opponent"
        self.safe_addstr(current_line, 2, f"{owner} Battlefield:")
        current_line += 1

        # Color map for different rows
        row_colors = {
            "CLOSE": curses.color_pair(3),
            "RANGED": curses.color_pair(4),
            "SIEGE": curses.color_pair(5)
        }
        
        for row_name in row_order:
            if current_line >= self.max_y - 2:
                break
                
            # Add extra spacing before each row
            current_line += 1
            
            cards = rows[row_name]
            value = sum(card.value for card in cards if hasattr(card, 'value'))
            color = row_colors[row_name]
            
            # Draw row header with color
            row_str = f"[{row_name}] Value: {value}"
            self.safe_addstr(current_line, 2, " " * (max_width - 4), color)
            self.safe_addstr(current_line, 2, row_str, color)
            
            if cards:
                current_line += 1
                # Draw cards line with color
                self.safe_addstr(current_line, 2, " " * (max_width - 4), color)
                card_str = ""
                for card in cards:
                    name_width = self.config['battlefield_spacing']
                    if isinstance(card, HeroCard):
                        card_str += f"╣{card.name[:name_width]:<{name_width}}╠ "
                    else:
                        card_str += f"[{card.name[:name_width]:<{name_width}}] "
                self.safe_addstr(current_line, 4, card_str, color)
            else:
                current_line += 1
                # Draw empty line with color
                self.safe_addstr(current_line, 2, " " * (max_width - 4), color)
            
            current_line += 1  # Space after each row
            
        return current_line  # Return the next available line

    def draw_hand(self, start_line: int, hand: List[AbstractCard], max_width: int):
        if start_line >= self.max_y - 3:
            return
        
        # Clear the hand area first
        for y in range(start_line, start_line + 8):  # Height of card display + scroll message
            self.safe_addstr(y, 2, " " * (max_width - 4))  # Clear the line
            
        # Draw hand title with scroll indicators
        title = "Your Hand:"
        if len(hand) > self.config['max_visible_cards']:
            if self.hand_offset > 0:
                title = "← " + title
            if self.hand_offset + self.config['max_visible_cards'] < len(hand):
                title = title + " →"
        self.safe_addstr(start_line, 2, title)

        if not hand:
            self.safe_addstr(start_line + 1, 4, "No cards")
            return

        # Add card count indicator
        card_count = f"({self.hand_offset + 1}-{min(self.hand_offset + self.config['max_visible_cards'], len(hand))}/{len(hand)})"
        self.safe_addstr(start_line, len(title) + 4, card_count)
            
        visible_cards = hand[self.hand_offset:self.hand_offset + self.config['max_visible_cards']]
        for i, card in enumerate(visible_cards):
            x_pos = 4 + i * self.config['card_spacing']
            
            # Calculate card dimensions
            width = self.config['card_width']
            border_width = width + 2  # Add 2 for borders
            
            # Draw card box with configurable width
            is_hero = isinstance(card, HeroCard)
            border_top = "╔" + "═" * width + "╗" if is_hero else "┌" + "─" * width + "┐"
            border_side = "║" if is_hero else "│"
            border_bottom = "╚" + "═" * width + "╝" if is_hero else "└" + "─" * width + "┘"
            
            # Draw card frame
            self.safe_addstr(start_line + 1, x_pos, border_top)
            self.safe_addstr(start_line + 2, x_pos, f"{border_side}{card.name[:width]:<{width}}{border_side}")
            
            # Value line - exactly 10 chars
            if hasattr(card, 'value'):
                self.safe_addstr(start_line + 3, x_pos, f"{border_side}Val:{card.value:<{width-4}}{border_side}")
            else:
                self.safe_addstr(start_line + 3, x_pos, f"{border_side}{' ' * width}{border_side}")
            
            # Row line - exactly 10 chars
            if hasattr(card, 'row') and card.row:
                row_str = '/'.join(r.name[0] for r in card.row)
                self.safe_addstr(start_line + 4, x_pos, f"{border_side}Row:{row_str:<{width-4}}{border_side}")
            else:
                self.safe_addstr(start_line + 4, x_pos, f"{border_side}{' ' * width}{border_side}")
            
            # Ability/type line - exactly 10 chars
            if hasattr(card, 'ability') and card.ability and card.ability != Ability.NONE:
                ability_str = card.ability.name[:width]
                self.safe_addstr(start_line + 5, x_pos, f"{border_side}{ability_str:<{width}}{border_side}")
            elif hasattr(card, 'type'):
                type_str = card.type.name[:width]
                self.safe_addstr(start_line + 5, x_pos, f"{border_side}{type_str:<{width}}{border_side}")
            else:
                self.safe_addstr(start_line + 5, x_pos, f"{border_side}{' ' * width}{border_side}")
                
            self.safe_addstr(start_line + 6, x_pos, border_bottom)
            
            # If hero, redraw with special borders
            if is_hero:
                self.safe_addstr(start_line + 1, x_pos, "╔" + "═" * width + "╗")
                for y in range(2, 6):
                    # Replace first and last char of each line with hero border
                    self.pad.addch(start_line + y, x_pos, "║")
                    self.pad.addch(start_line + y, x_pos + width + 1, "║")
                self.safe_addstr(start_line + 6, x_pos, "╚" + "═" * width + "╝")
            
            # Apply colors after drawing full card
            if is_hero:
                for y in range(start_line + 1, start_line + 7):
                    self.pad.chgat(y, x_pos, border_width, curses.color_pair(2))
            
            # Highlight selected card
            if i + self.hand_offset == self.hand_selected:
                for y in range(start_line + 1, start_line + 7):
                    self.pad.chgat(y, x_pos, border_width, curses.color_pair(1))
        
        if len(hand) > self.config['max_visible_cards']:
            self.safe_addstr(start_line + 7, 4, "Use <- -> to scroll")

    def get_user_card_choice(self, hand):
        """Get card choice using mouse or keyboard, two-step: select then confirm"""
        self.safe_addstr(self.max_y-2, 2, "Select card: ←→ to move, Enter to confirm, P to pass turn, ESC to cancel")
        self.refresh_screen()
        
        while True:
            event = self.pad.getch()
            
            if event == 27:  # ESC
                return None
                
            elif event == curses.KEY_LEFT:
                if self.hand_selected > 0:
                    self.hand_selected -= 1
                    if self.hand_selected < self.hand_offset:
                        self.hand_offset = self.hand_selected
                    self.draw_board(self.board, self.player_score, self.opponent_score, 
                                  self.is_player_turn, hand)
                    
            elif event == curses.KEY_RIGHT:
                if self.hand_selected < len(hand) - 1:
                    self.hand_selected += 1
                    if self.hand_selected >= self.hand_offset + self.config['max_visible_cards']:
                        self.hand_offset = self.hand_selected - (self.config['max_visible_cards'] - 1)
                    self.draw_board(self.board, self.player_score, self.opponent_score, 
                                  self.is_player_turn, hand)
                    
            elif event == curses.KEY_UP:
                # Select visible card
                if self.hand_selected >= len(hand):
                    self.hand_selected = len(hand) - 1
                self.draw_board(self.board, self.player_score, self.opponent_score, 
                              self.is_player_turn, hand)
                    
            elif event == curses.KEY_DOWN:
                # Deselect card
                self.hand_selected = -1
                self.draw_board(self.board, self.player_score, self.opponent_score, 
                              self.is_player_turn, hand)

            elif event == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, _ = curses.getmouse()
                    if 24 <= my <= 30:  # Hand area
                        for i, _ in enumerate(hand[self.hand_offset:self.hand_offset + self.config['max_visible_cards']]):
                            card_x = 4 + i * self.config['card_spacing']
                            if card_x <= mx < card_x + self.config['card_width'] + 2:
                                self.hand_selected = i + self.hand_offset
                                self.draw_board(self.board, self.player_score, 
                                              self.opponent_score, self.is_player_turn, hand)
                except:
                    pass
                    
            elif event == 10 or event == ord('\n'):  # Enter key - confirm selection
                if 0 <= self.hand_selected < len(hand):
                    return self.hand_selected
                    
            elif event in [ord(str(i)) for i in range(10)]:  # Number keys
                index = int(chr(event))
                if 0 <= index < len(hand):
                    self.hand_selected = index
                    self.draw_board(self.board, self.player_score, self.opponent_score, 
                                  self.is_player_turn, hand)
                    
            elif event == ord('p') or event == ord('P'):  # Pass turn
                return "PASS"

    def get_user_row_choice(self, card):
        """Get row choice based on card's valid rows"""
        if not hasattr(card, 'row') or not card.row:
            return "CLOSE"  # Default row if none specified
            
        valid_rows = [r.name for r in card.row]
        if len(valid_rows) == 1:
            return valid_rows[0]
            
        # Create row shortcuts dictionary
        row_map = {
            ord('c'): 'CLOSE',
            ord('C'): 'CLOSE',
            ord('r'): 'RANGED',
            ord('R'): 'RANGED',
            ord('s'): 'SIEGE',
            ord('S'): 'SIEGE'
        }
        
        # Show available rows with shortcuts
        options = [f"{r[0]}({r.lower()})" for r in valid_rows]
        self.safe_addstr(self.max_y-2, 2, f"Choose row [{'/'.join(options)}]: ")
        self.refresh_screen()
        
        while True:
            try:
                # Get single character instead of string
                key = self.pad.getch()
                
                # Check if key is a valid shortcut
                if key in row_map:
                    row_choice = row_map[key]
                    if row_choice in valid_rows:
                        return row_choice
                    
                # Show error only for non-special keys
                if 32 <= key <= 126:  # Printable characters
                    self.safe_addstr(self.max_y-2, 2, " " * (self.max_x - 4))
                    self.safe_addstr(self.max_y-2, 2, f"Invalid choice! Choose [{'/'.join(options)}]: ")
                    self.refresh_screen()
                
            except:
                continue

    def get_graveyard_card_choice(self, revivable_cards) -> Optional[int]:
        """Display graveyard cards and get user choice for medic ability"""
        if not revivable_cards:
            return None
            
        self.safe_addstr(self.max_y-2, 2, "Choose card to revive (ESC to cancel):")
        
        # Display revivable cards
        y_pos = self.max_y-8  # Show above command line
        for idx, (grave_idx, card) in enumerate(revivable_cards):
            # Show card info on one line
            card_str = f"{idx+1}) {card.name} ({card.value})"
            if hasattr(card, 'row'):
                row_str = '/'.join(r.name[0] for r in card.row)
                card_str += f" [{row_str}]"
            self.safe_addstr(y_pos + idx, 4, card_str)
            
        self.refresh_screen()
        
        while True:
            event = self.pad.getch()
            if event == 27:  # ESC
                return None
            elif event in [ord(str(i)) for i in range(1, len(revivable_cards) + 1)]:
                choice_idx = int(chr(event)) - 1
                if 0 <= choice_idx < len(revivable_cards):
                    return revivable_cards[choice_idx][0]  # Return original graveyard index

    def draw_log(self, start_line: int, x_pos: int):
        """Draw game log in right panel"""
        log_width = self.config['log_width'] - 4  # Account for borders
        
        self.safe_addstr(start_line, x_pos + 2, "Game Log")
        self.safe_addstr(start_line + 1, x_pos + 1, "-" * (log_width + 2))
        
        # Show more log lines since we have vertical space
        visible_lines = self.max_y - start_line - 3
        for i, entry in enumerate(self.log[-visible_lines:]):
            # Word wrap log entries to fit log width
            remaining = entry
            line_num = i
            while remaining and line_num < visible_lines:
                line = remaining[:log_width]
                self.safe_addstr(start_line + 2 + line_num, x_pos + 2, line)
                remaining = remaining[log_width:]
                line_num += 1

    def init_display(self):
        """Implement AbstractView method"""
        self.init_curses()
        
    def cleanup_display(self):
        """Implement AbstractView method"""
        self.end_curses()
        
    def add_log_message(self, message: str):
        """Implement AbstractView method"""
        self.log.append(message)
        
    def handle_resize(self):
        """Implement AbstractView method"""
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        self.screen_too_small = (self.max_y < 30 or self.max_x < 80)
        if not self.screen_too_small:
            self.pad = curses.newpad(self.max_y + 1, self.max_x + 1)
            self.pad.keypad(True)
