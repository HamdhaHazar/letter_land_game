import pygame
import math
import random
from game_core import (W, H, CREAM_WHITE, DEEP_SKY, GOLD, WHITE, BLACK, PURPLE, SUNNY_YELLOW, RED, ORANGE,
                       LIME_GREEN, WARM_BG_TOP, WARM_BG_BOT, WARM_ACCENT, WARM_HEADER, WARM_CARD,
                       WARM_CORAL, WARM_GREEN, WARM_PEACH,
                       load_font, draw_rounded_rect_with_shadow, draw_gradient_rect,
                       draw_sticker_text, draw_glow_circle, MonkeyGuide, BirdGuide,
                       draw_vector_star, draw_vector_lock, draw_vector_seed, draw_vector_crown)
from systems.animation_engine import ParticleSystem

# Coordinates for the winding roadmap path
LEVEL_COORDINATES = [
    (140, 580), # 0. Animals
    (310, 480), # 1. Food
    (430, 590), # 2. Objects
    (580, 420), # 3. Colors
    (730, 520), # 4. Actions
    (880, 360), # 5. Space
    (750, 180)  # 6. Final Challenge
]

LEVEL_INFO = [
    {"name": "Animal Level", "emoji": "🐦", "theme": "jungle"},
    {"name": "Food Level", "emoji": "🍎", "theme": "food"},
    {"name": "Object Level", "emoji": "🚗", "theme": "objects"},
    {"name": "Color Level", "emoji": "🌈", "theme": "food"},
    {"name": "Actions Level", "emoji": "🏃", "theme": "jungle"},
    {"name": "Space Bonus", "emoji": "🚀", "theme": "space"},
    {"name": "Final Star", "emoji": "⭐", "theme": "space"}
]

class MapSystem:
    def __init__(self, voice_system, audio_manager, progress_tracker):
        self.voice = voice_system
        self.audio = audio_manager
        self.progress = progress_tracker
        
        # Bird character
        self.monkey = BirdGuide()
        self.monkey.stage = self.progress.data["monkey_stage"]
        
        # Position monkey at player's current level node
        curr_lvl = self.progress.data["current_level"]
        start_coord = LEVEL_COORDINATES[min(curr_lvl, len(LEVEL_COORDINATES) - 1)]
        self.monkey.x = start_coord[0]
        self.monkey.y = start_coord[1] - 40
        self.monkey.target_x = self.monkey.x
        self.monkey.target_y = self.monkey.y
        
        self.last_known_level = curr_lvl
        self.bg_time = 0.0
        self.particles = ParticleSystem()
        
        # Speak instructions on map start
        nickname = self.progress.get_nickname()
        self.voice.speak(f"Hey {nickname}! Choose a level to start your adventure!")

    def update(self, dt):
        self.bg_time += dt
        self.particles.update(dt)
        
        # Check if monkey stage evolved
        self.monkey.stage = self.progress.data["monkey_stage"]
        
        # Level progress detection (for hopping movement)
        curr_lvl = self.progress.data["current_level"]
        if curr_lvl != self.last_known_level:
            # Let the bird hop!
            target_coord = LEVEL_COORDINATES[min(curr_lvl, len(LEVEL_COORDINATES) - 1)]
            self.monkey.set_target(target_coord[0], target_coord[1] - 40)
            self.last_known_level = curr_lvl
            self.audio.play_sfx("unlock")
            self.particles.spawn_burst(target_coord[0], target_coord[1], count=15, shape="star", colors=[GOLD, WHITE])
            
        self.monkey.update(dt)

    def handle_click(self, pos):
        """Returns level_index if clicked, 'dashboard' if clicked, 'back' if clicked, or None."""
        mx, my = pos
        
        # Check Top-Right Quit Button (closes app)
        quit_rect = pygame.Rect(W - 65, 20, 45, 45)
        if quit_rect.collidepoint(mx, my):
            self.audio.play_sfx("click")
            pygame.quit()
            import sys
            sys.exit()
            
        # (Bottom Navigation Dock click check removed)
            
        # Check Level Nodes
        for idx, (lx, ly) in enumerate(LEVEL_COORDINATES):
            # Check proximity to node (radius 36)
            dist = math.hypot(mx - lx, my - ly)
            if dist <= 38:
                # Is level unlocked?
                unlocked = (idx == 0) or ((idx - 1) in self.progress.data["completed_levels"])
                if unlocked:
                    self.audio.play_sfx("click")
                    return idx
                else:
                    self.audio.play_sfx("fail")
                    self.voice.speak("Oops! This level is locked. Complete the previous level first!")
                    return None
        return None

    def draw(self, surface):
        # 1. Vibrant solid Sky Yellow background matching Reference Image 1
        sky_yellow = (255, 235, 59)
        surface.fill(sky_yellow)
        
        # 2. Draw grass green landscape container
        grass_green = (139, 195, 74)
        # Main land covering the middle and upper areas
        pygame.draw.rect(surface, grass_green, (0, 80, W, H - 160), border_radius=25)
        
        # River at bottom-left corner with sandy beach border
        pygame.draw.circle(surface, (3, 169, 244), (0, H - 80), 200)
        pygame.draw.circle(surface, (255, 224, 130), (0, H - 80), 200, 10)
        
        # Ambient clouds in map
        for i in range(3):
            cx = (i * 350 + int(self.bg_time * 5)) % (W + 200) - 100
            cy = 120 + i * 30
            pygame.draw.circle(surface, (255, 255, 255, 180), (cx, cy), 30)
            pygame.draw.circle(surface, (255, 255, 255, 180), (cx + 20, cy - 8), 25)
            pygame.draw.circle(surface, (255, 255, 255, 180), (cx - 15, cy), 22)

        # Draw a few cartoon trees
        for tx, ty in [(180, 240), (220, 260), (200, 460), (740, 150), (700, 360), (750, 380), (120, 110), (810, 520)]:
            # Tree shadow
            pygame.draw.ellipse(surface, (0, 0, 0, 40), (tx - 15, ty + 12, 30, 8))
            # Tree trunk
            pygame.draw.rect(surface, (139, 69, 19), (tx - 3, ty, 6, 15))
            # Tree top crown (warm orange circular foliage matching reference image)
            pygame.draw.circle(surface, (255, 127, 80), (tx, ty), 16)
            pygame.draw.circle(surface, WHITE, (tx, ty), 16, 2)

        # 3. Draw curved winding trail pathway matching reference image
        path_color = (255, 218, 120)    # Sandy gold trail color
        border_color = (255, 193, 7)    # Golden amber border
        
        # Base road trail (thick shadow/border)
        for i in range(len(LEVEL_COORDINATES) - 1):
            p1 = LEVEL_COORDINATES[i]
            p2 = LEVEL_COORDINATES[i+1]
            pygame.draw.line(surface, border_color, p1, p2, 28)
            pygame.draw.line(surface, path_color, p1, p2, 20)
            
        # Draw small dotted trail step markers inside path
        for i in range(len(LEVEL_COORDINATES) - 1):
            p1 = LEVEL_COORDINATES[i]
            p2 = LEVEL_COORDINATES[i+1]
            dx, dy = p2[0] - p1[0], p2[1] - p1[1]
            dist = math.hypot(dx, dy)
            steps = int(dist / 22)
            if steps > 0:
                for s in range(1, steps, 2):
                    t = s / steps
                    sx = int(p1[0] * (1-t) + p2[0] * t)
                    sy = int(p1[1] * (1-t) + p2[1] * t)
                    pygame.draw.circle(surface, WHITE, (sx, sy), 4)

        # 4. Draw Level Nodes as White Cards with Gold Borders and Stars
        for idx, (lx, ly) in enumerate(LEVEL_COORDINATES):
            info = LEVEL_INFO[idx]
            
            unlocked = (idx == 0) or ((idx - 1) in self.progress.data["completed_levels"])
            completed = idx in self.progress.data["completed_levels"]
            current = (idx == self.progress.data["current_level"])
            
            bob = math.sin(self.bg_time * 2.5 + idx) * 4
            ny = ly + bob
            
            # Shadow
            pygame.draw.ellipse(surface, (0, 0, 0, 40), (lx - 26, ly + 25, 52, 10))
            
            # Glow circle if current
            if current and unlocked:
                draw_glow_circle(surface, SUNNY_YELLOW, (lx, int(ny)), 42, glow_width=18)
                
            # Node body color — white/creamy card matching reference screen
            if not unlocked:
                node_color = (235, 235, 235)  # Light grey locked card
                border_col = (180, 180, 180)  # Grey border
            elif completed:
                node_color = (76, 175, 80)     # Green completed card
                border_col = GOLD             # Gold border
            else:
                node_color = WHITE             # Active white card
                border_col = (255, 152, 0)     # Vibrant orange border
                
            # Draw circular node
            pygame.draw.circle(surface, node_color, (lx, int(ny)), 36)
            pygame.draw.circle(surface, border_col, (lx, int(ny)), 36, 4)
            
            # Star in center
            if not unlocked:
                # Lock symbol (draw programmatically)
                draw_vector_lock(surface, (lx, int(ny)), size=15)
            else:
                # Render star (draw programmatically)
                star_color = GOLD if not completed else WHITE
                draw_vector_star(surface, (lx, int(ny) - 2), size=16, color=star_color, border_color=WHITE)
                
            # Badge completion checkmark at bottom of node
            if completed:
                check_font = load_font(14, bold=True)
                check_rect = pygame.Rect(lx - 12, int(ny) + 24, 24, 18)
                draw_rounded_rect_with_shadow(surface, LIME_GREEN, check_rect, radius=5, shadow_offset=(1, 1), border_width=1, border_color=WHITE)
                draw_sticker_text(surface, "✓", check_font, WHITE, BLACK, check_rect.center, border_size=1)
                
            # Level tags/labels
            tag_font = load_font(15, bold=True)
            draw_sticker_text(surface, info["name"], tag_font, CREAM_WHITE, BLACK, (lx, int(ny) - 52), border_size=2)

        # 5. Draw particles and Tweety the Bird hops
        self.particles.draw(surface)
        self.monkey.draw(surface)

        # Fetch mouse position to handle hover interactive states
        mx, my = pygame.mouse.get_pos()

        # 6. Top Left: Progress capsule
        bar_rect = pygame.Rect(20, 20, 200, 45)
        bar_hovered = bar_rect.collidepoint(mx, my)
        
        if bar_hovered:
            draw_rect = bar_rect.inflate(6, 6)
            draw_glow_circle(surface, ORANGE, draw_rect.center, 55, glow_width=25)
            border_color = WHITE
            shadow_offset = (2, 4)
            radius = 15
        else:
            draw_rect = bar_rect
            border_color = WARM_ACCENT
            shadow_offset = (1, 2)
            radius = 12
            
        draw_rounded_rect_with_shadow(surface, WHITE, draw_rect, radius=radius, shadow_offset=shadow_offset, border_width=3, border_color=border_color)
        
        comp_ratio = len(self.progress.data["completed_levels"]) / float(len(LEVEL_COORDINATES))
        max_fill_w = draw_rect.w - 10
        fill_w = int(max_fill_w * comp_ratio)
        if fill_w > 0:
            fill_rect = pygame.Rect(draw_rect.x + 5, draw_rect.y + 5, fill_w, draw_rect.h - 10)
            draw_gradient_rect(surface, (255, 183, 77), (255, 87, 34), fill_rect, radius=radius - 4)
            
        pct_font = load_font(13 if bar_hovered else 14, bold=True)
        pct_text = f"🏆 PROGRESS: {int(comp_ratio*100)}%"
        draw_sticker_text(surface, pct_text, pct_font, WHITE, BLACK, draw_rect.center, border_size=2)

        # 7. Top Center: 3 Rounded Stats Cards (Stars count, Seeds count, Nickname)
        start_x = W // 2 - 280
        pills_info = [
            {
                "icon": "⭐", 
                "text": f"STARS: {self.progress.data['stars']}", 
                "glow": SUNNY_YELLOW,
                "grad_top": (255, 235, 59),
                "grad_bot": (255, 160, 0)
            },
            {
                "icon": "🌾", 
                "text": f"SEEDS: {self.progress.data['bananas']}", 
                "glow": LIME_GREEN,
                "grad_top": (197, 225, 165),
                "grad_bot": (104, 159, 56)
            },
            {
                "icon": "👑", 
                "text": f"{self.progress.get_nickname().upper()}", 
                "glow": DEEP_SKY,
                "grad_top": (144, 202, 249),
                "grad_bot": (21, 101, 192)
            }
        ]
        
        for idx, pill in enumerate(pills_info):
            px = start_x + idx * 200
            pill_rect = pygame.Rect(px, 20, 190, 45)
            hovered = pill_rect.collidepoint(mx, my)
            
            if hovered:
                draw_rect = pill_rect.inflate(6, 6)
                draw_glow_circle(surface, pill["glow"], draw_rect.center, 50, glow_width=20)
                border_color = WHITE
                shadow_offset = (2, 4)
                radius = 15
            else:
                draw_rect = pill_rect
                border_color = (255, 255, 255)
                shadow_offset = (1, 2)
                radius = 12
                
            draw_gradient_rect(surface, pill["grad_top"], pill["grad_bot"], draw_rect, radius=radius)
            pygame.draw.rect(surface, border_color, draw_rect, 3, border_radius=radius)
            
            icon_y = draw_rect.centery
            # Draw pill icon programmatically instead of text
            if pill["icon"] == "⭐":
                draw_vector_star(surface, (draw_rect.x + 22, icon_y), size=11, color=GOLD, border_color=WHITE)
            elif pill["icon"] == "🌾":
                draw_vector_seed(surface, (draw_rect.x + 22, icon_y), size=9)
            elif pill["icon"] == "👑":
                draw_vector_crown(surface, (draw_rect.x + 22, icon_y), size=12)
            
            font_size = 12 if len(pill["text"]) > 13 else 14
            if hovered:
                font_size += 1
            text_font = load_font(font_size, bold=True)
            
            draw_sticker_text(surface, pill["text"], text_font, CREAM_WHITE, BLACK, (draw_rect.x + 110, icon_y), border_size=2)

        # 8. Top Right: Bold red "X" Quit Button to exit application
        quit_rect = pygame.Rect(W - 65, 20, 45, 45)
        if quit_rect.collidepoint(mx, my):
            quit_rect = quit_rect.inflate(6, 6)
            quit_color = (255, 100, 100)
        else:
            quit_color = (235, 50, 50)
            
        draw_rounded_rect_with_shadow(surface, quit_color, quit_rect, radius=12, shadow_offset=(1, 2), border_width=2, border_color=WHITE)
        draw_sticker_text(surface, "X", load_font(22, bold=True), WHITE, BLACK, quit_rect.center, border_size=1)


        # (Bottom Navigation Dock drawing removed)
