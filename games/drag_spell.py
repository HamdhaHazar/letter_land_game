import pygame
import random
import math
import time
from game_core import (W, H, CREAM_WHITE, DEEP_SKY, GOLD, WHITE, BLACK, PURPLE, HOT_PINK,
                       SUNNY_YELLOW, RED, LIME_GREEN,
                       WARM_BG_TOP, WARM_BG_BOT, WARM_ACCENT, WARM_HEADER, WARM_CARD, WARM_CORAL, WARM_GREEN,
                       load_font, draw_rounded_rect_with_shadow, draw_gradient_rect,
                       draw_sticker_text, draw_vocabulary_picture, draw_vector_star)
from systems.animation_engine import ParticleSystem

# Phonics sounds guide
PHONICS = {
    'A': 'ay', 'B': 'buh', 'C': 'kuh', 'D': 'duh', 'E': 'eh',
    'F': 'fuh', 'G': 'guh', 'H': 'huh', 'I': 'ih', 'J': 'juh',
    'K': 'kuh', 'L': 'luh', 'M': 'muh', 'N': 'nuh', 'O': 'oh',
    'P': 'puh', 'Q': 'kwuh', 'R': 'ruh', 'S': 'suh', 'T': 'tuh',
    'U': 'uh', 'V': 'vuh', 'W': 'wuh', 'X': 'ks', 'Y': 'yuh', 'Z': 'zuh'
}

# Word repeat interval (seconds) — keeps saying the word until child gets it
WORD_REPEAT_INTERVAL = 6.0

class FloatingTile:
    def __init__(self, char, x, y, size=75):
        self.char = char.upper()
        self.x = x
        self.y = y
        self.size = size
        
        self.vx = random.uniform(-1.0, 1.0)
        self.vy = random.uniform(-0.5, 0.5)
        self.bob_offset = random.uniform(0, math.pi * 2)
        
        self.dragging = False
        self.placed = False
        self.scale = 1.0
        
    def update(self, dt, t_ticks):
        if self.placed or self.dragging:
            return
            
        self.x += self.vx
        self.y += self.vy + math.sin(t_ticks * 2 + self.bob_offset) * 0.3
        
        # Check boundary collision bounces
        margin = 35
        if self.x < margin:
            self.x = margin
            self.vx = abs(self.vx)
        if self.x > W - margin - self.size:
            self.x = W - margin - self.size
            self.vx = -abs(self.vx)
        if self.y < H * 0.54:
            self.y = H * 0.54
            self.vy = abs(self.vy)
        if self.y > H - margin - self.size:
            self.y = H - margin - self.size
            self.vy = -abs(self.vy)

    def draw(self, surface, font):
        if self.placed:
            return
            
        s = int(self.size * self.scale)
        rx = int(self.x + (self.size - s) / 2)
        ry = int(self.y + (self.size - s) / 2)
        r = pygame.Rect(rx, ry, s, s)
        
        # Color based on letter — warm amber for vowels, warm green for consonants
        color = WARM_HEADER if self.char in "AEIOU" else WARM_GREEN
        draw_rounded_rect_with_shadow(surface, color, r, radius=15, shadow_offset=(2, 3), border_width=3, border_color=WHITE)
        
        lbl = font.render(self.char, True, CREAM_WHITE)
        surface.blit(lbl, lbl.get_rect(center=r.center))

class LetterSlot:
    def __init__(self, char, cx, cy, idx, size=82):
        self.char = char.upper()
        self.cx = cx
        self.cy = cy
        self.idx = idx
        self.size = size
        self.filled = False
        self.flash_timer = 0.0

    def rect(self):
        return pygame.Rect(self.cx - self.size//2, self.cy - self.size//2, self.size, self.size)

    def draw(self, surface, font, hint_level):
        r = self.rect()
        
        # Flash animation
        bg_col = WARM_GREEN if self.filled else WARM_CARD  # Green if filled, warm cream empty
        if self.flash_timer > 0:
            bg_col = GOLD
            
        draw_rounded_rect_with_shadow(surface, bg_col, r, radius=18, shadow_offset=(2, 2), border_width=4, border_color=WARM_ACCENT)
        
        # Text inside slot
        if self.filled:
            lbl = font.render(self.char, True, (0, 100, 0))
            surface.blit(lbl, lbl.get_rect(center=r.center))
        else:
            # Assist hints
            if hint_level == 2:
                # Show translucent helper letter
                char_surf = font.render(self.char, True, WARM_ACCENT)
                char_surf.set_alpha(100)
                surface.blit(char_surf, char_surf.get_rect(center=r.center))
            elif hint_level == 1:
                # Highlight borders
                pygame.draw.rect(surface, GOLD, r, 5, border_radius=18)
                
            # Question mark placeholder
            else:
                lbl = font.render("?", True, (180, 150, 120))
                surface.blit(lbl, lbl.get_rect(center=r.center))

class DragSpellGame:
    def __init__(self, level_idx, voice_system, audio_manager, progress_tracker, ai_engine):
        self.level_idx = level_idx
        self.voice = voice_system
        self.audio = audio_manager
        self.progress = progress_tracker
        self.ai = ai_engine
        
        # Load words from vocabulary database
        import os, json
        vocab_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vocabulary.json")
        try:
            with open(vocab_path, "r") as f:
                vocab_data = json.load(f)
            self.words_pool = vocab_data.get("animals", [])
        except:
            self.words_pool = [
                {"word": "CAT", "description": "A furry friend that meows!"},
                {"word": "DOG", "description": "A loyal pet that says woof!"},
                {"word": "PIG", "description": "A pink animal that says oink!"}
            ]
            
        random.shuffle(self.words_pool)
        self.words = self.words_pool[:4] # 4 words per level session
        
        # Progress states
        self.current_word_idx = 0
        self.total_words = len(self.words)
        
        # Active Word structures
        self.word = ""
        self.description = ""
        self.tiles = []
        self.slots = []
        
        # Interaction variables
        self.dragging_tile = None
        self.drag_offset = (0, 0)
        self.particles = ParticleSystem()
        
        # Stats tracking for adaptive AI
        self.word_errors = 0
        self.word_start_time = 0
        self.celebration = False
        self.celebration_timer = 0.0
        
        # Word repeat timer — speaks the word every few seconds until child succeeds
        self.repeat_timer = 0.0
        self.bg_time = 0.0

    def get_instruction_text(self):
        return "Look at the picture, drag letters to their matching boxes, and spell the word!"

    def start_game(self):
        self.current_word_idx = 0
        self.load_word(self.words[self.current_word_idx])
        self.ai.reset_round()

    def load_word(self, word_obj):
        self.word = word_obj["word"].upper()
        self.description = word_obj["description"]
        self.celebration = False
        self.celebration_timer = 0.0
        self.word_errors = 0
        self.word_start_time = time.time()
        self.repeat_timer = 0.0
        
        n = len(self.word)
        self.slots = []
        self.tiles = []
        
        # Create Letter Slots centered in top-middle
        slot_spacing = 105
        slot_w = n * slot_spacing
        start_x = W // 2 - slot_w // 2 + slot_spacing // 2
        slot_y = 322
        
        for i in range(n):
            self.slots.append(LetterSlot(self.word[i], start_x + i * slot_spacing, slot_y, i))
            
        # Create Floating tiles
        letters = list(self.word)
        # Add random distractor letter if child is playing well
        if self.ai.success_streak >= 3:
            distractors = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            dist_char = random.choice([c for c in distractors if c not in letters])
            letters.append(dist_char)
            
        random.shuffle(letters)
        
        # Distribute tiles along the lower half of screen
        margin = 80
        col_w = (W - margin * 2) / len(letters)
        for idx, char in enumerate(letters):
            tx = margin + idx * col_w + random.uniform(-10, 10)
            ty = int(H * 0.65) + random.uniform(-40, 40)
            self.tiles.append(FloatingTile(char, tx, ty))
            
        # Speak spelling prompt
        self.voice.speak(self.word)

    def handle_event(self, event):
        mx, my = pygame.mouse.get_pos()
        
        # Check Back to Map button
        back_rect = pygame.Rect(20, 30, 160, 40)
        if event.type == pygame.MOUSEBUTTONDOWN and back_rect.collidepoint(mx, my):
            self.audio.play_sfx("click")
            return "quit"
            
        if self.celebration:
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Find clicked tile in reverse order (topmost first)
            for tile in reversed(self.tiles):
                if not tile.placed:
                    tile_rect = pygame.Rect(tile.x, tile.y, tile.size, tile.size)
                    if tile_rect.collidepoint(mx, my):
                        self.dragging_tile = tile
                        tile.dragging = True
                        tile.scale = 1.15
                        self.drag_offset = (mx - tile.x, my - tile.y)
                        self.audio.play_sfx("click")
                        break
                        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging_tile:
                tile = self.dragging_tile
                tile.dragging = False
                tile.scale = 1.0
                
                # Check slot collision
                dropped_successfully = False
                for slot in self.slots:
                    if not slot.filled and slot.rect().collidepoint(mx, my):
                        # Match verification
                        if slot.char == tile.char:
                            slot.filled = True
                            slot.flash_timer = 0.2
                            tile.placed = True
                            tile.x = slot.cx - tile.size // 2
                            tile.y = slot.cy - tile.size // 2
                            
                            # Phonics guide output removed
                            pass
                            
                            self.particles.spawn_burst(slot.cx, slot.cy, count=12, shape="star", colors=[GOLD, WHITE])
                            self.audio.play_sfx("click")
                            dropped_successfully = True
                            # Reset repeat timer on correct placement
                            self.repeat_timer = 0.0
                            break
                        else:
                            # Log mistake
                            self.word_errors += 1
                            self.ai.record_mistake(self.word)
                            self.audio.play_sfx("fail")
                            # Error speech removed
                            break
                            
                if not dropped_successfully:
                    # Animate floating slide back to screen center
                    tile.x = W // 2 - tile.size // 2 + random.uniform(-100, 100)
                    tile.y = int(H * 0.72) + random.uniform(-40, 40)
                    
                self.dragging_tile = None
                
                # Check win state
                if all(s.filled for s in self.slots):
                    self.trigger_word_win()

    def trigger_word_win(self):
        self.celebration = True
        self.celebration_timer = 0.0
        
        time_spent = time.time() - self.word_start_time
        self.progress.log_word_attempt(self.word, self.word_errors, time_spent)
        
        if self.word_errors == 0:
            self.ai.record_success(self.word)
            
        self.audio.play_sfx("success")
        self.particles.spawn_burst(W // 2, H // 2, count=30, shape="star")
        self.voice.speak(self.word)

    def update(self, dt):
        self.particles.update(dt)
        self.bg_time += dt
        t_ticks = pygame.time.get_ticks() * 0.001
        
        # Update float physics
        for tile in self.tiles:
            tile.update(dt, t_ticks)
            
        # Drag mechanics
        if self.dragging_tile:
            mx, my = pygame.mouse.get_pos()
            self.dragging_tile.x = mx - self.drag_offset[0]
            self.dragging_tile.y = my - self.drag_offset[1]
            
        # Slot updates
        for slot in self.slots:
            if slot.flash_timer > 0:
                slot.flash_timer -= dt
                
        if self.celebration:
            self.celebration_timer += dt
            if self.celebration_timer >= 2.5:
                # Proceed to next word
                self.current_word_idx += 1
                if self.current_word_idx >= self.total_words:
                    pass  # check_completed will handle this
                else:
                    self.load_word(self.words[self.current_word_idx])
        else:
            # WORD REPEAT: Keep saying the word until the child succeeds
            self.repeat_timer += dt
            if self.repeat_timer >= WORD_REPEAT_INTERVAL:
                self.repeat_timer = 0.0
                if not self.voice.is_busy():
                    self.voice.speak(self.word)

    def draw(self, surface):
        # 1. Vibrant Sky Blue gradient matching Reference Image 1 third screen
        draw_gradient_rect(surface, (200, 242, 255), (160, 220, 255), (0, 0, W, H))
        
        # Draw a beautiful glowing rainbow in the background (highly colorful!)
        from game_core import draw_rainbow
        draw_rainbow(surface, W // 2, H // 2 + 120, start_radius=340, width=14)
        
        # Draw a beautiful glowing sun in the top-left
        pygame.draw.circle(surface, (255, 253, 220), (80, 80), 45)
        pygame.draw.circle(surface, (255, 224, 0), (80, 80), 35)
        
        # Draw floating animated clouds
        bg_time = pygame.time.get_ticks() * 0.001
        for i in range(3):
            cx = (i * 350 + int(bg_time * 5)) % (W + 200) - 100
            cy = 70 + i * 20
            pygame.draw.circle(surface, (255, 255, 255, 180), (cx, cy), 25)
            pygame.draw.circle(surface, (255, 255, 255, 180), (cx + 15, cy - 6), 20)
            pygame.draw.circle(surface, (255, 255, 255, 180), (cx - 12, cy), 18)
            
        # 2. Vibrant curved green hill ground at bottom center
        pygame.draw.ellipse(surface, (0, 0, 0, 15), (0, H - 210, W, 220))
        pygame.draw.ellipse(surface, (120, 210, 80), (-50, H - 200, W + 100, 250))
        pygame.draw.ellipse(surface, (139, 220, 95), (-50, H - 200, W + 100, 250), 6)
        
        # Curved cyan river at bottom-left corner with sand border matching map screen
        pygame.draw.circle(surface, (255, 224, 130), (-20, H + 20), 160, 10)
        pygame.draw.circle(surface, (3, 169, 244), (-20, H + 20), 150)
        
        # Draw a couple of cartoon orange trees on the side of the green hill with sway
        for tx, ty in [(70, H - 180), (125, H - 165), (W - 110, H - 175), (W - 60, H - 195)]:
            sway = int(math.sin(self.bg_time * 2.5 + tx) * 5)
            # Tree shadow
            pygame.draw.ellipse(surface, (0, 0, 0, 40), (tx - 12, ty + 10, 24, 6))
            # Tree trunk
            pygame.draw.rect(surface, (139, 69, 19), (tx - 2, ty, 4, 12))
            # Tree top crown (sways!)
            pygame.draw.circle(surface, (255, 127, 80), (tx + sway, ty), 14)
            pygame.draw.circle(surface, (255, 255, 255), (tx + sway, ty), 14, 2)
        
        self.particles.draw(surface)
        
        # Draw header interface
        # 1. Back button (warm coral with hover scaling)
        mx, my = pygame.mouse.get_pos()
        back_rect = pygame.Rect(20, 30, 160, 40)
        if back_rect.collidepoint(mx, my):
            back_rect = back_rect.inflate(8, 4)
            back_color = WARM_ACCENT
        else:
            back_color = WARM_CORAL
            
        draw_rounded_rect_with_shadow(surface, back_color, back_rect, radius=10, shadow_offset=(1, 2), border_width=2, border_color=WHITE)
        draw_sticker_text(surface, "🗺️ LEAVE LEVEL", load_font(18, bold=True), CREAM_WHITE, BLACK, back_rect.center, border_size=2)
        
        # 2. Explorer Name Capsule
        name_rect = pygame.Rect(195, 30, 160, 40)
        tag_rect_n = pygame.Rect(215, 15, 120, 22)
        draw_rounded_rect_with_shadow(surface, WARM_CORAL, tag_rect_n, radius=6, thickness=2)
        draw_sticker_text(surface, "EXPLORER", load_font(12, bold=True), CREAM_WHITE, BLACK, tag_rect_n.center, border_size=1)
        draw_rounded_rect_with_shadow(surface, WHITE, name_rect, radius=12, border_width=3, border_color=WARM_CORAL)
        
        name_font = load_font(15, bold=True)
        name_txt = name_font.render(self.progress.get_nickname(), True, BLACK)
        surface.blit(name_txt, name_txt.get_rect(center=name_rect.center))

        # 3. Horizontal progress capsule (with PROGRESS tag)
        bar_rect = pygame.Rect(W // 2 - 100, 30, 200, 40)
        tag_rect_p = pygame.Rect(W // 2 - 70, 15, 140, 22)
        draw_rounded_rect_with_shadow(surface, WARM_HEADER, tag_rect_p, radius=6, thickness=2)
        draw_sticker_text(surface, "PROGRESS", load_font(12, bold=True), CREAM_WHITE, BLACK, tag_rect_p.center, border_size=1)
        draw_rounded_rect_with_shadow(surface, WHITE, bar_rect, radius=12, border_width=3, border_color=WARM_ACCENT)
        
        comp_ratio = self.current_word_idx / float(self.total_words)
        fill_w = int(180 * comp_ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(W // 2 - 90, 35, fill_w, 30)
            draw_gradient_rect(surface, (255, 183, 77), (255, 112, 67), fill_rect, radius=8)
            
        pct_font = load_font(13, bold=True)
        pct_text = pct_font.render(f"WORD {self.current_word_idx + 1} OF {self.total_words}", True, BLACK)
        surface.blit(pct_text, pct_text.get_rect(center=bar_rect.center))
        
        # 4. Top-Right: Stats Capsule showing current stars count (with STARS tag)
        stats_rect = pygame.Rect(W - 250, 30, 170, 40)
        tag_rect_s = pygame.Rect(W - 220, 15, 110, 22)
        draw_rounded_rect_with_shadow(surface, GOLD, tag_rect_s, radius=6, thickness=2)
        draw_sticker_text(surface, "STARS", load_font(12, bold=True), CREAM_WHITE, BLACK, tag_rect_s.center, border_size=1)
        draw_rounded_rect_with_shadow(surface, WHITE, stats_rect, radius=12, border_width=3, border_color=GOLD)
        
        # Draw a beautiful vector star next to the score text
        draw_vector_star(surface, (W - 238 + 12, stats_rect.centery), size=11, color=GOLD, border_color=WHITE)
        
        score_font = load_font(16, bold=True)
        score_surf = score_font.render(f"STARS: {self.progress.data['stars']}", True, BLACK)
        surface.blit(score_surf, score_surf.get_rect(midleft=(W - 205, stats_rect.centery)))
        
        # Draw wooden chalkboard card for target instructions (prevents overlapping background)
        board_rect = pygame.Rect(W // 2 - 200, 85, 400, 55)
        draw_rounded_rect_with_shadow(surface, (139, 69, 19), board_rect, radius=12, border_width=3, border_color=WHITE)
        inner_rect = board_rect.inflate(-8, -8)
        pygame.draw.rect(surface, (30, 45, 35), inner_rect, border_radius=8)
        
        word_font = load_font(24, bold=True)
        draw_sticker_text(surface, f"Spell: {self.word}", word_font, CREAM_WHITE, BLACK, board_rect.center, border_size=1)
        
        # Draw word picture placeholder (shifted down slightly)
        draw_vocabulary_picture(surface, self.word, W // 2, 210, radius=55)
        
        # Divider path line
        pygame.draw.line(surface, GOLD, (60, int(H * 0.52)), (W - 60, int(H * 0.52)), 4)
        
        # Determine hint level from AI Engine
        h_lvl = self.ai.get_hint_level(self.word)
        
        # Draw slots
        slot_font = load_font(42, bold=True)
        for slot in self.slots:
            # Highlight target slots of the next required letter if struggling
            next_empty_idx = -1
            for s in self.slots:
                if not s.filled:
                    next_empty_idx = s.idx
                    break
            
            is_target = (slot.idx == next_empty_idx)
            slot.draw(surface, slot_font, h_lvl if is_target else 0)
            
        # Draw tiles
        tile_font = load_font(36, bold=True)
        for tile in self.tiles:
            tile.draw(surface, tile_font)
            
        # Success overlay announcement
        if self.celebration:
            banner = pygame.Rect(W // 2 - 250, H // 2 - 50, 500, 100)
            draw_rounded_rect_with_shadow(surface, GOLD, banner, radius=22, shadow_offset=(3, 5), border_width=4, border_color=(139, 69, 19))
            font = load_font(45, bold=True)
            text_str = f"{self.word}!"
            text_w = font.size(text_str)[0]
            draw_sticker_text(surface, text_str, font, (139, 69, 19), WHITE, banner.center, border_size=2)
            draw_vector_star(surface, (banner.centerx - text_w // 2 - 35, banner.centery), size=18, color=(255, 235, 59), border_color=(139, 69, 19))
            draw_vector_star(surface, (banner.centerx + text_w // 2 + 35, banner.centery), size=18, color=(255, 235, 59), border_color=(139, 69, 19))

    @property
    def active_game_completed(self):
        return self.current_word_idx >= self.total_words

    @active_game_completed.setter
    def active_game_completed(self, val):
        pass

    def check_completed(self):
        if self.current_word_idx >= self.total_words:
            return "completed"
        return None
