import pygame
import random
import math
import time
from game_core import (W, H, CREAM_WHITE, DEEP_SKY, GOLD, WHITE, BLACK, PURPLE, HOT_PINK,
                       SUNNY_YELLOW, RED, LIME_GREEN, ORANGE,
                       WARM_BG_TOP, WARM_BG_BOT, WARM_ACCENT, WARM_HEADER, WARM_CARD,
                       WARM_CORAL, WARM_GREEN,
                       load_font, draw_rounded_rect_with_shadow, draw_gradient_rect,
                       draw_sticker_text, draw_vocabulary_picture)
from systems.animation_engine import ParticleSystem

# Word repeat interval (seconds)
WORD_REPEAT_INTERVAL = 6.0

class OptionButton:
    def __init__(self, text, rect, color=WARM_ACCENT):
        self.text = text.upper()
        self.rect = pygame.Rect(rect)
        self.color = color
        self.hovered = False
        self.scale = 1.0
        self.visible = True

    def draw(self, surface, font):
        if not self.visible:
            return
            
        # Hover scaling effect
        w = int(self.rect.w * self.scale)
        h = int(self.rect.h * self.scale)
        rx = self.rect.centerx - w // 2
        ry = self.rect.centery - h // 2
        draw_rect = pygame.Rect(rx, ry, w, h)
        
        # Draw golden glow outline if hovered/scaled
        if self.scale > 1.01:
            pygame.draw.rect(surface, GOLD, draw_rect.inflate(10, 10), border_radius=20)
            
        draw_rounded_rect_with_shadow(surface, self.color, draw_rect, radius=16, shadow_offset=(2, 3), border_width=3, border_color=WHITE)
        
        lbl = font.render(self.text, True, CREAM_WHITE)
        surface.blit(lbl, lbl.get_rect(center=draw_rect.center))

class PictureChoiceGame:
    def __init__(self, level_idx, voice_system, audio_manager, progress_tracker, ai_engine):
        self.level_idx = level_idx
        self.voice = voice_system
        self.audio = audio_manager
        self.progress = progress_tracker
        self.ai = ai_engine
        
        # Load food data
        import os, json
        vocab_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vocabulary.json")
        try:
            with open(vocab_path, "r") as f:
                vocab_data = json.load(f)
            self.words_pool = vocab_data.get("food", [])
        except:
            self.words_pool = [
                {"word": "APPLE", "description": "A crunchy red fruit!"},
                {"word": "BANANA", "description": "A yellow fruit!"},
                {"word": "CAKE", "description": "A sweet birthday treat!"},
                {"word": "MILK", "description": "A healthy white drink!"}
            ]
            
        random.shuffle(self.words_pool)
        self.words = self.words_pool[:4]
        
        # Game loop states
        self.current_word_idx = 0
        self.total_words = len(self.words)
        
        self.word = ""
        self.description = ""
        self.options = []
        self.buttons = []
        
        self.particles = ParticleSystem()
        self.word_errors = 0
        self.word_start_time = 0
        self.celebration = False
        self.celebration_timer = 0.0
        
        # Word repeat timer
        self.repeat_timer = 0.0
        self.bg_time = 0.0

    def get_instruction_text(self):
        return "Look at the picture, listen to me ask: What is this?, and click the correct matching word!"

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
        
        # Determine number of options from adaptive AI (2, 3 or 4)
        option_count = self.ai.get_option_count("food")
        
        # Pick incorrect options
        all_distractors = [w["word"].upper() for w in self.words_pool if w["word"].upper() != self.word]
        random.shuffle(all_distractors)
        
        distractor_count = option_count - 1
        picked_distractors = all_distractors[:distractor_count]
        
        choices = picked_distractors + [self.word]
        random.shuffle(choices)
        self.options = choices
        
        # Create buttons with warm theme colors
        self.buttons = []
        btn_w = 230
        btn_h = 56
        btn_spacing = 30
        
        # Compute start coordinates to center buttons
        total_w = len(choices) * btn_w + (len(choices) - 1) * btn_spacing
        start_x = W // 2 - total_w // 2
        btn_y = 420
        
        colors = [WARM_ACCENT, WARM_HEADER, WARM_CORAL, WARM_GREEN]
        
        for idx, choice in enumerate(choices):
            bx = start_x + idx * (btn_w + btn_spacing)
            col = colors[idx % len(colors)]
            self.buttons.append(OptionButton(choice, (bx, btn_y, btn_w, btn_h), col))
            
        # Speak prompt question
        self.voice.speak("What is this?")
        self.voice.speak(self.description)

    def handle_event(self, event):
        mx, my = pygame.mouse.get_pos()
        
        # Leave level button
        back_rect = pygame.Rect(20, 30, 160, 40)
        if event.type == pygame.MOUSEBUTTONDOWN and back_rect.collidepoint(mx, my):
            self.audio.play_sfx("click")
            return "quit"
            
        if self.celebration:
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for btn in self.buttons:
                if btn.visible and btn.rect.collidepoint(mx, my):
                    if btn.text == self.word:
                        # Correct!
                        self.trigger_word_win()
                    else:
                        # Incorrect!
                        self.word_errors += 1
                        self.ai.record_mistake(self.word)
                        self.audio.play_sfx("fail")
                        self.voice.speak("Oops! That's not it, try another one!")
                        
                        # Adaptive assistance: hide this incorrect button if struggling
                        btn.visible = False
                        
                        # Trigger adaptive drop to 2 options immediately if not already
                        if len([b for b in self.buttons if b.visible]) > 2:
                            for b in self.buttons:
                                if b.visible and b.text != self.word:
                                    b.visible = False
                                    break
                    break

    def trigger_word_win(self):
        self.celebration = True
        self.celebration_timer = 0.0
        
        time_spent = time.time() - self.word_start_time
        self.progress.log_word_attempt(self.word, self.word_errors, time_spent)
        
        if self.word_errors == 0:
            self.ai.record_success(self.word)
            
        self.audio.play_sfx("success")
        self.particles.spawn_burst(W // 2, H // 2, count=30, shape="confetti")
        self.voice.speak(f"Great job! That is {self.word}!")

    def update(self, dt):
        self.particles.update(dt)
        mx, my = pygame.mouse.get_pos()
        self.bg_time += dt
        
        for btn in self.buttons:
            if btn.visible:
                if btn.rect.collidepoint(mx, my):
                    btn.scale = min(1.08, btn.scale + dt * 1.5)
                else:
                    btn.scale = max(1.0, btn.scale - dt * 1.5)
                    
        if self.celebration:
            self.celebration_timer += dt
            if self.celebration_timer >= 2.5:
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
                    self.voice.speak(f"What is this? Can you find {self.word}?")

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
        
        star_font = load_font(20)
        star_surf = star_font.render("⭐", True, GOLD)
        surface.blit(star_surf, star_surf.get_rect(midleft=(W - 238, stats_rect.centery)))
        
        score_font = load_font(16, bold=True)
        score_surf = score_font.render(f"STARS: {self.progress.data['stars']}", True, BLACK)
        surface.blit(score_surf, score_surf.get_rect(midleft=(W - 205, stats_rect.centery)))
        
        # Draw wooden chalkboard card for target instructions (prevents overlapping background)
        board_rect = pygame.Rect(W // 2 - 200, 85, 400, 60)
        draw_rounded_rect_with_shadow(surface, (139, 69, 19), board_rect, radius=12, border_width=3, border_color=WHITE)
        inner_rect = board_rect.inflate(-8, -8)
        pygame.draw.rect(surface, (30, 45, 35), inner_rect, border_radius=8)
        
        q_font = load_font(24, bold=True)
        draw_sticker_text(surface, "What is this? 🤔", q_font, CREAM_WHITE, BLACK, board_rect.center, border_size=1)
        
        # Draw central food vector placard (shifted and resized to fit perfectly)
        draw_vocabulary_picture(surface, self.word, W // 2, 255, radius=70)
        
        # Draw buttons
        btn_font = load_font(24, bold=True)
        for btn in self.buttons:
            btn.draw(surface, btn_font)
            
        # Success overlay
        if self.celebration:
            banner = pygame.Rect(W // 2 - 250, H // 2 - 50, 500, 100)
            draw_rounded_rect_with_shadow(surface, GOLD, banner, radius=22, shadow_offset=(3, 5), border_width=4, border_color=(139, 69, 19))
            draw_sticker_text(surface, f"⭐ {self.word}! ⭐", load_font(45, bold=True), (139, 69, 19), WHITE, banner.center, border_size=2)

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
