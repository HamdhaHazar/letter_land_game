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

class Asteroid:
    def __init__(self, text, x, y, speed_mult=1.0):
        self.text = text.upper()
        self.x = x
        self.y = y
        self.size = random.randint(60, 75)
        
        # Velocity drifting from right to left
        self.vx = -random.uniform(1.2, 2.5) * speed_mult
        self.vy = random.uniform(-0.4, 0.4)
        
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-1.0, 1.0)
        self.scale = 1.0
        self.visible = True
        
        # Craters offset positions (fixed)
        self.craters = []
        for _ in range(3):
            self.craters.append((
                random.randint(-self.size//3, self.size//3),
                random.randint(-self.size//3, self.size//3),
                random.randint(6, 12)
            ))

    def update(self, dt):
        if not self.visible:
            return
            
        self.x += self.vx
        self.y += self.vy
        self.angle += self.rot_speed
        
        # Wrap around to right side if off-screen left
        if self.x < -self.size:
            self.x = W + self.size
            self.y = random.randint(180, H - 150)

    def rect(self):
        s = int(self.size * self.scale)
        return pygame.Rect(self.x - s // 2, self.y - s // 2, s, s)

    def draw(self, surface, font):
        if not self.visible:
            return
            
        s = int(self.size * self.scale)
        # Draw golden glow behind rock if hovered/scaled
        if self.scale > 1.01:
            draw_glow_circle(surface, GOLD, (self.x, self.y), s // 2, glow_width=12)
            
        # Asteroid base rock drawing
        rock_surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        cx, cy = s, s
        
        # Render grey rocky polygon outline (sticker-like cartoon rock)
        points = []
        num_points = 8
        for i in range(num_points):
            angle = math.pi * 2 * i / num_points
            r_dist = s // 2 + random.randint(-5, 5)
            px = cx + int(r_dist * math.cos(angle))
            py = cy + int(r_dist * math.sin(angle))
            points.append((px, py))
            
        # Draw shadow
        pygame.draw.polygon(rock_surf, (0, 0, 0, 70), [(p[0]+2, p[1]+3) for p in points])
        # Draw Rock body
        pygame.draw.polygon(rock_surf, (140, 130, 130), points)
        pygame.draw.polygon(rock_surf, WHITE, points, 3)
        
        # Draw craters
        for cx_off, cy_off, cr_size in self.craters:
            pygame.draw.circle(rock_surf, (90, 80, 80), (cx + cx_off, cy + cy_off), cr_size)
            pygame.draw.circle(rock_surf, (180, 170, 170), (cx + cx_off, cy + cy_off), cr_size, 2)
            
        # Rotate
        rotated = pygame.transform.rotate(rock_surf, self.angle)
        surface.blit(rotated, (self.x - rotated.get_width()//2, self.y - rotated.get_height()//2))
        
        # Draw vocabulary text floating centered on the asteroid
        lbl_font = load_font(18, bold=True)
        draw_sticker_text(surface, self.text, lbl_font, CREAM_WHITE, BLACK, (self.x, self.y), border_size=2)

class SpeedGame:
    def __init__(self, level_idx, voice_system, audio_manager, progress_tracker, ai_engine):
        self.level_idx = level_idx
        self.voice = voice_system
        self.audio = audio_manager
        self.progress = progress_tracker
        self.ai = ai_engine
        
        # Space category or final mix
        self.category = "space" if self.level_idx == 5 else "final"
        
        import os, json
        vocab_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "vocabulary.json")
        try:
            with open(vocab_path, "r") as f:
                vocab_data = json.load(f)
            if self.category == "space":
                self.words_pool = vocab_data.get("space", [])
            else:
                # Merge multiple categories for final level
                self.words_pool = vocab_data.get("space", []) + vocab_data.get("animals", []) + vocab_data.get("food", [])
        except:
            self.words_pool = [
                {"word": "STAR", "description": "Glows in the sky!"},
                {"word": "MOON", "description": "Bright circle at night!"},
                {"word": "ROCKET", "description": "Blasts off into space!"},
                {"word": "SUN", "description": "Hot yellow star!"}
            ]
            
        random.shuffle(self.words_pool)
        self.words = self.words_pool[:4] # 4 targets per round
        
        self.current_idx = 0
        self.total_words = len(self.words)
        
        self.target_word = ""
        self.description = ""
        self.asteroids = []
        self.particles = ParticleSystem()
        
        self.word_errors = 0
        self.start_time = 0
        
        self.celebration = False
        self.celebration_timer = 0.0
        
        # Word repeat timer
        self.repeat_timer = 0.0
        
        # Background enhancements
        self.bg_time = 0.0
        self.shooting_stars = []
        self.crystals = []
        for _ in range(8):
            self.crystals.append({
                "orbit_radius": random.randint(310, 370),
                "angle": random.uniform(0, math.pi * 2),
                "speed": random.uniform(0.15, 0.4),
                "radius": random.randint(3, 7),
                "color": random.choice([(255, 215, 0), (0, 255, 255), (255, 255, 255)])
            })

    def get_instruction_text(self):
        return "Listen to the word I speak, and tap the correct flying asteroid as fast as you can!"

    def start_game(self):
        self.current_idx = 0
        self.load_word(self.words[self.current_idx])
        self.ai.reset_round()

    def load_word(self, word_obj):
        self.target_word = word_obj["word"].upper()
        self.description = word_obj["description"]
        self.celebration = False
        self.celebration_timer = 0.0
        self.word_errors = 0
        self.start_time = time.time()
        self.repeat_timer = 0.0
        
        # Speed modifier from adaptive AI
        speed_mult = self.ai.get_speed_multiplier()
        
        # Pick incorrect options
        all_choices = [w["word"].upper() for w in self.words_pool if w["word"].upper() != self.target_word]
        random.shuffle(all_choices)
        picked_choices = all_choices[:3] # 3 distractors
        
        choices = picked_choices + [self.target_word]
        random.shuffle(choices)
        
        self.asteroids = []
        
        # Distribute asteroids horizontally across the screen
        col_w = W / (len(choices) + 1)
        for idx, text in enumerate(choices):
            ax = col_w * (idx + 1) + random.uniform(-20, 20)
            ay = random.randint(180, H - 240)
            self.asteroids.append(Asteroid(text, ax, ay, speed_mult))
            
        # Audio call
        self.voice.speak(self.target_word)

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
            clicked_ast = None
            for ast in self.asteroids:
                if ast.visible and ast.rect().collidepoint(mx, my):
                    clicked_ast = ast
                    break
                    
            if clicked_ast:
                if clicked_ast.text == self.target_word:
                    self.trigger_asteroid_pop(clicked_ast)
                else:
                    # Mistake
                    self.word_errors += 1
                    self.ai.record_mistake(self.target_word)
                    self.audio.play_sfx("fail")
                    
                    # Highlight target if struggling removed
                    clicked_ast.visible = False

    def trigger_asteroid_pop(self, ast):
        self.celebration = True
        self.celebration_timer = 0.0
        
        time_spent = time.time() - self.start_time
        self.progress.log_word_attempt(self.target_word, self.word_errors, time_spent)
        
        if self.word_errors == 0:
            self.ai.record_success(self.target_word)
            
        self.audio.play_sfx("success")
        # Asteroid explosion particle bursts
        self.particles.spawn_burst(ast.x, ast.y, count=30, shape="star", colors=[(230, 230, 230), (130, 120, 120)])
        ast.visible = False
        
        self.voice.speak(self.target_word)

    def update(self, dt):
        self.particles.update(dt)
        mx, my = pygame.mouse.get_pos()
        self.bg_time += dt
        
        # Update shooting stars
        if random.random() < 0.015 and len(self.shooting_stars) < 3:
            self.shooting_stars.append({
                "x": random.randint(W // 2, W),
                "y": -20,
                "vx": -random.uniform(300, 600),
                "vy": random.uniform(200, 400),
                "length": random.randint(40, 80),
                "color": random.choice([(255, 105, 180), (0, 229, 255), (255, 215, 0), (255, 255, 255)])
            })
        for s in self.shooting_stars:
            s['x'] += s['vx'] * dt
            s['y'] += s['vy'] * dt
        self.shooting_stars = [s for s in self.shooting_stars if s['x'] > -100 and s['y'] < H + 100]
        
        # Update orbiting crystals
        for c in self.crystals:
            c['angle'] += c['speed'] * dt
            
        for ast in self.asteroids:
            ast.update(dt)
            if ast.visible:
                if ast.rect().collidepoint(mx, my):
                    ast.scale = min(1.08, ast.scale + dt * 1.5)
                else:
                    ast.scale = max(1.0, ast.scale - dt * 1.5)
                    
        if self.celebration:
            self.celebration_timer += dt
            if self.celebration_timer >= 2.5:
                self.current_idx += 1
                if self.current_idx >= self.total_words:
                    pass  # check_completed will handle this
                else:
                    self.load_word(self.words[self.current_idx])
        else:
            # WORD REPEAT: Keep saying the target word until child taps it
            self.repeat_timer += dt
            if self.repeat_timer >= WORD_REPEAT_INTERVAL:
                self.repeat_timer = 0.0
                if not self.voice.is_busy():
                    self.voice.speak(self.target_word)

    def draw(self, surface):
        # 1. Deep space backdrop with floating stars
        draw_gradient_rect(surface, (15, 10, 25), (35, 15, 60), (0, 0, W, H))
        
        # Distant nebula/galaxy glow color shifting
        neb_r = int(130 + math.sin(self.bg_time * 0.5) * 40)
        neb_g = int(60 + math.cos(self.bg_time * 0.7) * 30)
        neb_b = int(220 + math.sin(self.bg_time * 0.3) * 35)
        
        nebula_surf = pygame.Surface((300, 300), pygame.SRCALPHA)
        pygame.draw.circle(nebula_surf, (neb_r, neb_g, neb_b, 35), (150, 150), 90)
        pygame.draw.circle(nebula_surf, (neb_b, neb_r, neb_g, 18), (150, 150), 130)
        surface.blit(nebula_surf, (W - 280, 70))
        
        # Draw shooting stars
        for s in self.shooting_stars:
            pygame.draw.line(surface, s['color'], (s['x'], s['y']), (s['x'] - s['vx']*0.08, s['y'] - s['vy']*0.08), 3)
            pygame.draw.circle(surface, WHITE, (int(s['x']), int(s['y'])), 4)
            
        # Floating background starry dots with blinking effects
        star_colors = [
            (255, 255, 255),  # White
            (255, 223, 0),    # Gold
            (0, 229, 255),    # Cyan
            (255, 105, 180)   # Hot Pink
        ]
        for idx in range(25):
            blink = int(math.sin(self.bg_time * 4.0 + idx) * 127 + 128)
            col = star_colors[idx % len(star_colors)]
            x = (idx * 60 + int(self.bg_time * 18.0)) % (W + 20) - 10
            y = int(math.sin(idx * 1.5) * 230) + H // 2 - 40
            pygame.draw.circle(surface, col, (x, y), 2 + (idx % 2))
            
        # Draw a cute floating alien saucer in the space background
        saucer_x = (int(self.bg_time * 20)) % (W + 160) - 80
        saucer_y = 130 + int(math.sin(self.bg_time * 2.5) * 18)
        # Draw glass dome
        pygame.draw.circle(surface, (135, 206, 250, 200), (saucer_x, saucer_y - 6), 14)
        # Draw metallic saucer body
        pygame.draw.ellipse(surface, (192, 192, 192), (saucer_x - 28, saucer_y, 56, 14))
        # Draw glowing neon green lights on the saucer
        light_color = (0, 255, 127) if int(self.bg_time * 5) % 2 == 0 else (255, 215, 0)
        pygame.draw.circle(surface, light_color, (saucer_x - 16, saucer_y + 7), 3)
        pygame.draw.circle(surface, light_color, (saucer_x, saucer_y + 7), 3)
        pygame.draw.circle(surface, light_color, (saucer_x + 16, saucer_y + 7), 3)
        
        # 2. Draw giant planetary body at the bottom for massive outer space engagement
        pygame.draw.ellipse(surface, (0, 0, 0, 30), (W // 2 - 300, H - 180, 600, 220))
        # Orange gas giant planet
        pygame.draw.ellipse(surface, (255, 127, 80), (W // 2 - 290, H - 170, 580, 250))
        # Planet glowing ring outline
        pygame.draw.ellipse(surface, (255, 200, 100), (W // 2 - 380, H - 80, 760, 50), 6)
        
        # Draw orbiting crystals (high quality visual details)
        for c in self.crystals:
            cx = W // 2 + int(math.cos(c['angle']) * c['orbit_radius'])
            cy = (H - 45) + int(math.sin(c['angle']) * c['orbit_radius'] * 0.38)
            pygame.draw.circle(surface, c['color'], (cx, cy), c['radius'])
            draw_glow_circle(surface, c['color'], (cx, cy), c['radius'], glow_width=6)
            
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
        
        comp_ratio = self.current_idx / float(self.total_words)
        fill_w = int(180 * comp_ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(W // 2 - 90, 35, fill_w, 30)
            draw_gradient_rect(surface, (255, 183, 77), (255, 112, 67), fill_rect, radius=8)
            
        pct_font = load_font(13, bold=True)
        pct_text = pct_font.render(f"ASTEROID {self.current_idx + 1} OF {self.total_words}", True, BLACK)
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
        
        # Draw asteroids
        for ast in self.asteroids:
            # Assist glow halo if struggling
            if self.ai.get_hint_level(self.target_word) >= 1 and ast.text == self.target_word and ast.visible:
                draw_glow_circle(surface, GOLD, (ast.x, ast.y), 45, glow_width=18)
            ast.draw(surface, load_font(16, bold=True))
            
        # 3D Cyber cockpit panel base shadow
        base_rect = pygame.Rect(W // 2 - 130, 96, 260, 65)
        pygame.draw.rect(surface, (20, 5, 40), base_rect, border_radius=15)
        
        # Blinking/Flickering neon colors
        t = pygame.time.get_ticks() * 0.001
        flicker = 1.0 if (int(t * 18) % 12) not in [3, 4, 9] else 0.3
        pulse = 1.0 + math.sin(t * 6.0) * 0.08
        
        border_color = (0, int(220 * flicker), int(255 * flicker))
        text_color = (int(255 * flicker), int(230 * flicker), int(50 * flicker))
        
        board_rect = pygame.Rect(W // 2 - 130, 90, 260, 65)
        draw_rounded_rect_with_shadow(surface, (40, 15, 80), board_rect, radius=12, border_width=3, border_color=border_color)
        inner_rect = board_rect.inflate(-8, -8)
        pygame.draw.rect(surface, (10, 5, 25), inner_rect, border_radius=8)
        
        # Blinking neon glint stars / sparkles
        sparkle_angle = t * 4.0
        for i in range(2):
            sx = board_rect.x + (i * 240) + int(math.cos(sparkle_angle + i * math.pi) * 8)
            sy = board_rect.centery + int(math.sin(sparkle_angle + i * math.pi) * 8)
            pygame.draw.circle(surface, (0, 255, 255), (sx, sy), 4)
            pygame.draw.circle(surface, WHITE, (sx, sy), 2)
            
        # Render 3D pulsing target word
        word_size = int(32 * pulse)
        word_font = load_font(word_size, bold=True)
        
        # Shadow text layer
        sh_surf = word_font.render(self.target_word, True, (0, 100, 255))
        sh_surf.set_alpha(int(130 * flicker))
        surface.blit(sh_surf, sh_surf.get_rect(center=(board_rect.centerx + 3, board_rect.centery + 3)))
        
        # Main text layer
        word_surf = word_font.render(self.target_word, True, text_color)
        surface.blit(word_surf, word_surf.get_rect(center=board_rect.center))
        
        if self.celebration:
            banner = pygame.Rect(W // 2 - 250, H // 2 - 50, 500, 100)
            draw_rounded_rect_with_shadow(surface, GOLD, banner, radius=22, shadow_offset=(3, 5), border_width=4, border_color=(139, 69, 19))
            draw_sticker_text(surface, f"⭐ {self.target_word}! ⭐", load_font(40, bold=True), (139, 69, 19), WHITE, banner.center, border_size=2)

    @property
    def active_game_completed(self):
        return self.current_idx >= self.total_words

    @active_game_completed.setter
    def active_game_completed(self, val):
        pass

    def check_completed(self):
        if self.current_idx >= self.total_words:
            return "completed"
        return None
