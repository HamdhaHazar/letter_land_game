import pygame
import random
import math
import time
from game_core import (W, H, CREAM_WHITE, DEEP_SKY, GOLD, WHITE, BLACK, PURPLE, HOT_PINK,
                       SUNNY_YELLOW, RED, LIME_GREEN, SOFT_YELLOW,
                       WARM_BG_TOP, WARM_BG_BOT, WARM_ACCENT, WARM_HEADER, WARM_CARD,
                       WARM_CORAL, WARM_GREEN,
                       load_font, draw_rounded_rect_with_shadow, draw_gradient_rect,
                       draw_sticker_text, draw_vocabulary_picture, draw_glow_circle, draw_vector_star)
from systems.animation_engine import ParticleSystem

# Word repeat interval (seconds)
WORD_REPEAT_INTERVAL = 6.0

class MatchingCard:
    def __init__(self, item_id, text, x, y, card_type, w=150, h=105):
        self.item_id = item_id # Unique ID linking picture and word
        self.text = text.upper()
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.card_type = card_type # "pic" or "word"
        
        self.selected = False
        self.matched = False
        self.scale = 1.0
        
        # 3D Flip animation variables
        self.flip_t = 1.0
        self.is_flipping = False
        self.width_scale = 1.0

    def start_flip(self):
        self.is_flipping = True
        self.flip_t = 0.0
        self.width_scale = 1.0

    def update_flip(self, dt):
        if self.is_flipping:
            self.flip_t += dt * 4.0
            if self.flip_t >= 1.0:
                self.flip_t = 1.0
                self.is_flipping = False
            # Simulate 3D rotation by scaling width using cosine wave
            self.width_scale = abs(math.cos(self.flip_t * math.pi))

    def rect(self):
        w = int(self.w * self.scale * self.width_scale)
        h = int(self.h * self.scale)
        rx = self.x - w // 2
        ry = self.y - h // 2
        return pygame.Rect(rx, ry, w, h)

    def draw(self, surface, font):
        r = self.rect()
        if r.w <= 0:
            return
            
        # Determine background color — warm theme
        if self.matched:
            bg_col = WARM_GREEN
            border_col = GOLD
        elif self.selected:
            bg_col = WARM_BG_TOP
            border_col = WARM_HEADER
        else:
            bg_col = WARM_CARD
            border_col = WARM_ACCENT
            
        # Draw golden glow outline if hovered/scaled and not matched
        if self.scale > 1.01 and not self.matched:
            pygame.draw.rect(surface, GOLD, r.inflate(10, 10), border_radius=18)
            
        draw_rounded_rect_with_shadow(surface, bg_col, r, radius=15, shadow_offset=(2, 3), border_width=4, border_color=border_col)
        
        if self.card_type == "pic":
            # Render picture onto temporary surface to scale horizontally (3D rotate look)
            temp_surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            draw_vocabulary_picture(temp_surf, self.text, self.w // 2, self.h // 2, radius=42)
            
            scaled_w = max(1, int(self.w * self.scale * self.width_scale))
            scaled_h = max(1, int(self.h * self.scale))
            scaled_surf = pygame.transform.smoothscale(temp_surf, (scaled_w, scaled_h))
            surface.blit(scaled_surf, (self.x - scaled_w // 2, self.y - scaled_h // 2))
        else:
            # Word Card
            lbl = font.render(self.text, True, BLACK if not self.matched else WHITE)
            if self.width_scale < 0.99:
                text_w = max(1, int(lbl.get_width() * self.width_scale))
                text_h = lbl.get_height()
                lbl = pygame.transform.smoothscale(lbl, (text_w, text_h))
            surface.blit(lbl, lbl.get_rect(center=r.center))

class MatchingGame:
    def __init__(self, level_idx, voice_system, audio_manager, progress_tracker, ai_engine):
        self.level_idx = level_idx
        self.voice = voice_system
        self.audio = audio_manager
        self.progress = progress_tracker
        self.ai = ai_engine
        
        # Load category based on level
        self.category = "objects" if self.level_idx == 2 else "actions"
        
        import os, json
        vocab_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vocabulary.json")
        try:
            with open(vocab_path, "r") as f:
                vocab_data = json.load(f)
            self.words_pool = vocab_data.get(self.category, [])
        except:
            if self.category == "objects":
                self.words_pool = [
                    {"word": "CAR", "description": "A vehicle to drive!"},
                    {"word": "BUS", "description": "Takes you to school!"},
                    {"word": "CUP", "description": "Drink milk from this!"}
                ]
            else:
                self.words_pool = [
                    {"word": "RUN", "description": "Move fast on feet!"},
                    {"word": "JUMP", "description": "Bounce off floor!"},
                    {"word": "FLY", "description": "Soar like a bird!"}
                ]
                
        # Game stats
        self.particles = ParticleSystem()
        self.celebration = False
        self.celebration_timer = 0.0
        self.word_errors = 0
        self.start_time = 0
        
        self.cards = []
        self.connections = [] # Stores coordinate pairs representing correct matches
        self.selected_pic_card = None
        self.selected_word_card = None
        
        # Adaptive helper
        self.hint_target_word = None
        
        # Word repeat timer
        self.repeat_timer = 0.0
        self.current_target_word = None

        # Background decorations
        self.bg_time = 0.0
        self.bg_petals = []
        for _ in range(12):
            self.bg_petals.append({
                "x": random.randint(0, W),
                "y": random.randint(0, H),
                "vx": random.uniform(-1.5, -0.4),
                "vy": random.uniform(0.4, 1.2),
                "size": random.randint(6, 12),
                "color": random.choice([(255, 182, 193, 140), (255, 192, 203, 150), (144, 238, 144, 130)]), # Pink petals & green leaves
                "angle": random.uniform(0, 360),
                "rot_speed": random.uniform(-2.0, 2.0)
            })
            
        self.bg_butterflies = []
        butterfly_colors = [(255, 105, 180), (255, 165, 0), (135, 206, 250), (255, 255, 100)]
        for _ in range(3):
            self.bg_butterflies.append({
                "x": random.randint(-100, W),
                "y": random.randint(100, H - 250),
                "base_y": random.randint(100, H - 250),
                "phase": random.uniform(0, math.pi * 2),
                "speed": random.uniform(1.2, 2.5),
                "scale": random.uniform(0.8, 1.2),
                "color": random.choice(butterfly_colors)
            })

    def get_instruction_text(self):
        return "Tap a card on the left, then find and tap its matching card on the right!"

    def start_game(self):
        self.celebration = False
        self.celebration_timer = 0.0
        self.word_errors = 0
        self.start_time = time.time()
        self.connections = []
        self.selected_pic_card = None
        self.selected_word_card = None
        self.ai.reset_round()
        self.repeat_timer = 0.0
        
        # Setup 3 items for matching grid
        random.shuffle(self.words_pool)
        round_words = self.words_pool[:3]
        
        self.cards = []
        
        # Picture cards on the left, Word cards on the right (shuffled)
        pic_items = list(round_words)
        word_items = list(round_words)
        random.shuffle(word_items)
        
        card_w, card_h = 175, 115
        
        # Compute Y coordinates to stack 3 cards
        start_y = H // 2 - 130
        spacing_y = 150
        
        for idx in range(3):
            # Left Picture Card
            pic_obj = pic_items[idx]
            self.cards.append(MatchingCard(
                item_id=pic_obj["word"],
                text=pic_obj["word"],
                x=W // 4 + 30,
                y=start_y + idx * spacing_y,
                card_type="pic",
                w=card_w,
                h=card_h
            ))
            
            # Right Word Card
            word_obj = word_items[idx]
            self.cards.append(MatchingCard(
                item_id=word_obj["word"],
                text=word_obj["word"],
                x=3 * W // 4 - 30,
                y=start_y + idx * spacing_y,
                card_type="word",
                w=card_w,
                h=card_h
            ))
            
        self.current_target_word = pic_items[0]["word"].upper()
        self.voice.speak(self.current_target_word)

    def handle_event(self, event):
        mx, my = pygame.mouse.get_pos()
        
        # Back button check
        back_rect = pygame.Rect(20, 30, 160, 40)
        if event.type == pygame.MOUSEBUTTONDOWN and back_rect.collidepoint(mx, my):
            self.audio.play_sfx("click")
            return "quit"
            
        if self.celebration:
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_card = None
            for card in self.cards:
                if not card.matched and card.rect().collidepoint(mx, my):
                    clicked_card = card
                    break
                    
            if clicked_card:
                self.audio.play_sfx("click")
                clicked_card.start_flip() # Start 3D Flip
                
                # Visual highlight toggle
                if clicked_card.card_type == "pic":
                    if self.selected_pic_card:
                        self.selected_pic_card.selected = False
                    self.selected_pic_card = clicked_card
                    clicked_card.selected = True
                    
                    self.voice.speak(clicked_card.text)
                else:
                    if self.selected_word_card:
                        self.selected_word_card.selected = False
                    self.selected_word_card = clicked_card
                    clicked_card.selected = True
                    
                # Verify match once both left and right are selected
                if self.selected_pic_card and self.selected_word_card:
                    self.check_match()

    def check_match(self):
        p_card = self.selected_pic_card
        w_card = self.selected_word_card
        if not p_card or not w_card:
            return
            
        if p_card.item_id == w_card.item_id:
            # Match Success!
            p_card.matched = True
            w_card.matched = True
            p_card.selected = False
            w_card.selected = False
            
            # Connect them visually
            self.connections.append((p_card.x + p_card.w//2, p_card.y, w_card.x - w_card.w//2, w_card.y))
            
            # Clear helpers
            self.hint_target_word = None
            
            # Celebrations
            self.audio.play_sfx("success")
            self.particles.spawn_burst(p_card.x, p_card.y, count=10, shape="star", colors=[GOLD, WHITE])
            self.particles.spawn_burst(w_card.x, w_card.y, count=10, shape="star", colors=[GOLD, WHITE])
            
            # Speak correct match word and prompt next
            matched_text = p_card.text
            self.voice.speak(matched_text)
            
            self.selected_pic_card = None
            self.selected_word_card = None
            
            # Verify if all matched
            if all(c.matched for c in self.cards):
                self.current_target_word = None
                self.trigger_round_win()
            else:
                remaining = [c.text for c in self.cards if not c.matched and c.card_type == "pic"]
                if remaining:
                    self.current_target_word = remaining[0]
                    self.voice.speak(self.current_target_word)
        else:
            # Mismatch!
            p_card.selected = False
            w_card.selected = False
            
            self.word_errors += 1
            self.ai.record_mistake(p_card.text)
            self.audio.play_sfx("fail")
            # Error speech removed
            
            # Adaptive AI: If errors accrue, show glowing outline matching helper
            if self.ai.get_hint_level(p_card.text) >= 1:
                self.hint_target_word = p_card.text
                
            self.selected_pic_card = None
            self.selected_word_card = None

    def trigger_round_win(self):
        self.celebration = True
        self.celebration_timer = 0.0
        
        # Log attempt for each word
        time_spent = (time.time() - self.start_time) / 3.0
        for card in self.cards:
            if card.card_type == "pic":
                self.progress.log_word_attempt(card.text, self.word_errors, time_spent)
                
        if self.word_errors == 0:
            self.ai.record_success("MATCHING")
            
        self.audio.play_sfx("success")
        self.particles.spawn_burst(W // 2, H // 2, count=30, shape="confetti")
        self.voice.speak("Fantastic! You matched all the words correctly!")

    def update(self, dt):
        self.particles.update(dt)
        mx, my = pygame.mouse.get_pos()
        self.bg_time += dt
        
        # Update bg animations
        for p in self.bg_petals:
            p['x'] += p['vx'] * dt * 40.0
            p['y'] += p['vy'] * dt * 40.0
            p['angle'] += p['rot_speed'] * dt * 3.0
            if p['x'] < -20:
                p['x'] = W + 20
                p['y'] = random.randint(100, H - 200)
            if p['y'] > H + 20:
                p['y'] = -20
                p['x'] = random.randint(0, W)
                
        for b in self.bg_butterflies:
            b['x'] += b['speed'] * dt * 45.0
            b['phase'] += dt * 5.0
            b['y'] = b['base_y'] + math.sin(b['phase']) * 40.0
            if b['x'] > W + 30:
                b['x'] = -30
                b['base_y'] = random.randint(150, H - 250)
        
        for card in self.cards:
            card.update_flip(dt)
            if not card.matched:
                if card.rect().collidepoint(mx, my):
                    card.scale = min(1.08, card.scale + dt * 1.5)
                else:
                    card.scale = max(1.0, card.scale - dt * 1.5)
                    
        if self.celebration:
            self.celebration_timer += dt
        else:
            # WORD REPEAT: Keep prompting the child
            self.repeat_timer += dt
            if self.repeat_timer >= WORD_REPEAT_INTERVAL:
                self.repeat_timer = 0.0
                if not self.voice.is_busy():
                    if self.current_target_word:
                        self.voice.speak(self.current_target_word)

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
            
        # Draw floating cherry blossom petals & leaves
        for p in self.bg_petals:
            petal_surf = pygame.Surface((p['size']*2, p['size']*2), pygame.SRCALPHA)
            pygame.draw.ellipse(petal_surf, p['color'], (p['size']//2, p['size']//2, p['size'], p['size']//2))
            rotated = pygame.transform.rotate(petal_surf, p['angle'])
            surface.blit(rotated, (int(p['x'] - rotated.get_width()//2), int(p['y'] - rotated.get_height()//2)))
            
        # Draw animated flapping butterflies
        for b in self.bg_butterflies:
            flap = abs(math.sin(b['phase'] * 2.0))
            w_w = int(12 * b['scale'] * flap)
            w_h = int(14 * b['scale'])
            pygame.draw.ellipse(surface, b['color'], (b['x'] - w_w - 2, b['y'] - w_h//2, w_w, w_h))
            pygame.draw.ellipse(surface, b['color'], (b['x'] + 2, b['y'] - w_h//2, w_w, w_h))
            pygame.draw.ellipse(surface, BLACK, (b['x'] - 2, b['y'] - w_h//2 - 2, 4, w_h + 4))

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
        
        matched_count = len([c for c in self.cards if c.matched]) // 2
        comp_ratio = matched_count / 3.0
        fill_w = int(180 * comp_ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(W // 2 - 90, 35, fill_w, 30)
            draw_gradient_rect(surface, (255, 183, 77), (255, 112, 67), fill_rect, radius=8)
            
        pct_font = load_font(13, bold=True)
        pct_text = pct_font.render(f"MATCHED: {matched_count} OF 3", True, BLACK)
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
        
        # Draw permanent connection lines between matched cards (golden)
        for x1, y1, x2, y2 in self.connections:
            pygame.draw.line(surface, GOLD, (x1, y1), (x2, y2), 10)
            pygame.draw.line(surface, CREAM_WHITE, (x1, y1), (x2, y2), 4)
            pygame.draw.circle(surface, GOLD, (x1, y1), 8)
            pygame.draw.circle(surface, GOLD, (x2, y2), 8)
            
        # Draw cards
        card_font = load_font(25, bold=True)
        for card in self.cards:
            # Glow assistance target if adaptive AI is triggered
            if self.hint_target_word and card.item_id == self.hint_target_word and not card.matched:
                draw_glow_circle(surface, GOLD, (card.x, card.y), 65, glow_width=15)
            # Add dynamic orbiting sparkle particles around the CURRENT target word card (high quality visual!)
            if self.current_target_word and card.item_id == self.current_target_word and not card.matched:
                sparkle_angle = self.bg_time * 6.0
                sx = int(card.x + math.cos(sparkle_angle) * 75)
                sy = int(card.y + math.sin(sparkle_angle) * 55)
                pygame.draw.circle(surface, GOLD, (sx, sy), 5)
                pygame.draw.circle(surface, WHITE, (sx, sy), 2)
            card.draw(surface, card_font)
            
        # Draw wooden chalkboard card for target instructions (prevents overlapping background)
        board_rect = pygame.Rect(W // 2 - 275, 90, 550, 60)
        draw_rounded_rect_with_shadow(surface, (139, 69, 19), board_rect, radius=12, border_width=3, border_color=WHITE)
        inner_rect = board_rect.inflate(-8, -8)
        pygame.draw.rect(surface, (30, 45, 35), inner_rect, border_radius=8)
        
        inst_font = load_font(18, bold=True)
        if self.current_target_word:
            text_str = f"Can you find and match the picture for {self.current_target_word}?"
        else:
            text_str = "Match the picture card with the word card!"
        draw_sticker_text(surface, text_str, inst_font, CREAM_WHITE, BLACK, board_rect.center, border_size=1)
        
        # Winner banner
        if self.celebration:
            banner = pygame.Rect(W // 2 - 250, H // 2 - 50, 500, 100)
            draw_rounded_rect_with_shadow(surface, GOLD, banner, radius=22, shadow_offset=(3, 5), border_width=4, border_color=(139, 69, 19))
            font = load_font(40, bold=True)
            text_str = "MATCH COMPLETE!"
            text_w = font.size(text_str)[0]
            draw_sticker_text(surface, text_str, font, (139, 69, 19), WHITE, banner.center, border_size=2)
            draw_vector_star(surface, (banner.centerx - text_w // 2 - 35, banner.centery), size=18, color=(255, 235, 59), border_color=(139, 69, 19))
            draw_vector_star(surface, (banner.centerx + text_w // 2 + 35, banner.centery), size=18, color=(255, 235, 59), border_color=(139, 69, 19))

    @property
    def active_game_completed(self):
        # Set trigger once round exits
        return self.celebration and self.celebration_timer >= 2.5

    @active_game_completed.setter
    def active_game_completed(self, val):
        pass

    def check_completed(self):
        if self.active_game_completed:
            return "completed"
        return None
