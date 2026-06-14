import pygame
import random
import math
from game_core import (W, H, CREAM_WHITE, WHITE, BLACK, GOLD, SUNNY_YELLOW, RED, DEEP_SKY,
                       WARM_BG_TOP, WARM_BG_BOT, WARM_ACCENT, WARM_HEADER, WARM_CARD, WARM_CORAL, WARM_GREEN,
                       load_font, draw_rounded_rect_with_shadow, draw_gradient_rect, draw_sticker_text, MonkeyGuide)
from systems.animation_engine import ParticleSystem

# Fun list of kid-friendly explorer names for the microphone voice input
KID_EXPLORER_NAMES = [
    "Daring Dino", "Happy Hippo", "Jungle Kid", "Super Star", 
    "Space Ranger", "Berry Finder", "Banana Boss", "Curious Koala", 
    "Sparkle Bear", "Rainbow Tiger"
]

class NicknameSystem:
    def __init__(self, voice_system, audio_manager, progress_tracker):
        self.voice = voice_system
        self.audio = audio_manager
        self.progress = progress_tracker
        
        self.input_text = ""
        self.active = True
        
        # Guide monkey instance
        self.monkey = MonkeyGuide(W // 4, H // 2 + 50)
        self.monkey.expression = "neutral"
        self.monkey.stage = 0 # Small monkey
        
        self.particles = ParticleSystem()
        
        # Submissions state
        self.submitted = False
        self.submitted_timer = 0.0
        
        # Speak prompt initially
        self.voice.speak("What is your explorer name?")
        
    def handle_event(self, event):
        if self.submitted:
            return
            
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if len(self.input_text.strip()) > 0:
                    self.submit_name()
            elif event.key == pygame.K_BACKSPACE:
                self.input_text = self.input_text[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.audio.play_sfx("click")
                return "back"
            else:
                # Limit length to 15 chars, allow all printable text inputs
                if len(self.input_text) < 15 and event.unicode and event.unicode.isprintable():
                    self.input_text += event.unicode
                    self.audio.play_sfx("click")

        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            # Check Back Button to go to intro screen
            back_rect = pygame.Rect(20, 20, 110, 45)
            if back_rect.collidepoint(mx, my):
                self.audio.play_sfx("click")
                return "back"
                
            # Check Microphone Button
            mic_rect = pygame.Rect(W // 2 + 280, H // 2, 56, 56)
            if mic_rect.collidepoint(mx, my):
                self.audio.play_sfx("click")
                # Simulate speech input by choosing a fun random kid explorer name
                self.input_text = random.choice(KID_EXPLORER_NAMES)
                self.voice.speak(f"Explorer name captured: {self.input_text}")
                
            # Check GO Button
            go_rect = pygame.Rect(W // 2 + 10, H // 2 + 80, 160, 50)
            if go_rect.collidepoint(mx, my) and len(self.input_text.strip()) > 0:
                self.submit_name()

    def submit_name(self):
        self.submitted = True
        self.input_text = self.input_text.strip()
        self.progress.set_nickname(self.input_text)
        
        # Wave, confetti burst, welcome voice output
        self.monkey.expression = "waving"
        self.audio.play_sfx("success")
        self.particles.spawn_burst(W // 2, H // 2, count=60, shape="confetti")
        self.voice.speak(f"Hello {self.input_text}! Welcome to Words Land!")

    def update(self, dt):
        self.monkey.update(dt)
        self.particles.update(dt)
        
        if self.submitted:
            self.submitted_timer += dt
            # If celebration complete, return True to indicate screen completion
            if self.submitted_timer >= 3.0:
                return True
        return False

    def draw(self, surface, dt):
        # Warm yellow gradient background
        draw_gradient_rect(surface, WARM_BG_TOP, WARM_BG_BOT, (0, 0, W, H))
        
        # Draw background elements
        self.particles.draw(surface)
        self.monkey.draw(surface)
        
        # Draw Back Button (top-left) — warm coral
        if not self.submitted:
            back_rect = pygame.Rect(20, 20, 110, 45)
            draw_rounded_rect_with_shadow(surface, WARM_CORAL, back_rect, radius=10, shadow_offset=(1, 2), border_width=2, border_color=WHITE)
            draw_sticker_text(surface, "◀ BACK", load_font(18, bold=True), CREAM_WHITE, BLACK, back_rect.center, border_size=2)
        
        # Speech Bubble from Monkey (warm cream card)
        bubble_x = W // 4 + 70
        bubble_y = H // 2 - 200
        bubble_w = 480
        bubble_h = 110
        draw_rounded_rect_with_shadow(surface, WARM_CARD, (bubble_x, bubble_y, bubble_w, bubble_h), radius=20, shadow_offset=(3, 4))
        
        # Triangle pointer for bubble pointing at monkey
        pygame.draw.polygon(surface, WARM_CARD, [(bubble_x, bubble_y + 50), (bubble_x - 18, bubble_y + 40), (bubble_x, bubble_y + 30)])
        pygame.draw.polygon(surface, WARM_HEADER, [(bubble_x, bubble_y + 50), (bubble_x - 18, bubble_y + 40), (bubble_x, bubble_y + 30)], 2)
        pygame.draw.rect(surface, WARM_HEADER, (bubble_x, bubble_y, bubble_w, bubble_h), 3, border_radius=20)
        
        bubble_font = load_font(25, bold=True)
        lbl1 = bubble_font.render("What is your explorer name?", True, (139, 69, 19))
        lbl2 = load_font(18).render("Type it below or tap the microphone!", True, BLACK)
        surface.blit(lbl1, lbl1.get_rect(center=(bubble_x + bubble_w//2, bubble_y + 35)))
        surface.blit(lbl2, lbl2.get_rect(center=(bubble_x + bubble_w//2, bubble_y + 75)))
        
        # Input Box (warm white card)
        input_w = 340
        input_h = 56
        input_x = W // 2 - 80
        input_y = H // 2
        input_rect = pygame.Rect(input_x, input_y, input_w, input_h)
        
        draw_rounded_rect_with_shadow(surface, WHITE, input_rect, radius=15, shadow_offset=(2, 3))
        pygame.draw.rect(surface, WARM_ACCENT, input_rect, 3, border_radius=15)
        
        # Text input display
        input_font = load_font(28, bold=True)
        display_text = self.input_text
        # Blinking cursor
        if not self.submitted and int(pygame.time.get_ticks() / 500) % 2 == 0:
            display_text += "|"
            
        txt_surf = input_font.render(display_text, True, BLACK)
        surface.blit(txt_surf, txt_surf.get_rect(midleft=(input_x + 15, input_y + input_h//2)))
        
        # Microphone / Audio Simulation Button (warm amber)
        mic_rect = pygame.Rect(W // 2 + 280, H // 2, 56, 56)
        draw_rounded_rect_with_shadow(surface, WARM_HEADER, mic_rect, radius=15, shadow_offset=(2, 3), border_width=3, border_color=WHITE)
        
        # Draw mic simple cartoon drawing inside button
        mx, my = mic_rect.center
        pygame.draw.rect(surface, CREAM_WHITE, (mx - 6, my - 14, 12, 22), border_radius=6)
        pygame.draw.arc(surface, CREAM_WHITE, (mx - 12, my - 6, 24, 16), math.pi, 2*math.pi, 3)
        pygame.draw.line(surface, CREAM_WHITE, (mx, my + 10), (mx, my + 17), 3)
        
        # GO Button (warm green)
        if len(self.input_text.strip()) > 0 and not self.submitted:
            go_w = 160
            go_h = 50
            go_x = W // 2 + 10
            go_y = H // 2 + 80
            go_rect = pygame.Rect(go_x, go_y, go_w, go_h)
            
            draw_rounded_rect_with_shadow(surface, WARM_GREEN, go_rect, radius=15, shadow_offset=(2, 3), border_width=3, border_color=WHITE)
            go_font = load_font(24, bold=True)
            draw_sticker_text(surface, "LET'S GO! 🚀", go_font, CREAM_WHITE, BLACK, go_rect.center, border_size=2)
            
        # Welcome Announcement Overlay
        if self.submitted:
            overlay_font = load_font(42, bold=True)
            draw_sticker_text(surface, f"WELCOME, {self.input_text.upper()}!", overlay_font, GOLD, (139, 69, 19), (W // 2, H // 2 + 150), border_size=4)
