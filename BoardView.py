import curses
from typing import List
from Card import AbstractCard

class BoardView:
    def __init__(self):
        self.stdscr = None
        self.log = []
        self.hand_offset = 0  # For scrolling hand cards
        self.max_y = 0
        self.max_x = 0
        self.command_line = ""
        self.hand_selected = 0  # Currently selected card in hand

    def init_curses(self):
        self.stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        self.stdscr.keypad(True)
        self.max_y, self.max_x = self.stdscr.getmaxyx()
        
        if self.max_y < 30 or self.max_x < 80:
            self.end_curses()
            raise RuntimeError("Terminal window too small. Minimum size: 80x30")
        
        curses.mousemask(curses.ALL_MOUSE_EVENTS | curses.REPORT_MOUSE_POSITION)
        curses.mouseinterval(0)
        # Initialize some colors
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Selected card

    def end_curses(self):
        curses.nocbreak()
        self.stdscr.keypad(False)
        curses.echo()
        curses.endwin()

    def draw_board(self, board, player_score, opponent_score, is_player_turn, player_hand: List[AbstractCard]):
        try:
            self.stdscr.clear()
            
            # Draw frame
            self.safe_addstr(0, 0, "+" + "-" * (self.max_x - 2) + "+")
            
            # Title
            title = "GWENT CLI"
            self.safe_addstr(1, (self.max_x - len(title)) // 2, title)
            
            # Weather and turn info
            weather_str = ", ".join([w.name for w in board.weather]) or "Clear"
            self.safe_addstr(2, 2, f"Weather: [{weather_str}]")
            turn_str = "Player" if is_player_turn else "Opponent"
            self.safe_addstr(2, self.max_x - 20, f"Turn: {turn_str}")
            
            # Scores
            self.safe_addstr(3, 2, f"Opponent Score: {opponent_score}")
            self.safe_addstr(3, self.max_x - 20, f"Player Score: {player_score}")
            
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
        
        for row_name, cards in rows.items():
            if line >= self.max_y - 2:
                break
                
            value = sum(card.value for card in cards if hasattr(card, 'value'))
            self.safe_addstr(line, 2, f"[{row_name}] Value: {value}")
            
            if cards:
                card_str = " ".join(f"[{card.name[:8]}]" for card in cards)
                self.safe_addstr(line + 1, 4, card_str)
            line += 2

    def draw_hand(self, start_line: int, hand: List[AbstractCard]):
        if start_line >= self.max_y - 3:
            return
            
        self.safe_addstr(start_line, 2, "Your Hand:")
        if not hand:
            self.safe_addstr(start_line + 1, 4, "No cards")
            return
            
        visible_cards = hand[self.hand_offset:self.hand_offset + 5]
        card_str = " ".join(f"[{i+self.hand_offset}:{card.name[:8]}]" for i, card in enumerate(visible_cards))
        self.safe_addstr(start_line + 1, 4, card_str)
        
        if len(hand) > 5:
            self.safe_addstr(start_line + 2, 4, "Use <- -> to scroll")

    def get_user_card_choice(self, hand):
        """Get card choice using mouse or keyboard"""
        self.safe_addstr(self.max_y-2, 2, "Click on a card or press [0-9] to select, Enter to confirm, ESC to cancel")
        self.stdscr.refresh()
        
        while True:
            event = self.stdscr.getch()
            
            if event == 27:  # ESC
                return None
                
            if event == curses.KEY_MOUSE:
                try:
                    _, mx, my, _, _ = curses.getmouse()
                    # Check if click is in hand area
                    if my == self.max_y-4:  # Hand row
                        for i, card in enumerate(hand[self.hand_offset:self.hand_offset + 5]):
                            card_x = 4 + i * 12  # Approximate card width
                            if card_x <= mx < card_x + 11:
                                return i + self.hand_offset
                except:
                    pass
                    
            elif event in [ord(str(i)) for i in range(10)]:
                index = int(chr(event))
                if 0 <= index < len(hand):
                    return index
                    
            elif event == curses.KEY_ENTER or event == 10:
                if 0 <= self.hand_selected < len(hand):
                    return self.hand_selected

            elif event == curses.KEY_LEFT:
                if self.hand_offset > 0:
                    self.hand_offset -= 1
                    self.draw_hand(self.max_y-4, hand)
                    
            elif event == curses.KEY_RIGHT:
                if self.hand_offset + 5 < len(hand):
                    self.hand_offset += 1
                    self.draw_hand(self.max_y-4, hand)

    def get_user_row_choice(self, card):
        """Get row choice based on card's valid rows"""
        if not hasattr(card, 'row') or not card.row:
            return "CLOSE"  # Default row if none specified
            
        valid_rows = [r.name for r in card.row]
        if len(valid_rows) == 1:
            return valid_rows[0]
            
        self.safe_addstr(self.max_y-2, 2, f"Choose row [{'/'.join(valid_rows)}]: ")
        self.stdscr.refresh()
        
        while True:
            choice = self.stdscr.getstr().decode('utf-8').upper()
            if choice in valid_rows:
                return choice

    def draw_log(self, start_line: int):
        self.safe_addstr(start_line, 2, "Game Log:")
        for i, entry in enumerate(self.log[-3:]):  # Show last 3 log entries
            self.safe_addstr(start_line + i + 1, 4, f"> {entry}")
