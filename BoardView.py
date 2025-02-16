import curses
from typing import List
from Card import AbstractCard, Ability, HeroCard, UnitCard, WeatherCard, SpecialCard, Weather, Special
from Player import INITIAL_LIVES  # Import the constant

class BoardView:
    # Default view configuration
    DEFAULT_CONFIG = {
        'card_width': 10,          # Width of card content (excluding borders)
        'card_spacing': 14,        # Space between cards in hand
        'battlefield_spacing': 12,  # Space between cards on battlefield
        'max_visible_cards': 5,    # Maximum number of visible cards in hand
        'log_lines': 3,           # Number of visible log lines
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
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Selected card
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Hero card
        
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        
        if self.max_y < 30 or self.max_x < 80:
            self.end_curses()
            raise RuntimeError("Terminal window too small. Minimum size: 80x30\nPlease use a monospace font.")
        
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        curses.mouseinterval(0)

    def end_curses(self):
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
            # Store the board reference and scores
            self.board = board
            self.player_score = player_score
            self.opponent_score = opponent_score
            self.is_player_turn = is_player_turn
            
            self.stdscr.clear()
            
            # Draw frame
            self.safe_addstr(0, 0, "+" + "-" * (self.max_x - 2) + "+")
            
            # Title
            title = "GWENT CLI"
            self.safe_addstr(1, (self.max_x - len(title)) // 2, title)
            
            # Weather and turn info
            weather_str = ", ".join([w.name for w in (board.weather if board else [])]) or "Clear"
            self.safe_addstr(2, 2, f"Weather: [{weather_str}]")
            turn_str = "Player" if is_player_turn else "Opponent"
            self.safe_addstr(2, self.max_x - 20, f"Turn: {turn_str}")
            
            # Scores
            player1_lives = "O" * self.player1.get_lives() + "X" * (INITIAL_LIVES - self.player1.get_lives())
            player2_lives = "O" * self.player2.get_lives() + "X" * (INITIAL_LIVES - self.player2.get_lives())
            self.safe_addstr(3, 2, f"Player 2 Score: {opponent_score} Lives: [{player2_lives}] (Cards: {len(self.board.get_enemy_hand())})")
            self.safe_addstr(3, self.max_x - 45, f"Player 1 Score: {player_score} Lives: [{player1_lives}] (Cards: {len(player_hand)})")
            
            # Battlefields
            self.draw_battlefield(5, board.enemy, False)
            self.draw_battlefield(12, board.player, True)
            
            # Draw game log
            self.draw_log(19)
            
            # Draw hand at the bottom
            self.draw_hand(24, player_hand)
            
            # Draw bottom frame
            self.safe_addstr(self.max_y-1, 0, "+" + "-" * (self.max_x - 2) + "+")
            
            self.stdscr.refresh()
            
        except curses.error:
            pass  # Ignore curses errors from writing outside window

    def safe_addstr(self, y, x, string):
        """Safely add a string to the screen, truncating if necessary"""
        try:
            if y < self.max_y and x < self.max_x:
                remaining_space = self.max_x - x - 1
                if remaining_space > 0:
                    self.stdscr.addstr(y, x, string[:remaining_space])
        except curses.error:
            pass

    def draw_battlefield(self, start_line: int, rows: dict, is_player: bool):
        owner = "Your" if is_player else "Opponent"
        self.safe_addstr(start_line, 2, f"{owner} Battlefield:")
        line = start_line + 1
        
        # Define row order based on player/opponent
        row_order = ["SIEGE", "RANGED", "CLOSE"] if is_player else ["CLOSE", "RANGED", "SIEGE"]
        
        for row_name in row_order:
            if line >= self.max_y - 2:
                break
                
            cards = rows[row_name]
            value = sum(card.value for card in cards if hasattr(card, 'value'))
            self.safe_addstr(line, 2, f"[{row_name}] Value: {value}")
            
            if cards:
                card_str = ""
                for card in cards:
                    # Use special borders for hero cards on battlefield
                    name_width = self.config['battlefield_spacing']
                    if isinstance(card, HeroCard):
                        card_str += f"╣{card.name[:name_width]:<{name_width}}╠ "
                    else:
                        card_str += f"[{card.name[:name_width]:<{name_width}}] "
                self.safe_addstr(line + 1, 4, card_str)
            line += 2

    def draw_hand(self, start_line: int, hand: List[AbstractCard]):
        if start_line >= self.max_y - 3:
            return
        
        # Clear the hand area first
        for y in range(start_line, start_line + 8):  # Height of card display + scroll message
            self.safe_addstr(y, 2, " " * (self.max_x - 4))  # Clear the line
            
        self.safe_addstr(start_line, 2, "Your Hand:")
        if not hand:
            self.safe_addstr(start_line + 1, 4, "No cards")
            return
            
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
                    self.stdscr.addch(start_line + y, x_pos, "║")
                    self.stdscr.addch(start_line + y, x_pos + width + 1, "║")
                self.safe_addstr(start_line + 6, x_pos, "╚" + "═" * width + "╝")
            
            # Apply colors after drawing full card
            if is_hero:
                for y in range(start_line + 1, start_line + 7):
                    self.stdscr.chgat(y, x_pos, border_width, curses.color_pair(2))
            
            # Highlight selected card
            if i + self.hand_offset == self.hand_selected:
                for y in range(start_line + 1, start_line + 7):
                    self.stdscr.chgat(y, x_pos, border_width, curses.color_pair(1))
        
        if len(hand) > self.config['max_visible_cards']:
            self.safe_addstr(start_line + 7, 4, "Use <- -> to scroll")

    def get_user_card_choice(self, hand):
        """Get card choice using mouse or keyboard, two-step: select then confirm"""
        self.safe_addstr(self.max_y-2, 2, "Select card: ←→ to move, Enter to confirm, P to pass turn, ESC to cancel")
        self.stdscr.refresh()
        
        while True:
            event = self.stdscr.getch()
            
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
        self.stdscr.refresh()
        
        while True:
            try:
                # Get single character instead of string
                key = self.stdscr.getch()
                
                # Check if key is a valid shortcut
                if key in row_map:
                    row_choice = row_map[key]
                    if row_choice in valid_rows:
                        return row_choice
                    
                # Show error only for non-special keys
                if 32 <= key <= 126:  # Printable characters
                    self.safe_addstr(self.max_y-2, 2, " " * (self.max_x - 4))
                    self.safe_addstr(self.max_y-2, 2, f"Invalid choice! Choose [{'/'.join(options)}]: ")
                    self.stdscr.refresh()
                
            except:
                continue

    def draw_log(self, start_line: int):
        self.safe_addstr(start_line, 2, "Game Log:")
        for i, entry in enumerate(self.log[-self.config['log_lines']:]):  # Show last log lines based on config
            self.safe_addstr(start_line + i + 1, 4, f"> {entry}")
