import pygame
from typing import List, Optional, Tuple
from model.Card import AbstractCard
from .AbstractView import AbstractView

class PyGameView(AbstractView):
    COLORS = {
        'white': (255, 255, 255),
        'black': (0, 0, 0),
        'gray': (128, 128, 128),
        'blue': (0, 0, 255),
        'red': (255, 0, 0),
        'green': (0, 255, 0),
        'yellow': (255, 255, 0),
    }
    
    def __init__(self, config=None):
        self.width = 1600  # Increased window size
        self.height = 900
        self.game_area_width = self.width - 300  # Reserve 300px for log
        self.screen = None
        self.font = None
        self.log = []
        self.board = None
        self.player1 = None
        self.player2 = None
        self.selected_card = 0
        self.hand_offset = 0
        self.config = {
            'card_width': 200,  # Increased from 120
            'card_height': 280,  # Increased from 180
            'card_spacing': 220, # Increased from 140
            'battlefield_spacing': 130,
            'max_visible_cards': 5,
            'font_size': 20,     # Added font size config
            'title_font_size': 32, # Added title font size
            'line_height': 25,  # Added for better text spacing
            'battlefield_card_height': 80  # Added for battlefield cards
        }
        if config:
            self.config.update(config)
        self.board = None
        self.last_scores = (0, 0)  # Store last known scores
        self.card_scroll_pos = 0  # Add scroll position for hand
        self.row_scroll_positions = {  # Add scroll positions for each row
            'player': {'CLOSE': 0, 'RANGED': 0, 'SIEGE': 0},
            'enemy': {'CLOSE': 0, 'RANGED': 0, 'SIEGE': 0}
        }
        self.scrollbar_dragging = False
        self.scrollbar_drag_start = None
        self.last_click_pos = None
        self.ui_manager = None
        self.hand_container = None
        self.scroll_bar = None

    def init_display(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Gwent PyGame")
        self.font = pygame.font.SysFont('monospace', self.config['font_size'])
        self.title_font = pygame.font.SysFont('monospace', self.config['title_font_size'])
        
    def cleanup_display(self):
        """Clean up pygame and UI properly"""
        if self.ui_manager:
            self.ui_manager.clear_and_reset()
        pygame.quit()

    def setup_players(self, player1, player2):
        self.player1 = player1
        self.player2 = player2

    def draw_board(self, board, player_score, opponent_score, is_player_turn, player_hand):
        """Draw the game board"""
        # Store references
        self.board = board
        self.last_scores = (player_score, opponent_score)
        
        self.screen.fill(self.COLORS['black'])
        
        # Draw vertical separator
        pygame.draw.line(self.screen, self.COLORS['white'], 
                        (self.game_area_width, 0), 
                        (self.game_area_width, self.height))

        # Draw title
        title = self.title_font.render("GWENT CLI", True, self.COLORS['white'])
        self.screen.blit(title, (self.game_area_width // 2 - title.get_width() // 2, 10))

        # Draw scores and lives
        self._draw_stats(player_score, opponent_score, is_player_turn)
        
        # Draw battlefields
        self._draw_battlefields(board)
        
        # Draw hand
        self._draw_hand(player_hand)
        
        # Draw log
        self._draw_log()
        
        # Draw UI last
        pygame.display.flip()

    def _draw_stats(self, player_score, opponent_score, is_player_turn):
        # Draw weather, scores, lives etc.
        weather = self.font.render("Weather: [Clear]", True, self.COLORS['white'])
        self.screen.blit(weather, (10, 50))
        
        turn = self.font.render(f"Turn: {'Player' if is_player_turn else 'Opponent'}", 
                              True, self.COLORS['white'])
        self.screen.blit(turn, (self.game_area_width - 200, 50))
        
        # Add scores and lives...

    def _draw_battlefields(self, board):
        """Improved battlefield drawing"""
        if not board:  # Add safety check
            return
            
        y_offset = 100  # Start higher up
        section_height = (self.height - 400) // 2  # Divide available space between players
        
        for side in ['enemy', 'player']:
            # Draw battlefield title
            title = f"{'Opponent' if side == 'enemy' else 'Your'} Battlefield:"
            text = self.font.render(title, True, self.COLORS['white'])
            self.screen.blit(text, (10, y_offset))
            
            y_offset += 40
            rows = ['SIEGE', 'RANGED', 'CLOSE'] if side == 'enemy' else ['CLOSE', 'RANGED', 'SIEGE']
            rows_data = board.enemy if side == 'enemy' else board.player
            
            # Calculate row height
            row_height = section_height // 3
            
            for row_name in rows:
                # Draw row header with value
                value = sum(card.value for card in rows_data[row_name] if hasattr(card, 'value'))
                row_text = self.font.render(f"[{row_name}] Value: {value}", True, self.COLORS['white'])
                self.screen.blit(row_text, (10, y_offset))
                
                self._draw_battlefield_row(row_name, rows_data[row_name], y_offset, row_height, side == 'player')
                
                y_offset += row_height

            y_offset += 20  # Space between battlefields

    def _draw_battlefield_row(self, row_name, cards, y_offset, row_height, is_player):
        # Draw row background
        pygame.draw.rect(self.screen, self.COLORS['gray'],
                        (10, y_offset + 30, self.game_area_width - 20, row_height - 40), 1)
        
        # Calculate how many cards fit in view
        visible_width = self.game_area_width - 40  # Account for margins and scrollbar
        cards_per_view = visible_width // self.config['battlefield_spacing']
        
        # Get scroll position for this row
        side = 'player' if is_player else 'enemy'
        scroll_pos = self.row_scroll_positions[side][row_name]
        max_scroll = max(0, len(cards) - cards_per_view)
        scroll_pos = min(scroll_pos, max_scroll)
        self.row_scroll_positions[side][row_name] = scroll_pos
        
        # Draw visible cards
        visible_cards = cards[scroll_pos:scroll_pos + cards_per_view]
        card_x = 20
        for card in visible_cards:
            card_text = self.font.render(f"{card.name}({card.value})", True, self.COLORS['white'])
            self.screen.blit(card_text, (card_x, y_offset + 40))
            card_x += self.config['battlefield_spacing']
        
        # Draw scrollbar if needed
        if len(cards) > cards_per_view:
            self._draw_scrollbar(self.game_area_width - 15, y_offset + 30,
                               10, row_height - 40,
                               len(cards), cards_per_view, scroll_pos)

    def _draw_hand(self, hand):
        if not hand:
            return
            
        y_pos = self.height - self.config['card_height'] - 40  # More space from bottom
        
        # Clear hand area
        pygame.draw.rect(self.screen, self.COLORS['black'],
                        (0, y_pos - 30, self.game_area_width, self.config['card_height'] + 70))

        # Draw hand title and cards count
        title = f"Your Hand ({len(hand)} cards)"
        self.screen.blit(self.font.render(title, True, self.COLORS['white']), (10, y_pos - 30))

        # Calculate visible cards
        visible_width = self.game_area_width - 40
        cards_per_view = visible_width // self.config['card_spacing']
        max_scroll = max(0, len(hand) - cards_per_view)
        self.card_scroll_pos = min(self.card_scroll_pos, max_scroll)
        visible_cards = hand[self.card_scroll_pos:self.card_scroll_pos + cards_per_view]

        # Draw scroll indicators if needed
        if self.card_scroll_pos > 0:
            left_arrow = self.font.render("←", True, self.COLORS['white'])
            self.screen.blit(left_arrow, (5, y_pos + self.config['card_height'] // 2))
        if self.card_scroll_pos + cards_per_view < len(hand):
            right_arrow = self.font.render("→", True, self.COLORS['white'])
            self.screen.blit(right_arrow, (self.game_area_width - 20, y_pos + self.config['card_height'] // 2))

        # Draw cards
        for i, card in enumerate(visible_cards):
            x_pos = 10 + i * self.config['card_spacing']
            color = self.COLORS['yellow'] if i + self.card_scroll_pos == self.selected_card else self.COLORS['white']
            
            # Draw card background and border
            pygame.draw.rect(self.screen, self.COLORS['gray'], 
                           (x_pos, y_pos, self.config['card_width'], self.config['card_height']))
            pygame.draw.rect(self.screen, color, 
                           (x_pos, y_pos, self.config['card_width'], self.config['card_height']), 2)

            # Draw card info
            text_x = x_pos + 10
            text_y = y_pos + 10
            line_height = self.config['line_height']

            # Name
            name = self.font.render(card.name[:15], True, color)
            self.screen.blit(name, (text_x, text_y))

            # Value
            if hasattr(card, 'value'):
                value = self.font.render(f"Value: {card.value}", True, color)
                self.screen.blit(value, (text_x, text_y + line_height))

            # Row
            if hasattr(card, 'row') and card.row:
                row_str = '/'.join(r.name[0] for r in card.row)
                row_text = self.font.render(f"Row: {row_str}", True, color)
                self.screen.blit(row_text, (text_x, text_y + line_height * 2))

            # Ability
            if hasattr(card, 'ability') and card.ability:
                ability = self.font.render(str(card.ability.name)[:12], True, color)
                self.screen.blit(ability, (text_x, text_y + line_height * 3))

        # Draw scrollbar if needed
        if len(hand) > cards_per_view:
            self._draw_horizontal_scrollbar(10, y_pos + self.config['card_height'] + 5,
                                         self.game_area_width - 20, 10,
                                         len(hand), cards_per_view,
                                         self.card_scroll_pos)

    def _draw_scrollbar(self, x, y, width, height, total_items, visible_items, scroll_pos):
        """Helper to draw a scrollbar"""
        if total_items <= visible_items:
            return
            
        # Draw scrollbar background
        pygame.draw.rect(self.screen, self.COLORS['gray'], 
                        (x, y, 10, height), 1)
        
        # Calculate thumb size and position
        thumb_height = max(20, (visible_items / total_items) * height)
        thumb_pos = y + (scroll_pos / total_items) * (height - thumb_height)
        
        # Draw thumb
        pygame.draw.rect(self.screen, self.COLORS['white'],
                        (x, thumb_pos, 10, thumb_height))

    def _draw_horizontal_scrollbar(self, x, y, width, height, total_items, visible_items, scroll_pos):
        """Draw horizontal scrollbar"""
        if total_items <= visible_items:
            return

        # Draw scrollbar background
        pygame.draw.rect(self.screen, self.COLORS['gray'],
                        (x, y + height - 10, width, 10), 1)

        # Calculate thumb size and position
        thumb_width = max(40, (visible_items / total_items) * width)
        thumb_x = x + (scroll_pos / (total_items - visible_items)) * (width - thumb_width)

        # Draw thumb
        pygame.draw.rect(self.screen, self.COLORS['white'],
                        (thumb_x, y + height - 10, thumb_width, 10))

        return (thumb_x, y + height - 10, thumb_width, 10)  # Return thumb rect for hit testing

    def _draw_log(self):
        y_pos = 10
        log_x = self.game_area_width + 10
        
        title = self.font.render("Game Log", True, self.COLORS['white'])
        self.screen.blit(title, (log_x, y_pos))
        
        pygame.draw.line(self.screen, self.COLORS['white'],
                        (log_x, y_pos + 25),
                        (self.width - 10, y_pos + 25))
        
        y_pos += 35
        for entry in self.log[-10:]:  # Show last 10 log entries
            text = self.font.render(entry[:25], True, self.COLORS['white'])
            self.screen.blit(text, (log_x, y_pos))
            y_pos += 20

    def get_user_card_choice(self, hand) -> Optional[int]:
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_RETURN:
                        return self.selected_card
                    elif event.key == pygame.K_LEFT:
                        self.selected_card = max(0, self.selected_card - 1)
                    elif event.key == pygame.K_RIGHT:
                        self.selected_card = min(len(hand) - 1, self.selected_card + 1)
                    elif event.key == pygame.K_p:
                        return "PASS"
            
            # Use stored scores when redrawing
            if self.board:  # Only draw if we have a board reference
                self.draw_board(self.board, self.last_scores[0], 
                              self.last_scores[1], True, hand)
            pygame.time.wait(50)  # Add small delay to prevent CPU overuse

    def get_user_row_choice(self, card) -> Optional[str]:
        if not hasattr(card, 'row') or not card.row:
            return "CLOSE"
            
        valid_rows = [r.name for r in card.row]
        if len(valid_rows) == 1:
            return valid_rows[0]
            
        # Show row options at bottom of screen
        text = self.font.render("Choose row (c)lose, (r)anged, (s)iege:", True, self.COLORS['white'])
        self.screen.blit(text, (10, self.height - 30))
        pygame.display.flip()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_c:
                        return "CLOSE"
                    elif event.key == pygame.K_r:
                        return "RANGED"
                    elif event.key == pygame.K_s:
                        return "SIEGE"
                elif event.type == pygame.QUIT:
                    raise KeyboardInterrupt

    def get_graveyard_card_choice(self, revivable_cards) -> Optional[int]:
        if not revivable_cards:
            return None
            
        selection = 0
        while True:
            self.screen.fill(self.COLORS['black'])
            
            text = self.font.render("Choose card to revive (Enter to select, ESC to cancel):", 
                                  True, self.COLORS['white'])
            self.screen.blit(text, (10, 10))
            
            for i, (idx, card) in enumerate(revivable_cards):
                color = self.COLORS['yellow'] if i == selection else self.COLORS['white']
                card_text = f"{i+1}) {card.name} ({card.value})"
                text = self.font.render(card_text, True, color)
                self.screen.blit(text, (10, 40 + i * 25))
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return None
                    elif event.key == pygame.K_RETURN:
                        return revivable_cards[selection][0]
                    elif event.key == pygame.K_UP:
                        selection = max(0, selection - 1)
                    elif event.key == pygame.K_DOWN:
                        selection = min(len(revivable_cards) - 1, selection + 1)

    def add_log_message(self, message: str):
        self.log.append(message)
        
    def handle_resize(self):
        pass  # PyGame window is fixed size

    def handle_events(self, timeout: int = 100):
        """Handle pygame events"""
        clock = pygame.time.Clock()
        clock.tick(60)  # Limit FPS
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)
            elif event.type == pygame.KEYDOWN:
                self._handle_keyboard_event(event)
                
        pygame.time.wait(timeout)

    def _handle_mouse_click(self, event):
        """Handle mouse clicks"""
        if event.button == 1:  # Left click
            mx, my = event.pos
            # Check if click is in hand area
            hand_y = self.height - self.config['card_height'] - 40
            if hand_y <= my <= hand_y + self.config['card_height']:
                # Calculate which card was clicked
                card_idx = (mx - 10) // self.config['card_spacing']
                if 0 <= card_idx < self.config['max_visible_cards']:
                    actual_idx = card_idx + self.card_scroll_pos
                    if actual_idx < len(self.get_hand()):
                        self.selected_card = actual_idx
        elif event.button in (4, 5):  # Mouse wheel
            self._handle_scroll(event.button == 4)

    def _handle_scroll(self, scroll_up: bool):
        """Handle scrolling"""
        if scroll_up:
            self.card_scroll_pos = max(0, self.card_scroll_pos - 1)
        else:
            max_scroll = len(self.get_hand()) - self.config['max_visible_cards']
            self.card_scroll_pos = min(max_scroll, self.card_scroll_pos + 1)

    def _handle_battlefield_scroll(self, mx, my, scroll_amount):
        """Helper to handle battlefield row scrolling"""
        # Calculate row positions and determine which row was clicked
        y_offset = 100
        section_height = (self.height - 400) // 2
        row_height = section_height // 3
        
        for side in ['enemy', 'player']:
            for row_name in ['SIEGE', 'RANGED', 'CLOSE']:
                if y_offset <= my <= y_offset + row_height:
                    self.row_scroll_positions[side][row_name] = max(0, 
                        self.row_scroll_positions[side][row_name] + scroll_amount)
                y_offset += row_height
            y_offset += 20
