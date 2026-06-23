import pygame
import random
import math
from game_core import (W, H, CREAM_WHITE, WHITE, BLACK, GOLD, SUNNY_YELLOW, RED, DEEP_SKY, ORANGE, LIME_GREEN,
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
        
        # Guide bird instance
        self.bird = MonkeyGuide(220, H - 240)
        self.bird.expression = "neutral"
        self.bird.stage = 0 # Small bird
        
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
            mic_rect = pygame.Rect(390, 190, 56, 56)
            if mic_rect.collidepoint(mx, my):
                self.audio.play_sfx("click")
                # Simulate speech input by choosing a fun random kid explorer name
                self.input_text = random.choice(KID_EXPLORER_NAMES)
                self.voice.speak(f"Explorer name captured: {self.input_text}")
                
            # Check GO Button
            go_rect = pygame.Rect(60, 270, 220, 52)
            if go_rect.collidepoint(mx, my) and len(self.input_text.strip()) > 0:
                self.submit_name()

    def submit_name(self):
        self.submitted = True
        self.input_text = self.input_text.strip()
        self.progress.set_nickname(self.input_text)
        
        # Wave, confetti burst, welcome voice output
        self.bird.expression = "dancing"
        self.audio.play_sfx("success")
        self.particles.spawn_burst(W // 2, H // 2, count=60, shape="confetti")
        self.voice.speak(f"Hello {self.input_text}! Welcome to Words Land!")

    def update(self, dt):
        self.bird.update(dt)
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
        
        # Update bird position for drawing and draw it
        self.bird.x = 220
        self.bird.y = H - 210
        self.bird.draw(surface)
        
        # Draw Back Button (top-left) — warm coral
        if not self.submitted:
            back_rect = pygame.Rect(20, 20, 110, 45)
            draw_rounded_rect_with_shadow(surface, WARM_CORAL, back_rect, radius=10, shadow_offset=(1, 2), border_width=2, border_color=WHITE)
            draw_sticker_text(surface, "◀ BACK", load_font(18, bold=True), CREAM_WHITE, BLACK, back_rect.center, border_size=2)

        # Title (top-left)
        title_font = load_font(28, bold=True)
        draw_sticker_text(surface, "REGISTER EXPLORER PROFILE", title_font, GOLD, (139, 69, 19), (260, 110), border_size=2)
        
        # Left side panel for entry
        if not self.submitted:
            # Prompt label
            lbl_font = load_font(20, bold=True)
            lbl_surf = lbl_font.render("Enter your name to create your Explorer Passport:", True, (139, 69, 19))
            surface.blit(lbl_surf, (60, 155))
            
            # Input Box (warm white card)
            input_w = 310
            input_h = 56
            input_x = 60
            input_y = 190
            input_rect = pygame.Rect(input_x, input_y, input_w, input_h)
            
            draw_rounded_rect_with_shadow(surface, WHITE, input_rect, radius=15, shadow_offset=(2, 3))
            pygame.draw.rect(surface, WARM_ACCENT, input_rect, 3, border_radius=15)
            
            # Text input display
            input_font = load_font(28, bold=True)
            display_text = self.input_text
            # Blinking cursor
            if int(pygame.time.get_ticks() / 500) % 2 == 0:
                display_text += "|"
                
            txt_surf = input_font.render(display_text, True, BLACK)
            surface.blit(txt_surf, txt_surf.get_rect(midleft=(input_x + 15, input_y + input_h//2)))
            
            # Microphone / Audio Simulation Button (warm amber)
            mic_rect = pygame.Rect(390, 190, 56, 56)
            draw_rounded_rect_with_shadow(surface, WARM_HEADER, mic_rect, radius=15, shadow_offset=(2, 3), border_width=3, border_color=WHITE)
            
            # Draw mic simple cartoon drawing inside button
            mx, my = mic_rect.center
            pygame.draw.rect(surface, CREAM_WHITE, (mx - 6, my - 14, 12, 22), border_radius=6)
            pygame.draw.arc(surface, CREAM_WHITE, (mx - 12, my - 6, 24, 16), math.pi, 2*math.pi, 3)
            pygame.draw.line(surface, CREAM_WHITE, (mx, my + 10), (mx, my + 17), 3)
            
            # Info tip
            info_font = load_font(14, bold=True)
            info_surf = info_font.render("Type your name, or tap the microphone for a cool name!", True, BLACK)
            surface.blit(info_surf, (60, 252))
            
            # GO Button (warm green)
            if len(self.input_text.strip()) > 0:
                go_rect = pygame.Rect(60, 270, 220, 52)
                draw_rounded_rect_with_shadow(surface, WARM_GREEN, go_rect, radius=15, shadow_offset=(2, 3), border_width=3, border_color=WHITE)
                go_font = load_font(24, bold=True)
                draw_sticker_text(surface, "CREATE PASS! 🚀", go_font, CREAM_WHITE, BLACK, go_rect.center, border_size=2)
        else:
            # Welcome Message
            welcome_font = load_font(24, bold=True)
            welcome_lbl = welcome_font.render("Registration complete! Get ready to explore...", True, (139, 69, 19))
            surface.blit(welcome_lbl, (60, 200))
            
        # Guide Speech Bubble (displays text elegantly)
        bubble_rect = pygame.Rect(60, H - 150, 390, 90)
        draw_rounded_rect_with_shadow(surface, WARM_CARD, bubble_rect, radius=15, shadow_offset=(2, 3), border_width=2, border_color=WARM_HEADER)
        
        # Speech bubble pointer
        pygame.draw.polygon(surface, WARM_CARD, [(200, H - 150), (220, H - 165), (230, H - 150)])
        pygame.draw.polygon(surface, WARM_HEADER, [(200, H - 150), (220, H - 165), (230, H - 150)], 2)
        
        bubble_font = load_font(15, bold=True)
        if not self.submitted:
            msg1 = "Hello! I am Tweety the Bird!"
            msg2 = "Type your explorer name to fill out your passport!"
        else:
            msg1 = f"Welcome to Words Land, {self.input_text}!"
            msg2 = "Let's start our vocabulary adventure!"
            
        surface.blit(bubble_font.render(msg1, True, BLACK), (bubble_rect.x + 20, bubble_rect.y + 20))
        surface.blit(bubble_font.render(msg2, True, BLACK), (bubble_rect.x + 20, bubble_rect.y + 50))
        
        # --- EXPLORER PASSPORT CARD (RIGHT SIDE) ---
        passport_rect = pygame.Rect(510, 80, 440, 580)
        
        # Stitched passport folder border effect
        draw_rounded_rect_with_shadow(surface, (180, 110, 45), passport_rect, radius=25, shadow_offset=(4, 6), border_width=3, border_color=(120, 70, 25))
        
        # Inside page of passport
        page_rect = pygame.Rect(525, 95, 410, 550)
        draw_rounded_rect_with_shadow(surface, CREAM_WHITE, page_rect, radius=20, shadow_offset=(0, 0), border_width=2, border_color=(230, 220, 200))
        
        # Title of Passport
        pass_title_rect = pygame.Rect(545, 115, 370, 42)
        draw_rounded_rect_with_shadow(surface, DEEP_SKY, pass_title_rect, radius=10, shadow_offset=(1, 2), border_width=2, border_color=WHITE)
        draw_sticker_text(surface, "★ WORDS LAND EXPLORER PASS ★", load_font(18, bold=True), CREAM_WHITE, BLACK, pass_title_rect.center, border_size=2)
        
        # Polaroid Photo Frame (for Bird Avatar)
        photo_rect = pygame.Rect(630, 175, 200, 220)
        draw_rounded_rect_with_shadow(surface, WHITE, photo_rect, radius=8, shadow_offset=(2, 4), border_width=1, border_color=(200, 200, 200))
        
        # Draw Bird Avatar in Polaroid photo frame
        # Cache current pose, draw a centered version of the bird
        avatar_y = photo_rect.y + 100
        avatar_x = photo_rect.x + 100
        
        # Render a static clean bird in the photo
        orig_expr = self.bird.expression
        self.bird.expression = "happy" if not self.submitted else "dancing"
        
        # Temporarily move bird to polaroid, draw it, and restore
        old_x, old_y = self.bird.x, self.bird.y
        self.bird.x = avatar_x
        self.bird.y = avatar_y
        self.bird.draw(surface)
        
        self.bird.x = old_x
        self.bird.y = old_y
        self.bird.expression = orig_expr
        
        # Text label under photo frame
        photo_lbl_font = load_font(14, bold=True)
        photo_lbl = photo_lbl_font.render("OFFICIAL EXPLORER AVATAR", True, (139, 69, 19))
        surface.blit(photo_lbl, photo_lbl.get_rect(center=(photo_rect.centerx, photo_rect.bottom - 15)))
        
        # Passport Details Field labels and text
        details_font = load_font(18, bold=True)
        handwritten_font = load_font(22, bold=True)
        
        labels = [
            ("EXPLORER NAME:", self.input_text if self.input_text else "_________________"),
            ("EXPLORER RANK:", "Words Land Novice 🐦" if not self.submitted else "Official Explorer! 🎖️"),
            ("PASSPORT ID:", f"EXP-{2026 + len(self.input_text)}-WL" if self.input_text else "EXP-XXXX-WL"),
            ("STATUS:", "PENDING 🟡" if not self.submitted else "APPROVED ✅")
        ]
        
        for idx, (label_txt, value_txt) in enumerate(labels):
            ly = 415 + idx * 45
            # Label in clean brown
            lbl_surf = details_font.render(label_txt, True, (139, 69, 19))
            surface.blit(lbl_surf, (555, ly))
            
            # Value in distinct hand-written style blue/green
            val_color = DEEP_SKY if not self.submitted else LIME_GREEN
            if label_txt == "STATUS:" and self.submitted:
                val_color = LIME_GREEN
            elif label_txt == "STATUS:":
                val_color = ORANGE
                
            val_surf = handwritten_font.render(value_txt, True, val_color)
            surface.blit(val_surf, (715, ly - 3))
            
        # Draw dynamic Gold Star Approval stamp when completed!
        if self.submitted:
            stamp_cx = 850
            stamp_cy = 550
            # Draw decorative stamp shape
            stamp_radius = 50
            pygame.draw.circle(surface, GOLD, (stamp_cx, stamp_cy), stamp_radius)
            pygame.draw.circle(surface, (180, 140, 20), (stamp_cx, stamp_cy), stamp_radius, 3)
            
            # Stamp lines
            stamp_font = load_font(12, bold=True)
            stamp_text1 = stamp_font.render("WORDS LAND", True, (120, 90, 10))
            stamp_text2 = stamp_font.render("APPROVED", True, (120, 90, 10))
            surface.blit(stamp_text1, stamp_text1.get_rect(center=(stamp_cx, stamp_cy - 12)))
            surface.blit(stamp_text2, stamp_text2.get_rect(center=(stamp_cx, stamp_cy + 12)))
            
            # Tiny star in center
            star_font = load_font(18, bold=True)
            star_surf = star_font.render("★", True, (120, 90, 10))
            surface.blit(star_surf, star_surf.get_rect(center=(stamp_cx, stamp_cy)))
            
            # Welcome banner overlay
            overlay_font = load_font(42, bold=True)
            draw_sticker_text(surface, f"WELCOME, {self.input_text.upper()}!", overlay_font, GOLD, (139, 69, 19), (W // 2, H // 2 + 190), border_size=4)
