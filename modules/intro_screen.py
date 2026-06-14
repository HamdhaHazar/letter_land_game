import pygame
import math
import random
from game_core import (W, H, GOLD, CREAM_WHITE, WHITE, BLACK, SUNNY_YELLOW,
                       WARM_BG_TOP, WARM_BG_BOT, WARM_ACCENT, WARM_HEADER, WARM_CORAL, WARM_GREEN,
                       load_font, draw_rounded_rect_with_shadow, draw_gradient_rect,
                       draw_sticker_text, draw_glow_circle)
from systems.animation_engine import Easing, ParticleSystem

class IntroScreen:
    def __init__(self, voice_system, audio_manager):
        self.voice = voice_system
        self.audio = audio_manager
        
        # Parallax background variables
        self.bg_time = 0.0
        
        # Logo zoom/bounce animation variables
        self.logo_t = 0.0
        self.logo_scale = 0.0
        
        # Particles
        self.particles = ParticleSystem()
        
        # Play Intro Music
        self.audio.play_music("intro")
        
        # Button state
        self.button_pulse = 0.0
        
    def run_frame(self, surface, dt, mouse_pos):
        self.bg_time += dt
        self.logo_t = min(1.0, self.logo_t + dt * 1.5)
        self.button_pulse += dt * 3.0
        
        # Parallax calculations based on mouse offset from center
        mx, my = mouse_pos
        offset_x = (mx - W // 2) * 0.03
        offset_y = (my - H // 2) * 0.03
        
        # 1. Layer 1: Warm golden gradient sky
        draw_gradient_rect(surface, WARM_BG_TOP, WARM_BG_BOT, (0, 0, W, H))
        
        # Spawn floating sparkles in the sky
        if random.random() < 0.05:
            self.particles.spawn_burst(random.randint(0, W), random.randint(0, H//2), count=1, shape="star", colors=[WHITE, GOLD])
            
        self.particles.update(dt)
        self.particles.draw(surface)
        
        # 2. Layer 2: Distant Hills (warm sage green)
        hill_color_1 = (180, 210, 140)
        points_l2 = []
        for x in range(0, W + 10, 40):
            y = H * 0.65 + math.sin(x * 0.003 + self.bg_time * 0.1) * 35 + offset_y * 0.5
            points_l2.append((x + offset_x * 0.5, y))
        points_l2.append((W, H))
        points_l2.append((0, H))
        pygame.draw.polygon(surface, hill_color_1, points_l2)
        
        # 3. Layer 3: Closer Jungle Hills (warm green)
        hill_color_2 = (100, 170, 80)
        points_l3 = []
        for x in range(0, W + 10, 30):
            y = H * 0.76 + math.sin(x * 0.006 - self.bg_time * 0.2) * 20 + offset_y * 1.2
            points_l3.append((x + offset_x * 1.2, y))
        points_l3.append((W, H))
        points_l3.append((0, H))
        pygame.draw.polygon(surface, hill_color_2, points_l3)
        
        # Draw foreground warm bushes (Layer 4)
        bush_color = (76, 140, 60)
        pygame.draw.circle(surface, bush_color, (int(-30 + offset_x * 2.2), int(H * 0.95 + offset_y * 2.2)), 110)
        pygame.draw.circle(surface, bush_color, (int(W + 30 + offset_x * 2.2), int(H * 0.95 + offset_y * 2.2)), 110)
        
        # 4. Animated "WORDS LAND" Logo (Bounce + Zoom)
        logo_ease = Easing.ease_out_back(self.logo_t)
        self.logo_scale = logo_ease * 1.15
        
        title_font = load_font(int(85 * self.logo_scale), bold=True)
        sub_font = load_font(int(24 * self.logo_scale), bold=True)
        
        # Logo center
        logo_y = H // 3 + int(math.sin(self.bg_time * 2.0) * 12)
        
        # Draw logo glow circle (golden warm)
        draw_glow_circle(surface, GOLD, (W // 2, logo_y), int(160 * self.logo_scale), glow_width=25)
        
        # Sticker Text: WORDS LAND (golden on warm brown outline)
        draw_sticker_text(surface, "WORDS LAND", title_font, SUNNY_YELLOW, (139, 69, 19), (W // 2, logo_y), border_size=7)
        
        # Cute banner below the title (warm amber)
        banner_w = int(360 * self.logo_scale)
        banner_h = int(40 * self.logo_scale)
        if banner_w > 10:
            draw_rounded_rect_with_shadow(surface, WARM_HEADER, (W//2 - banner_w//2, logo_y + 60, banner_w, banner_h), radius=10, shadow_offset=(2,3))
            draw_sticker_text(surface, "🌟 THE GREAT VOCABULARY ADVENTURE 🌟", sub_font, CREAM_WHITE, BLACK, (W // 2, logo_y + 60 + banner_h//2), border_size=2)
            
        # 5. Play Button (Pulse scale) — warm coral/orange
        btn_scale = 1.0 + math.sin(self.button_pulse) * 0.06
        btn_w = int(280 * btn_scale)
        btn_h = int(75 * btn_scale)
        btn_x = W // 2 - btn_w // 2
        btn_y = H // 2 + 120
        
        btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        btn_color = WARM_CORAL
        
        draw_rounded_rect_with_shadow(surface, btn_color, btn_rect, radius=22, shadow_offset=(3, 6), border_width=4, border_color=WHITE)
        
        # Button Text
        btn_font = load_font(30, bold=True)
        draw_sticker_text(surface, "START ADVENTURE!", btn_font, CREAM_WHITE, BLACK, btn_rect.center, border_size=3)
        
        # Return if play button clicked or ENTER pressed
        return btn_rect
