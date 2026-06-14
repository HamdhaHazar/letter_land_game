import pygame
import random
import math
import time
from game_core import (W, H, CREAM_WHITE, DEEP_SKY, GOLD, WHITE, BLACK, PURPLE, HOT_PINK,
                       SUNNY_YELLOW, RED, LIME_GREEN,
                       WARM_BG_TOP, WARM_BG_BOT, WARM_ACCENT, WARM_HEADER, WARM_CARD,
                       WARM_CORAL, WARM_GREEN,
                       load_font, draw_rounded_rect_with_shadow, draw_gradient_rect,
                       draw_sticker_text, draw_glow_circle)
from systems.animation_engine import ParticleSystem

# Word repeat interval (seconds)
WORD_REPEAT_INTERVAL = 5.0

# Balloon color palettes mapping
BALLOON_COLORS = {
    "RED": (255, 60, 60),
    "BLUE": (60, 140, 255),
    "GREEN": (60, 220, 60),
    "YELLOW": (255, 220, 40),
    "PINK": (255, 105, 180)
}

class FloatingBalloon:
    def __init__(self, color_name, x, y, size=65):
        self.color_name = color_name.upper()
        self.x = x
        self.y = y
        self.size = size
        
        self.color = BALLOON_COLORS.get(self.color_name, RED)
        self.vy = random.uniform(-0.6, -1.2)
        self.bob_x = random.uniform(0, math.pi * 2)
        self.scale = 1.0
        self.visible = True
        
        # Shake animation values
        self.shake_t = 0.0

    def update(self, dt):
        if not self.visible:
            return
            
        # Float upwards, wrap around bottom if they fly off-screen
        self.y += self.vy
        if self.y < -self.size * 2:
            self.y = H + 50
            self.x = random.randint(100, W - 100)
            
        self.bob_x += dt * 2.0
        
        if self.shake_t > 0:
            self.shake_t -= dt * 5.0

    def rect(self):
        # Balloon hit box
        s = int(self.size * self.scale)
        rx = self.x - s // 2
        ry = self.y - int(s * 1.25) // 2
        return pygame.Rect(rx, ry, s, int(s * 1.25))

    def draw(self, surface):
        if not self.visible:
            return
            
        s = int(self.size * self.scale)
        shake_offset = math.sin(self.shake_t * 6) * 12 if self.shake_t > 0 else 0
        bx = int(self.x + shake_offset)
        by = int(self.y + math.sin(self.bob_x) * 10)
        
        # 1. Draw hanging string
        pygame.draw.arc(surface, (120, 120, 120), (bx - 10, by + s//2 - 5, 20, 45), 0, math.pi, 2)
        
        # 2. Draw small triangular balloon knot at bottom
        pygame.draw.polygon(surface, self.color, [(bx, by + s//2 - 6), (bx - 8, by + s//2 + 4), (bx + 8, by + s//2 + 4)])
        
        # 3. Draw main balloon body (Ellipse sticker look)
        ball_rect = pygame.Rect(bx - s//2, by - s//2 - 6, s, int(s * 1.15))
        
        # Draw golden glow if hovered/scaled
        if self.scale > 1.01:
            pygame.draw.ellipse(surface, GOLD, ball_rect.inflate(14, 14))
            
        # Shadow
        shadow_r = pygame.Rect(ball_rect.x + 3, ball_rect.y + 4, ball_rect.w, ball_rect.h)
        pygame.draw.ellipse(surface, (0, 0, 0, 50), shadow_r)
        
        pygame.draw.ellipse(surface, self.color, ball_rect)
        pygame.draw.ellipse(surface, WHITE, ball_rect, 3)
        
        # Balloon glare reflection glint
        glare_rect = pygame.Rect(bx - s//3, by - s//3 - 4, s//4, s//3)
        pygame.draw.ellipse(surface, (255, 255, 255, 160), glare_rect)

class ListeningGame:
    def __init__(self, level_idx, voice_system, audio_manager, progress_tracker, ai_engine):
        self.level_idx = level_idx
        self.voice = voice_system
        self.audio = audio_manager
        self.progress = progress_tracker
        self.ai = ai_engine
        
        self.colors_pool = ["RED", "BLUE", "GREEN", "YELLOW", "PINK"]
        # Ensure "RED" is always at the front of colors list
        distractors = [c for c in self.colors_pool if c != "RED"]
        random.shuffle(distractors)
        self.round_colors = ["RED"] + distractors[:3]
        
        self.current_idx = 0
        self.total_colors = len(self.round_colors)
        
        self.target_color = ""
        self.balloons = []
        self.particles = ParticleSystem()
        
        self.word_errors = 0
        self.start_time = 0
        
        self.celebration = False
        self.celebration_timer = 0.0
        
        # Word repeat timer
        self.repeat_timer = 0.0
        self.bg_time = 0.0

    def get_instruction_text(self):
        return "Listen to the color I say, and tap the correct floating balloon!"

    def start_game(self):
        self.current_idx = 0
        self.load_color(self.round_colors[self.current_idx])
        self.ai.reset_round()

    def load_color(self, color_name):
        self.target_color = color_name
        self.celebration = False
        self.celebration_timer = 0.0
        self.word_errors = 0
        self.start_time = time.time()
        self.repeat_timer = 0.0
        
        # AI adaptive options (2 to 4 balloons)
        option_count = self.ai.get_option_count("colors")
        
        distractors = [c for c in self.colors_pool if c != self.target_color]
        random.shuffle(distractors)
        picked_distractors = distractors[:option_count - 1]
        
        balloon_choices = picked_distractors + [self.target_color]
        random.shuffle(balloon_choices)
        
        self.balloons = []
        
        # Spawn balloon coordinates
        col_w = W / (len(balloon_choices) + 1)
        for idx, col in enumerate(balloon_choices):
            bx = col_w * (idx + 1) + random.uniform(-15, 15)
            by = H - random.randint(180, 240)
            self.balloons.append(FloatingBalloon(col, bx, by))
            
        if self.target_color.upper() == "RED":
            self.voice.speak("Touch the RED RED balloon! RED! RED!")
        else:
            self.voice.speak(f"Touch the {self.target_color} balloon!")

    def handle_event(self, event):
        mx, my = pygame.mouse.get_pos()
        
        # Back button
        back_rect = pygame.Rect(20, 30, 160, 40)
        if event.type == pygame.MOUSEBUTTONDOWN and back_rect.collidepoint(mx, my):
            self.audio.play_sfx("click")
            return "quit"
            
        if self.celebration:
            return None
            
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            clicked_balloon = None
            for b in self.balloons:
                if b.visible and b.rect().collidepoint(mx, my):
                    clicked_balloon = b
                    break
                    
            if clicked_balloon:
                if clicked_balloon.color_name == self.target_color:
                    # Correct!
                    self.trigger_balloon_pop(clicked_balloon)
                else:
                    # Incorrect!
                    clicked_balloon.shake_t = 3.0
                    self.word_errors += 1
                    self.ai.record_mistake(self.target_color)
                    self.audio.play_sfx("fail")
                    
                    # Say descriptive correction voice
                    self.voice.speak(f"No, that is the {clicked_balloon.color_name} balloon!")
                    self.voice.speak(f"Can you find the {self.target_color} balloon?")
                    
                    # Adaptive check: hide balloon
                    clicked_balloon.visible = False

    def trigger_balloon_pop(self, balloon):
        self.celebration = True
        self.celebration_timer = 0.0
        
        time_spent = time.time() - self.start_time
        self.progress.log_word_attempt(self.target_color, self.word_errors, time_spent)
        
        if self.word_errors == 0:
            self.ai.record_success(self.target_color)
            
        # Success sound + balloon pop particles
        self.audio.play_sfx("success")
        self.particles.spawn_burst(balloon.x, balloon.y, count=30, shape="star", colors=[balloon.color, WHITE])
        balloon.visible = False
        
        self.voice.speak(f"Pop! Awesome job, that is {self.target_color}!")

    def update(self, dt):
        self.particles.update(dt)
        mx, my = pygame.mouse.get_pos()
        self.bg_time += dt
        
        for b in self.balloons:
            b.update(dt)
            if b.visible:
                # Hover scale
                if b.rect().collidepoint(mx, my):
                    b.scale = min(1.08, b.scale + dt * 1.5)
                else:
                    b.scale = max(1.0, b.scale - dt * 1.5)
                    
        if self.celebration:
            self.celebration_timer += dt
            if self.celebration_timer >= 2.5:
                self.current_idx += 1
                if self.current_idx >= self.total_colors:
                    pass  # check_completed will handle this
                else:
                    self.load_color(self.round_colors[self.current_idx])
        else:
            # WORD REPEAT: Keep saying the color until child pops the right one
            self.repeat_timer += dt
            if self.repeat_timer >= WORD_REPEAT_INTERVAL:
                self.repeat_timer = 0.0
                if not self.voice.is_busy():
                    if self.target_color.upper() == "RED":
                        self.voice.speak("Pop the RED RED balloon! RED! RED!")
                    else:
                        self.voice.speak(f"Pop the {self.target_color} balloon!")

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
        name_rect = pygame.Rect(200, 30, 160, 40)
        tag_rect_n = pygame.Rect(220, 15, 120, 22)
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
        
        comp_ratio = self.current_idx / float(self.total_colors)
        fill_w = int(180 * comp_ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(W // 2 - 90, 35, fill_w, 30)
            draw_gradient_rect(surface, (255, 183, 77), (255, 112, 67), fill_rect, radius=8)
            
        pct_font = load_font(13, bold=True)
        pct_text = pct_font.render(f"COLOR {self.current_idx + 1} OF {self.total_colors}", True, BLACK)
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
        
        # Draw chalkboard card for target instructions (prevents overlapping background)
        board_rect = pygame.Rect(W // 2 - 250, 90, 500, 60)
        draw_rounded_rect_with_shadow(surface, (139, 69, 19), board_rect, radius=12, border_width=3, border_color=WHITE)
        inner_rect = board_rect.inflate(-8, -8)
        pygame.draw.rect(surface, (30, 45, 35), inner_rect, border_radius=8)
        
        req_font = load_font(21, bold=True)
        part1 = req_font.render("POP THE ", True, WHITE)
        part2 = req_font.render(self.target_color, True, BALLOON_COLORS.get(self.target_color, RED))
        part3 = req_font.render(" BALLOON!", True, WHITE)
        
        total_w = part1.get_width() + part2.get_width() + part3.get_width()
        start_x = board_rect.centerx - total_w // 2
        cy = board_rect.centery
        
        surface.blit(part1, part1.get_rect(midleft=(start_x, cy)))
        surface.blit(part2, part2.get_rect(midleft=(start_x + part1.get_width(), cy)))
        surface.blit(part3, part3.get_rect(midleft=(start_x + part1.get_width() + part2.get_width(), cy)))

        # Draw balloons
        for b in self.balloons:
            # Assist glow if error gets high
            if self.ai.get_hint_level(self.target_color) >= 1 and b.color_name == self.target_color and b.visible:
                draw_glow_circle(surface, GOLD, (b.x, b.y), 45, glow_width=15)
            b.draw(surface)
        
        # Success overlay banner
        if self.celebration:
            banner = pygame.Rect(W // 2 - 250, H // 2 - 50, 500, 100)
            draw_rounded_rect_with_shadow(surface, GOLD, banner, radius=22, shadow_offset=(3, 5), border_width=4, border_color=(139, 69, 19))
            draw_sticker_text(surface, f"⭐ {self.target_color}! ⭐", load_font(40, bold=True), (139, 69, 19), WHITE, banner.center, border_size=2)

    @property
    def active_game_completed(self):
        return self.current_idx >= self.total_colors

    @active_game_completed.setter
    def active_game_completed(self, val):
        pass

    def check_completed(self):
        if self.current_idx >= self.total_colors:
            return "completed"
        return None
