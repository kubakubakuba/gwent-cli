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
        self.width = 1600
        self.height = 900
        self.game_area_width = self.width - 300
        self.screen = None
        self.font = None
        self.log = []
        self.board = None
        self.player1 = None
        self.player2 = None
        self.selected_card = 0
        self.hand_offset = 0
        # Change these parameters to adjust card sizes
        self.config = {
            'card_width': 300,             # Wider hand cards
            'card_height': 280,
            'card_spacing': 320,           # Adjust spacing for wider cards
            'battlefield_spacing': 170,    # Adjust spacing on battlefield
            'max_visible_cards': 5,
            'font_size': 20,
            'title_font_size': 32,
            'line_height': 25,
            'battlefield_card_height': 80,
            'battlefield_card_width': 160   # Wider battlefield cards
        }
        if config:
            self.config.update(config)
        self.board = None
        self.last_scores = (0, 0)
        self.card_scroll_pos = 0
        self.row_scroll_positions = {
            'player': {'CLOSE': 0, 'RANGED': 0, 'SIEGE': 0},
            'enemy': {'CLOSE': 0, 'RANGED': 0, 'SIEGE': 0}
        }
        self.scrollbar_dragging = False
        self.scrollbar_drag_start = 0
        self.last_click_pos = None
        self.ui_manager = None
        self.hand_container = None
        self.scroll_bar = None
        self.player_hand = []
        self.hand_scrollbar_thumb_rect = None
        self.hand_scrollbar_track_rect = None

    def init_display(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Gwent PyGame")
        self.font = pygame.font.SysFont('monospace', self.config['font_size'])
        self.title_font = pygame.font.SysFont('monospace', self.config['title_font_size'])
        
    def cleanup_display(self):
        if self.ui_manager:
            self.ui_manager.clear_and_reset()
        pygame.quit()

    def setup_players(self, player1, player2):
        self.player1 = player1
        self.player2 = player2

    def draw_board(self, board, player_score, opponent_score, is_player_turn, player_hand):
        self.player_hand = player_hand
        self.board = board
        self.last_scores = (player_score, opponent_score)
        
        self.screen.fill(self.COLORS['black'])
        
        pygame.draw.line(self.screen, self.COLORS['white'], 
                         (self.game_area_width, 0), 
                         (self.game_area_width, self.height))

        title = self.title_font.render("GWENT CLI", True, self.COLORS['white'])
        self.screen.blit(title, (self.game_area_width // 2 - title.get_width() // 2, 10))

        self._draw_stats(player_score, opponent_score, is_player_turn)
        self._draw_battlefields(board)
        self._draw_hand(player_hand)
        self._draw_log()
        
        pygame.display.flip()

    def _draw_stats(self, player_score, opponent_score, is_player_turn):
        weather = self.font.render("Weather: [Clear]", True, self.COLORS['white'])
        self.screen.blit(weather, (10, 50))
        
        turn = self.font.render(f"Turn: {'Player' if is_player_turn else 'Opponent'}", 
                                True, self.COLORS['white'])
        self.screen.blit(turn, (self.game_area_width - 200, 50))

    def _draw_battlefields(self, board):
        if not board:
            return
            
        y_offset = 100
        section_height = (self.height - 400) // 2
        
        for side in ['enemy', 'player']:
            title = f"{'Opponent' if side == 'enemy' else 'Your'} Battlefield:"
            text = self.font.render(title, True, self.COLORS['white'])
            self.screen.blit(text, (10, y_offset))
            
            y_offset += 40
            rows = ['SIEGE', 'RANGED', 'CLOSE'] if side == 'enemy' else ['CLOSE', 'RANGED', 'SIEGE']
            rows_data = board.enemy if side == 'enemy' else board.player
            
            row_height = section_height // 3
            
            for row_name in rows:
                value = sum(card.value for card in rows_data[row_name] if hasattr(card, 'value'))
                row_text = self.font.render(f"[{row_name}] Value: {value}", True, self.COLORS['white'])
                self.screen.blit(row_text, (10, y_offset))
                
                self._draw_battlefield_row(row_name, rows_data[row_name], y_offset, row_height, side == 'player')
                
                y_offset += row_height

            y_offset += 20

    def _draw_battlefield_row(self, row_name, cards, y_offset, row_height, is_player):
        # Draw the row boundary
        pygame.draw.rect(self.screen, self.COLORS['gray'],
                         (10, y_offset + 30, self.game_area_width - 20, row_height - 40), 1)
        
        visible_width = self.game_area_width - 40
        card_width = self.config.get('battlefield_card_width', 160)
        spacing = self.config.get('battlefield_spacing', 170)
        cards_per_view = visible_width // spacing
        
        side = 'player' if is_player else 'enemy'
        scroll_pos = self.row_scroll_positions[side][row_name]
        max_scroll = max(0, len(cards) - cards_per_view)
        scroll_pos = min(scroll_pos, max_scroll)
        self.row_scroll_positions[side][row_name] = scroll_pos
        
        visible_cards = cards[scroll_pos:scroll_pos + cards_per_view]
        card_x = 20
        for card in visible_cards:
            # Draw card box background and border
            pygame.draw.rect(self.screen, self.COLORS['black'], 
                             (card_x, y_offset + 40, card_width, row_height - 50))
            pygame.draw.rect(self.screen, self.COLORS['white'], 
                             (card_x, y_offset + 40, card_width, row_height - 50), 1)
            
            # Wrap the text so it fits within the card box
            wrapped_lines = self._wrap_text(f"{card.name} ({card.value})", card_width - 10)
            line_y = y_offset + 45
            for line in wrapped_lines:
                rendered_line = self.font.render(line, True, self.COLORS['white'])
                self.screen.blit(rendered_line, (card_x + 5, line_y))
                line_y += self.config['line_height']
                if line_y > y_offset + row_height - 50:
                    break
            card_x += spacing
        
        if len(cards) > cards_per_view:
            self._draw_scrollbar(self.game_area_width - 15, y_offset + 30,
                                 10, row_height - 40,
                                 len(cards), cards_per_view, scroll_pos)

    def _wrap_text(self, text, max_width):
        """Splits text into multiple lines so each line fits within max_width."""
        words = text.split(' ')
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}" if current_line else word
            if self.font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
        return lines

    def _draw_hand(self, hand):
        if not hand:
            return
            
        y_pos = self.height - self.config['card_height'] - 40
        
        pygame.draw.rect(self.screen, self.COLORS['black'],
                         (0, y_pos - 30, self.game_area_width, self.config['card_height'] + 70))

        title = f"Your Hand ({len(hand)} cards)"
        self.screen.blit(self.font.render(title, True, self.COLORS['white']), (10, y_pos - 30))

        visible_width = self.game_area_width - 40
        cards_per_view = visible_width // self.config['card_spacing']
        max_scroll = max(0, len(hand) - cards_per_view)
        self.card_scroll_pos = min(self.card_scroll_pos, max_scroll)
        visible_cards = hand[self.card_scroll_pos:self.card_scroll_pos + cards_per_view]

        if self.card_scroll_pos > 0:
            left_arrow = self.font.render("←", True, self.COLORS['white'])
            self.screen.blit(left_arrow, (5, y_pos + self.config['card_height'] // 2))
        if self.card_scroll_pos + cards_per_view < len(hand):
            right_arrow = self.font.render("→", True, self.COLORS['white'])
            self.screen.blit(right_arrow, (self.game_area_width - 20, y_pos + self.config['card_height'] // 2))

        for i, card in enumerate(visible_cards):
            x_pos = 10 + i * self.config['card_spacing']
            color = self.COLORS['yellow'] if i + self.card_scroll_pos == self.selected_card else self.COLORS['white']
            
            pygame.draw.rect(self.screen, self.COLORS['gray'], 
                             (x_pos, y_pos, self.config['card_width'], self.config['card_height']))
            pygame.draw.rect(self.screen, color, 
                             (x_pos, y_pos, self.config['card_width'], self.config['card_height']), 2)

            text_x = x_pos + 10
            text_y = y_pos + 10
            line_height = self.config['line_height']

            name = self.font.render(card.name[:15], True, color)
            self.screen.blit(name, (text_x, text_y))

            if hasattr(card, 'value'):
                value = self.font.render(f"Value: {card.value}", True, color)
                self.screen.blit(value, (text_x, text_y + line_height))

            if hasattr(card, 'row') and card.row:
                row_str = '/'.join(r.name[0] for r in card.row)
                row_text = self.font.render(f"Row: {row_str}", True, color)
                self.screen.blit(row_text, (text_x, text_y + line_height * 2))

            if hasattr(card, 'ability') and card.ability:
                ability = self.font.render(str(card.ability.name)[:12], True, color)
                self.screen.blit(ability, (text_x, text_y + line_height * 3))

        if len(hand) > cards_per_view:
            thumb_rect = self._draw_horizontal_scrollbar(10, y_pos + self.config['card_height'] + 5,
                                                          self.game_area_width - 20, 10,
                                                          len(hand), cards_per_view,
                                                          self.card_scroll_pos)
            self.hand_scrollbar_thumb_rect = thumb_rect
            self.hand_scrollbar_track_rect = (10, y_pos + self.config['card_height'] + 5, self.game_area_width - 20, 10)
        else:
            self.hand_scrollbar_thumb_rect = None
            self.hand_scrollbar_track_rect = None

    def _draw_scrollbar(self, x, y, width, height, total_items, visible_items, scroll_pos):
        if total_items <= visible_items:
            return
        pygame.draw.rect(self.screen, self.COLORS['gray'], 
                         (x, y, 10, height), 1)
        thumb_height = max(20, (visible_items / total_items) * height)
        thumb_pos = y + (scroll_pos / total_items) * (height - thumb_height)
        pygame.draw.rect(self.screen, self.COLORS['white'],
                         (x, thumb_pos, 10, thumb_height))

    def _draw_horizontal_scrollbar(self, x, y, width, height, total_items, visible_items, scroll_pos):
        if total_items <= visible_items:
            return None
        pygame.draw.rect(self.screen, self.COLORS['gray'],
                         (x, y + height - 10, width, 10), 1)
        thumb_width = max(40, (visible_items / total_items) * width)
        thumb_x = x + (scroll_pos / (total_items - visible_items)) * (width - thumb_width)
        pygame.draw.rect(self.screen, self.COLORS['white'],
                         (thumb_x, y + height - 10, thumb_width, 10))
        return (thumb_x, y + height - 10, thumb_width, 10)

    def _draw_log(self):
        y_pos = 10
        log_x = self.game_area_width + 10
        title = self.font.render("Game Log", True, self.COLORS['white'])
        self.screen.blit(title, (log_x, y_pos))
        pygame.draw.line(self.screen, self.COLORS['white'],
                         (log_x, y_pos + 25),
                         (self.width - 10, y_pos + 25))
        y_pos += 35
        for entry in self.log[-10:]:
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
                        self._adjust_scroll_to_selected()
                    elif event.key == pygame.K_RIGHT:
                        self.selected_card = min(len(hand) - 1, self.selected_card + 1)
                        self._adjust_scroll_to_selected()
                    elif event.key == pygame.K_p:
                        return "PASS"
            if self.board:
                self.draw_board(self.board, self.last_scores[0], 
                                self.last_scores[1], True, hand)
            pygame.time.wait(50)

    def _adjust_scroll_to_selected(self):
        cards_per_view = (self.game_area_width - 40) // self.config['card_spacing']
        if self.selected_card < self.card_scroll_pos:
            self.card_scroll_pos = self.selected_card
        elif self.selected_card >= self.card_scroll_pos + cards_per_view:
            self.card_scroll_pos = max(0, self.selected_card - cards_per_view + 1)

    def get_user_row_choice(self, card) -> Optional[str]:
        if not hasattr(card, 'row') or not card.row:
            return "CLOSE"
        valid_rows = [r.name for r in card.row]
        if len(valid_rows) == 1:
            return valid_rows[0]
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
        pass

    def handle_events(self, timeout: int = 100):
        clock = pygame.time.Clock()
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise KeyboardInterrupt
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self._handle_mouse_click(event)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    self.scrollbar_dragging = False
                    self.scrollbar_drag_start = None
            elif event.type == pygame.MOUSEMOTION:
                if self.scrollbar_dragging:
                    self._handle_scrollbar_drag(event.pos)
            elif event.type == pygame.KEYDOWN:
                self._handle_keyboard_event(event)
        pygame.time.wait(timeout)

    def _handle_mouse_click(self, event):
        if event.button == 1:
            mx, my = event.pos
            hand_y = self.height - self.config['card_height'] - 40
            if hand_y <= my <= hand_y + self.config['card_height']:
                card_spacing = self.config['card_spacing']
                card_width = self.config['card_width']
                cards_per_view = (self.game_area_width - 40) // card_spacing
                card_idx = (mx - 10) // card_spacing
                x_start = 10 + card_idx * card_spacing
                x_end = x_start + card_width
                if 0 <= card_idx < cards_per_view and x_start <= mx <= x_end:
                    actual_idx = card_idx + self.card_scroll_pos
                    if actual_idx < len(self.player_hand):
                        self.selected_card = actual_idx
            elif self.hand_scrollbar_track_rect:
                track_rect = pygame.Rect(self.hand_scrollbar_track_rect)
                if track_rect.collidepoint(mx, my):
                    self._handle_scrollbar_click(mx)

    def _handle_scroll(self, scroll_up: bool):
        cards_per_view = (self.game_area_width - 40) // self.config['card_spacing']
        if scroll_up:
            self.card_scroll_pos = max(0, self.card_scroll_pos - 1)
        else:
            max_scroll = max(0, len(self.player_hand) - cards_per_view)
            self.card_scroll_pos = min(max_scroll, self.card_scroll_pos + 1)

    def _handle_scrollbar_click(self, mx):
        track_x, track_y, track_width, track_height = self.hand_scrollbar_track_rect
        click_x = mx - track_x
        cards_per_view = (self.game_area_width - 40) // self.config['card_spacing']
        total_items = len(self.player_hand)
        max_scroll = max(0, total_items - cards_per_view)
        if max_scroll == 0:
            return
        proportion = click_x / track_width
        self.card_scroll_pos = int(proportion * max_scroll)
        if self.hand_scrollbar_thumb_rect:
            thumb_rect = pygame.Rect(*self.hand_scrollbar_thumb_rect)
            if thumb_rect.collidepoint(mx, track_y + track_height / 2):
                self.scrollbar_dragging = True
                self.scrollbar_drag_start = mx - thumb_rect.x

    def _handle_scrollbar_drag(self, pos):
        mx, my = pos
        if not self.hand_scrollbar_track_rect or not self.scrollbar_dragging:
            return
        track_x, track_y, track_width, track_height = self.hand_scrollbar_track_rect
        thumb_width = self.hand_scrollbar_thumb_rect[2] if self.hand_scrollbar_thumb_rect else 40
        new_thumb_x = mx - self.scrollbar_drag_start
        new_thumb_x = max(track_x, min(new_thumb_x, track_x + track_width - thumb_width))
        scrollable_width = track_width - thumb_width
        if scrollable_width <= 0:
            return
        proportion = (new_thumb_x - track_x) / scrollable_width
        total_items = len(self.player_hand)
        cards_per_view = (self.game_area_width - 40) // self.config['card_spacing']
        max_scroll = max(0, total_items - cards_per_view)
        self.card_scroll_pos = int(proportion * max_scroll)

    def _handle_keyboard_event(self, event):
        if event.key == pygame.K_LEFT:
            self.selected_card = max(0, self.selected_card - 1)
            self._adjust_scroll_to_selected()
        elif event.key == pygame.K_RIGHT:
            self.selected_card = min(len(self.player_hand) - 1, self.selected_card + 1)
            self._adjust_scroll_to_selected()
