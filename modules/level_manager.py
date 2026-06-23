import pygame
import math
import random
from game_core import (W, H, CREAM_WHITE, DEEP_SKY, GOLD, WHITE, BLACK, PURPLE, HOT_PINK,
                       SUNNY_YELLOW, RED, LIME_GREEN, SOFT_YELLOW, SOFT_PURPLE,
                       WARM_BG_TOP, WARM_BG_BOT, WARM_ACCENT, WARM_HEADER, WARM_CARD,
                       WARM_CORAL, WARM_GREEN, PEACH_SKIN,
                       load_font, draw_rounded_rect_with_shadow, draw_gradient_rect,
                       draw_sticker_text, MonkeyGuide, draw_vector_star, draw_vector_seed)
from systems.animation_engine import ParticleSystem, Easing

# Imports of game modules will be resolved dynamically to prevent circular imports
from games.drag_spell import DragSpellGame, PHONICS
from games.picture_choice import PictureChoiceGame
from games.matching_game import MatchingGame
from games.listening_game import ListeningGame
from games.speed_game import SpeedGame

# Mapping level indices to specific game mode handlers
GAME_HANDLERS = {
    0: DragSpellGame,     # Level 1: Animals -> Drag & Spell
    1: PictureChoiceGame, # Level 2: Food -> Picture Choice
    2: MatchingGame,      # Level 3: Objects -> Matching Cards
    3: ListeningGame,     # Level 4: Colors -> Audio Balloons
    4: MatchingGame,      # Level 5: Actions -> Matching Cards (Action Vocab)
    5: SpeedGame,         # Level 6: Space -> Speed Asteroids
    6: SpeedGame          # Level 7: Final -> Mixed Speed/Listening
}

class LevelManager:
    def __init__(self, level_idx, voice_system, audio_manager, progress_tracker, ai_engine):
        self.level_idx = level_idx
        self.voice = voice_system
        self.audio = audio_manager
        self.progress = progress_tracker
        self.ai = ai_engine
        
        # State can be: "tutorial", "playing", "celebrating"
        self.state = "tutorial"
        self.tutorial_time = 0.0
        
        # Celebration progress
        self.cel_time = 0.0
        self.banana_x = W - 150
        self.banana_y = 150
        self.banana_scale = 1.0
        self.banana_eaten = False
        self.evolve_message_shown = False
        self.monkey_evolved = False
        self.congrats_spoken = False
        
        # Guide Bird
        self.monkey = MonkeyGuide(W // 2, H // 2 + 10)
        self.monkey.stage = self.progress.data["monkey_stage"]
        self.monkey.expression = "neutral"
        
        # Particles
        self.particles = ParticleSystem()
        self.last_spoken_word = None
        
        # Audio
        theme_names = ["jungle", "food", "objects", "food", "jungle", "space", "space"]
        self.audio.play_music(theme_names[self.level_idx])
        
        # Spawn Game Mode Handler
        handler_cls = GAME_HANDLERS.get(self.level_idx, DragSpellGame)
        
        # Instantiate active game
        self.active_game = handler_cls(self.level_idx, self.voice, self.audio, self.progress, self.ai)
        
        # Initialize active game elements
        self.active_game.start_game()
        
        # Clear initial gameplay prompts and speak tutorial instructions
        self.voice.clear_queue()
        self.start_tutorial_speech()
        
        # Tutorial animation variables
        self.tut_step = "intro"
        self.tut_timer = 0.0
        self.pointer_pos = [W // 2, H // 2 + 150]
        self.pointer_target = [W // 2, H // 2]
        self.pointer_speed = 350.0
        self.grabbed_tile = None
        self.ripple_radius = 0.0
        self.ripple_active = False
        
        self.demo_target_found = False
        self.demo_tile = None
        self.demo_slot = None
        self.demo_button = None
        self.demo_card_pic = None
        self.demo_card_word = None
        self.demo_balloon = None
        self.demo_asteroid = None

    def start_tutorial_speech(self):
        nickname = self.progress.get_nickname()
        tut_texts = {
            0: f"Let's learn animal words, {nickname}! Look at the picture, drag letters to their boxes, and spell the word!",
            1: f"Let's learn food words, {nickname}! Look at the delicious drawing, listen to me ask: What is this?, and select the correct word!",
            2: f"Let's match some objects, {nickname}! Touch a picture card, then touch its name to match them together!",
            3: f"Let's play listening colors, {nickname}! Listen closely to the color, and tap the correct balloon before they float away!",
            4: f"Let's learn action words, {nickname}! Connect the action picture with the correct word card!",
            5: f"Speed Space Bonus, {nickname}! Tap the flying asteroid with the correct vocabulary word as fast as you can!",
            6: f"Final Ultimate Star challenge, {nickname}! Select the flying target asteroid correctly to win the Words Land Crown!"
        }
        self.voice.speak(tut_texts.get(self.level_idx, "Let's play and learn!"))

    def get_current_word(self):
        if not self.active_game:
            return None
        if hasattr(self.active_game, "word"):
            return self.active_game.word
        elif hasattr(self.active_game, "current_target_word"):
            return self.active_game.current_target_word
        elif hasattr(self.active_game, "target_color"):
            return self.active_game.target_color
        elif hasattr(self.active_game, "target_word"):
            return self.active_game.target_word
        return None

    def find_demo_targets(self):
        if self.level_idx == 0:
            if hasattr(self.active_game, "slots") and len(self.active_game.slots) > 0:
                self.demo_slot = self.active_game.slots[0]
                if hasattr(self.active_game, "tiles"):
                    self.demo_tile = next((t for t in self.active_game.tiles if t.char == self.demo_slot.char), None)
                    if self.demo_tile:
                        self.pointer_target = [self.demo_tile.x + self.demo_tile.size//2, self.demo_tile.y + self.demo_tile.size//2]
        elif self.level_idx == 1:
            if hasattr(self.active_game, "buttons") and len(self.active_game.buttons) > 0:
                self.demo_button = next((b for b in self.active_game.buttons if b.text == self.active_game.word), None)
                if self.demo_button:
                    self.pointer_target = [self.demo_button.rect.centerx, self.demo_button.rect.centery]
        elif self.level_idx == 2 or self.level_idx == 4:
            if hasattr(self.active_game, "cards") and len(self.active_game.cards) > 0:
                self.demo_card_pic = next((c for c in self.active_game.cards if c.card_type == "pic"), None)
                if self.demo_card_pic:
                    self.demo_card_word = next((c for c in self.active_game.cards if c.item_id == self.demo_card_pic.item_id and c.card_type == "word"), None)
                    self.pointer_target = [self.demo_card_pic.x, self.demo_card_pic.y]
        elif self.level_idx == 3:
            if hasattr(self.active_game, "balloons") and len(self.active_game.balloons) > 0:
                self.demo_balloon = next((b for b in self.active_game.balloons if b.color_name == self.active_game.target_color), None)
                if self.demo_balloon:
                    self.pointer_target = [self.demo_balloon.x, self.demo_balloon.y]
        elif self.level_idx == 5 or self.level_idx == 6:
            if hasattr(self.active_game, "asteroids") and len(self.active_game.asteroids) > 0:
                self.demo_asteroid = next((a for a in self.active_game.asteroids if a.text == self.active_game.target_word), None)
                if self.demo_asteroid:
                    self.pointer_target = [self.demo_asteroid.x, self.demo_asteroid.y]

    def handle_event(self, event):
        # Global top-right Quit button click detection
        if self.state in ["tutorial", "playing"]:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                quit_rect = pygame.Rect(W - 65, 30, 45, 40)
                if quit_rect.collidepoint(mx, my):
                    self.audio.play_sfx("click")
                    self.voice.clear_queue()
                    return "quit"

        if self.state == "tutorial":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                
                # Check Leave level button
                leave_rect = pygame.Rect(20, 30, 160, 40)
                if leave_rect.collidepoint(mx, my):
                    self.audio.play_sfx("click")
                    self.voice.clear_queue()
                    return "quit"
                    
                # Check Skip button
                skip_rect = pygame.Rect(W - 170, 30, 150, 40)
                if skip_rect.collidepoint(mx, my):
                    self.audio.play_sfx("click")
                    self.voice.clear_queue()
                    self.state = "playing"
                    self.active_game.start_game()
                    return None
                    
                # Check Start button (outro state only)
                if self.tut_step == "outro":
                    start_rect = pygame.Rect(W // 2 - 130, H // 2 - 30, 260, 65)
                    if start_rect.collidepoint(mx, my):
                        self.audio.play_sfx("click")
                        self.voice.clear_queue()
                        self.state = "playing"
                        self.active_game.start_game()
                        return None
                        
        elif self.state == "playing":
            # Intercept clicks on the Repeat Word button
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = pygame.mouse.get_pos()
                repeat_rect = pygame.Rect(W - 400, 30, 140, 40)
                if repeat_rect.collidepoint(mx, my):
                    self.audio.play_sfx("click")
                    word = self.get_current_word()
                    if word:
                        self.voice.clear_queue()
                        self.voice.speak(word)
                    return None
            
            # Pass events straight to active game
            result = self.active_game.handle_event(event)
            if result == "completed":
                self.start_celebration()
            elif result == "quit":
                return "quit"
                
        elif self.state == "celebrating":
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                if self.cel_time >= 2.5:
                    self.audio.play_sfx("click")
                    return "exit_level"
        return None

    def start_celebration(self):
        self.state = "celebrating"
        self.cel_time = 0.0
        self.monkey.expression = "happy"
        self.congrats_spoken = False
        
        # Award stars and bananas
        self.progress.add_stars(15)
        bananas_gained, evolved = self.progress.add_bananas(3)
        self.monkey_evolved = evolved
        
        # Mark level as complete
        self.progress.complete_level(self.level_idx)
        self.progress.unlock_next_level()
        
        # Success sound — personalized congratulation!
        nickname = self.progress.get_nickname()
        self.audio.play_sfx("success")
        if self.level_idx == 6:
            self.voice.speak(f"Congratulations {nickname}! You have completed the entire game of Words Land! You are now a Grand Champion explorer!")
        else:
            self.voice.speak(f"Congratulations {nickname}! You completed the level! Look, Tweety the Bird is dancing with joy!")

    def update(self, dt):
        self.particles.update(dt)
        self.monkey.update(dt)
        
        if self.state == "tutorial":
            self.tutorial_time += dt
            self.monkey.expression = "waving"
            
            # Animate pointer click ripple
            if self.ripple_active:
                self.ripple_radius += dt * 65.0
                if self.ripple_radius > 35.0:
                    self.ripple_active = False
            
            # Float physics updates for elements
            t_ticks = pygame.time.get_ticks() * 0.001
            if hasattr(self.active_game, "tiles"):
                for tile in self.active_game.tiles:
                    if tile != self.grabbed_tile:
                        tile.update(dt, t_ticks)
            if hasattr(self.active_game, "balloons"):
                for b in self.active_game.balloons:
                    b.update(dt)
            if hasattr(self.active_game, "asteroids"):
                for ast in self.active_game.asteroids:
                    ast.update(dt)
            if hasattr(self.active_game, "particles"):
                self.active_game.particles.update(dt)
                
            # Tutorial State machine
            self.tut_timer += dt
            
            if self.tut_step == "intro":
                if self.tut_timer >= 3.5:
                    self.tut_step = "moving_to_target"
                    self.tut_timer = 0.0
                    self.demo_target_found = False
                    
            elif self.tut_step == "moving_to_target":
                if not self.demo_target_found:
                    self.find_demo_targets()
                    self.demo_target_found = True
                    
                # Update floating targets coordinates dynamically
                if self.level_idx == 3 and self.demo_balloon:
                    self.pointer_target = [self.demo_balloon.x, self.demo_balloon.y]
                elif (self.level_idx == 5 or self.level_idx == 6) and self.demo_asteroid:
                    self.pointer_target = [self.demo_asteroid.x, self.demo_asteroid.y]
                    
                # Interpolate hand cursor movement
                dx = self.pointer_target[0] - self.pointer_pos[0]
                dy = self.pointer_target[1] - self.pointer_pos[1]
                dist = math.hypot(dx, dy)
                
                if dist > 8.0:
                    self.pointer_pos[0] += (dx / dist) * self.pointer_speed * dt
                    self.pointer_pos[1] += (dy / dist) * self.pointer_speed * dt
                else:
                    self.tut_step = "action"
                    self.tut_timer = 0.0
                    self.ripple_active = True
                    self.ripple_radius = 5.0
                    
            elif self.tut_step == "action":
                if self.level_idx == 0:
                    if self.demo_tile and self.demo_slot:
                        self.grabbed_tile = self.demo_tile
                        self.demo_tile.dragging = True
                        self.demo_tile.scale = 1.15
                        self.pointer_target = [self.demo_slot.cx, self.demo_slot.cy]
                        self.tut_step = "dragging"
                    else:
                        self.tut_step = "celebrating_demo"
                        
                elif self.level_idx == 1:
                    if self.demo_button:
                        self.active_game.trigger_word_win()
                        self.tut_step = "celebrating_demo"
                    else:
                        self.tut_step = "celebrating_demo"
                        
                elif self.level_idx == 2 or self.level_idx == 4:
                    if self.demo_card_pic and self.demo_card_word:
                        self.demo_card_pic.selected = True
                        self.active_game.selected_pic_card = self.demo_card_pic
                        self.voice.speak(self.demo_card_pic.text)
                        self.audio.play_sfx("click")
                        self.pointer_target = [self.demo_card_word.x, self.demo_card_word.y]
                        self.tut_step = "moving_to_word"
                    else:
                        self.tut_step = "celebrating_demo"
                        
                elif self.level_idx == 3:
                    if self.demo_balloon:
                        self.active_game.trigger_balloon_pop(self.demo_balloon)
                        self.tut_step = "celebrating_demo"
                    else:
                        self.tut_step = "celebrating_demo"
                        
                elif self.level_idx == 5 or self.level_idx == 6:
                    if self.demo_asteroid:
                        self.active_game.trigger_asteroid_pop(self.demo_asteroid)
                        self.tut_step = "celebrating_demo"
                    else:
                        self.tut_step = "celebrating_demo"
                        
            elif self.tut_step == "dragging":
                dx = self.pointer_target[0] - self.pointer_pos[0]
                dy = self.pointer_target[1] - self.pointer_pos[1]
                dist = math.hypot(dx, dy)
                
                if self.grabbed_tile:
                    self.grabbed_tile.x = self.pointer_pos[0] - self.grabbed_tile.size // 2
                    self.grabbed_tile.y = self.pointer_pos[1] - self.grabbed_tile.size // 2
                    
                if dist > 8.0:
                    self.pointer_pos[0] += (dx / dist) * self.pointer_speed * dt
                    self.pointer_pos[1] += (dy / dist) * self.pointer_speed * dt
                else:
                    if self.demo_slot and self.demo_tile:
                        self.demo_slot.filled = True
                        self.demo_tile.placed = True
                        self.demo_tile.dragging = False
                        self.audio.play_sfx("click")
                        pass
                        self.active_game.particles.spawn_burst(self.demo_slot.cx, self.demo_slot.cy, count=12, shape="star", colors=[GOLD, WHITE])
                        self.grabbed_tile = None
                        self.ripple_active = True
                        self.ripple_radius = 5.0
                        self.tut_step = "celebrating_demo"
                        self.tut_timer = 0.0
                        
            elif self.tut_step == "moving_to_word":
                dx = self.pointer_target[0] - self.pointer_pos[0]
                dy = self.pointer_target[1] - self.pointer_pos[1]
                dist = math.hypot(dx, dy)
                
                if dist > 8.0:
                    self.pointer_pos[0] += (dx / dist) * self.pointer_speed * dt
                    self.pointer_pos[1] += (dy / dist) * self.pointer_speed * dt
                else:
                    if self.demo_card_word:
                        self.demo_card_word.selected = True
                        self.active_game.selected_word_card = self.demo_card_word
                        self.active_game.check_match()
                        self.ripple_active = True
                        self.ripple_radius = 5.0
                        self.tut_step = "celebrating_demo"
                        self.tut_timer = 0.0
                        
            elif self.tut_step == "celebrating_demo":
                if self.tut_timer >= 2.2:
                    self.tut_step = "outro"
                    self.tut_timer = 0.0
                    nickname = self.progress.get_nickname()
                    self.voice.speak(f"Now it's your turn, {nickname}! Tap Start to play!")
                    
            elif self.tut_step == "outro":
                pass
                
        elif self.state == "playing":
            self.active_game.update(dt)
            # CRITICAL: Check if game completed after update
            result = self.active_game.check_completed()
            if result == "completed":
                self.start_celebration()
            else:
                # Detect and automatically speak new target word
                word = self.get_current_word()
                if word and word != self.last_spoken_word:
                    self.last_spoken_word = word
                    self.voice.speak(word)
                
        elif self.state == "celebrating":
            self.cel_time += dt
            
            # Simulated Banana flying to monkey mouth animation
            if self.cel_time <= 1.2:
                t = self.cel_time / 1.2
                self.banana_x = W - 150 - (W - 150 - W // 2) * t
                self.banana_y = 150 + (H // 2 - 20 - 150) * t
            elif not self.banana_eaten:
                self.banana_eaten = True
                self.monkey.expression = "eating"
                self.audio.play_sfx("banana")
                self.particles.spawn_burst(W // 2, H // 2 - 20, count=25, shape="star", colors=[GOLD, WHITE])
            
            if self.cel_time > 1.8:
                self.monkey.expression = "dancing"
                if self.monkey_evolved:
                    self.monkey.stage = self.progress.data["monkey_stage"]
                    if not self.evolve_message_shown:
                        self.evolve_message_shown = True
                        self.particles.spawn_burst(W // 2, H // 2 + 50, count=40, shape="confetti")
                        
            # Periodic confetti bursts
            if random.random() < 0.04:
                self.particles.spawn_burst(random.randint(100, W - 100), random.randint(100, H - 200), count=15, shape="confetti")

    def draw_tutorial_pointer(self, surface, x, y):
        # A cartoon cursor finger pointing up-left
        shadow_offset = (2, 3)
        # Shadow
        pygame.draw.circle(surface, (0, 0, 0, 50), (x + shadow_offset[0], y + shadow_offset[1]), 14)
        pygame.draw.rect(surface, (0, 0, 0, 50), (x - 8 + shadow_offset[0], y + shadow_offset[1], 16, 22), border_radius=4)
        pygame.draw.rect(surface, (0, 0, 0, 50), (x - 6 + shadow_offset[0], y - 20 + shadow_offset[1], 12, 22), border_radius=5)
        
        # Main body skin
        pygame.draw.circle(surface, PEACH_SKIN, (x, y), 14)
        pygame.draw.rect(surface, PEACH_SKIN, (x - 8, y, 16, 22), border_radius=4)
        pygame.draw.rect(surface, PEACH_SKIN, (x - 6, y - 20, 12, 22), border_radius=5)
        
        # Outline
        pygame.draw.circle(surface, WHITE, (x, y), 14, 2)
        pygame.draw.rect(surface, WHITE, (x - 8, y, 16, 22), 2, border_radius=4)
        pygame.draw.rect(surface, WHITE, (x - 6, y - 20, 12, 22), 2, border_radius=5)
        
        # Connect joint overlap
        pygame.draw.rect(surface, PEACH_SKIN, (x - 5, y - 3, 10, 8))

    def draw(self, surface):
        if self.state == "tutorial":
            # Render game base preview first
            self.active_game.draw(surface)
            
            # Subtle transparent dark overlay dimming the preview slightly
            overlay = pygame.Surface((W, H), pygame.SRCALPHA)
            overlay.fill((15, 15, 30, 80))
            surface.blit(overlay, (0, 0))
            
            # 1. Header Tutorial Info Card (Warm cream card - compact, no overlap)
            header_rect = pygame.Rect(W // 2 - 140, 15, 280, 50)
            draw_rounded_rect_with_shadow(surface, WARM_CARD, header_rect, radius=15, shadow_offset=(2, 3), border_width=3, border_color=WARM_ACCENT)
            
            # Header title
            header_font = load_font(18, bold=True)
            draw_sticker_text(surface, f"TUTORIAL: LEVEL {self.level_idx + 1}", header_font, GOLD, (139, 69, 19), (W // 2, 40), border_size=2)
            
            # 2. Waving Guide Bird (bottom left)
            self.monkey.x = 80
            self.monkey.y = H - 150
            self.monkey.draw(surface)
            
            # 2.5 Guide Bird Speech Bubble (displays text elegantly, wraps to prevent overlap)
            bubble_rect = pygame.Rect(180, H - 195, W - 260, 100)
            # Soft shadow
            shadow_rect = pygame.Rect(bubble_rect.x + 3, bubble_rect.y + 4, bubble_rect.w, bubble_rect.h)
            pygame.draw.rect(surface, (0, 0, 0, 50), shadow_rect, border_radius=15)
            # White body
            pygame.draw.rect(surface, CREAM_WHITE, bubble_rect, border_radius=15)
            pygame.draw.rect(surface, WARM_ACCENT, bubble_rect, 3, border_radius=15)
            
            # Pointer triangle pointing to monkey
            pointer_points = [(180, H - 145), (155, H - 150), (180, H - 155)]
            pygame.draw.polygon(surface, CREAM_WHITE, pointer_points)
            pygame.draw.polygon(surface, WARM_ACCENT, pointer_points, 2)
            # Clear border overlap inside the bubble
            pygame.draw.line(surface, CREAM_WHITE, (180, H - 147), (180, H - 153), 3)
            
            # Wrapped text rendering inside speech bubble
            inst_font = load_font(15, bold=True)
            inst_text = self.active_game.get_instruction_text()
            
            words = inst_text.split(' ')
            lines = []
            current_line = ""
            for word in words:
                test_line = current_line + " " + word if current_line else word
                if inst_font.size(test_line)[0] < bubble_rect.w - 30:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            if current_line:
                lines.append(current_line)
                
            total_h = len(lines) * inst_font.get_linesize()
            start_y = bubble_rect.centery - total_h // 2
            for idx, line in enumerate(lines):
                line_surf = inst_font.render(line, True, BLACK)
                surface.blit(line_surf, line_surf.get_rect(center=(bubble_rect.centerx, start_y + idx * inst_font.get_linesize() + inst_font.get_linesize() // 2)))
            
            # 3. Leave Level Button (top-left) - warm coral
            leave_rect = pygame.Rect(20, 30, 160, 40)
            draw_rounded_rect_with_shadow(surface, WARM_CORAL, leave_rect, radius=10, shadow_offset=(1, 2), border_width=2, border_color=WHITE)
            draw_sticker_text(surface, "🗺️ LEAVE LEVEL", load_font(18, bold=True), CREAM_WHITE, BLACK, leave_rect.center, border_size=2)
            
            # 4. Skip Tutorial Button (top-right) - warm orange/amber
            skip_rect = pygame.Rect(W - 170, 30, 150, 40)
            draw_rounded_rect_with_shadow(surface, WARM_ACCENT, skip_rect, radius=10, shadow_offset=(1, 2), border_width=2, border_color=WHITE)
            draw_sticker_text(surface, "SKIP DEMO ⏭", load_font(18, bold=True), CREAM_WHITE, BLACK, skip_rect.center, border_size=2)
            
            # 5. Outro Start Game Button (center of the screen, pulses with gold glow)
            if self.tut_step == "outro":
                pulse = 1.0 + math.sin(pygame.time.get_ticks() * 0.007) * 0.05
                btn_w = int(260 * pulse)
                btn_h = int(65 * pulse)
                start_rect = pygame.Rect(W // 2 - btn_w // 2, H // 2 - btn_h // 2, btn_w, btn_h)
                
                # Outer glow ring
                pygame.draw.rect(surface, GOLD, start_rect.inflate(10, 10), border_radius=22)
                draw_rounded_rect_with_shadow(surface, WARM_GREEN, start_rect, radius=18, shadow_offset=(2, 4), border_width=3, border_color=WHITE)
                
                start_font = load_font(25, bold=True)
                draw_sticker_text(surface, "START GAME! ▶", start_font, CREAM_WHITE, BLACK, start_rect.center, border_size=2)
                
            # 6. Click ripple feedback animation
            if self.ripple_active:
                r = int(self.ripple_radius)
                alpha = max(0, int(255 * (1.0 - r / 35.0)))
                ripple_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(ripple_surf, (255, 255, 100, alpha), (r, r), r, 3)
                surface.blit(ripple_surf, (int(self.pointer_pos[0] - r), int(self.pointer_pos[1] - r)))
                
            # 7. Virtual pointing hand pointer
            self.draw_tutorial_pointer(surface, int(self.pointer_pos[0]), int(self.pointer_pos[1]))
            
        elif self.state == "playing":
            self.active_game.draw(surface)
            
            # Render Repeat Word button
            repeat_rect = pygame.Rect(W - 400, 30, 140, 40)
            mx, my = pygame.mouse.get_pos()
            if repeat_rect.collidepoint(mx, my):
                repeat_rect = repeat_rect.inflate(6, 4)
                btn_color = WARM_ACCENT
            else:
                btn_color = WARM_HEADER
            draw_rounded_rect_with_shadow(surface, btn_color, repeat_rect, radius=10, shadow_offset=(1, 2), border_width=2, border_color=WHITE)
            draw_sticker_text(surface, "🔊 REPEAT", load_font(16, bold=True), CREAM_WHITE, BLACK, repeat_rect.center, border_size=2)
            
        # Draw global Quit button overlay for gameplay and tutorial screens
        if self.state in ["playing", "tutorial"]:
            mx, my = pygame.mouse.get_pos()
            quit_rect = pygame.Rect(W - 65, 30, 45, 40)
            if quit_rect.collidepoint(mx, my):
                quit_rect = quit_rect.inflate(6, 6)
                quit_color = (255, 100, 100) # light red hover
            else:
                quit_color = (235, 50, 50) # bold red
                
            draw_rounded_rect_with_shadow(surface, quit_color, quit_rect, radius=12, shadow_offset=(1, 2), border_width=2, border_color=WHITE)
            # Draw X character
            x_font = load_font(22, bold=True)
            draw_sticker_text(surface, "X", x_font, WHITE, BLACK, quit_rect.center, border_size=1)
            
        elif self.state == "celebrating":
            # Warm golden celebration background
            draw_gradient_rect(surface, WARM_BG_TOP, WARM_BG_BOT, (0, 0, W, H))
            self.particles.draw(surface)
            
            # Draw Bird guide centered
            self.monkey.x = W // 2
            self.monkey.y = H // 2 + 60
            self.monkey.draw(surface)
            
            # Draw flying banana
            if not self.banana_eaten:
                banana_w, banana_h = 60, 40
                banana_surf = pygame.Surface((banana_w, banana_h), pygame.SRCALPHA)
                pygame.draw.ellipse(banana_surf, GOLD, (0, 0, banana_w, banana_h))
                pygame.draw.ellipse(banana_surf, WARM_BG_TOP, (10, -5, banana_w - 15, banana_h))
                pygame.draw.circle(banana_surf, (100, 50, 10), (5, 12), 4)
                surface.blit(banana_surf, (int(self.banana_x - banana_w//2), int(self.banana_y - banana_h//2)))
                
            # Star / Banana rewards board (warm card)
            nickname = self.progress.get_nickname()
            reward_box = pygame.Rect(W // 2 - 260, H // 2 - 280, 520, 130)
            draw_rounded_rect_with_shadow(surface, WARM_CARD, reward_box, radius=20, shadow_offset=(3, 5), border_width=4, border_color=GOLD)
            
            rw_font = load_font(36, bold=True)
            draw_sticker_text(surface, f"GREAT JOB, {nickname.upper()}! 🎉", rw_font, GOLD, (139, 69, 19), (W // 2, H // 2 - 255), border_size=2)
            
            sub_rw_font = load_font(22, bold=True)
            if self.level_idx == 6:
                lbl_text = "Congratulations! You have finished the game!"
            else:
                lbl_text = "Level Completed!"
            sub_lbl = sub_rw_font.render(lbl_text, True, BLACK)
            surface.blit(sub_lbl, sub_lbl.get_rect(center=(W // 2, H // 2 - 215)))
            
            stats_text = "Earned:  +15 Stars        +3 Seeds"
            stats_lbl = sub_rw_font.render(stats_text, True, BLACK)
            lbl_rect = stats_lbl.get_rect(center=(W // 2, H // 2 - 185))
            surface.blit(stats_lbl, lbl_rect)
            
            # Measure widths dynamically to place vector star and seed beside the words
            w_stars = sub_rw_font.size("Earned:  +15 Stars ")[0]
            w_seeds = sub_rw_font.size("Earned:  +15 Stars        +3 Seeds ")[0]
            
            draw_vector_star(surface, (lbl_rect.x + w_stars + 8, H // 2 - 185), size=10, color=GOLD, border_color=(139, 69, 19))
            draw_vector_seed(surface, (lbl_rect.x + w_seeds + 8, H // 2 - 185), size=10)
            
            # Evolve Alert
            if self.monkey_evolved and self.cel_time >= 1.8:
                evolve_rect = pygame.Rect(W // 2 - 200, H // 2 - 130, 400, 42)
                draw_rounded_rect_with_shadow(surface, WARM_HEADER, evolve_rect, radius=8, shadow_offset=(2, 3), border_width=2, border_color=WHITE)
                font = load_font(18, bold=True)
                text_str = "TWEETY THE BIRD EVOLVED!"
                text_w = font.size(text_str)[0]
                draw_sticker_text(surface, text_str, font, CREAM_WHITE, BLACK, evolve_rect.center, border_size=2)
                draw_vector_star(surface, (evolve_rect.centerx - text_w // 2 - 20, evolve_rect.centery), size=10, color=GOLD, border_color=WHITE)
                draw_vector_star(surface, (evolve_rect.centerx + text_w // 2 + 20, evolve_rect.centery), size=10, color=GOLD, border_color=WHITE)
                
            # Floating Badge reward announcement if unlocked a new badge
            badge_map = {
                0: "Animal Master",
                1: "Food Expert",
                2: "Object Explorer",
                3: "Color Genius",
                4: "Action Hero",
                5: "Star Explorer",
                6: "Words Land Champion"
            }
            badge_name = badge_map.get(self.level_idx, "")
            badge_rect = pygame.Rect(W // 2 - 240, H // 2 + 190, 480, 50)
            draw_rounded_rect_with_shadow(surface, WARM_ACCENT, badge_rect, radius=15, shadow_offset=(2, 3), border_width=3, border_color=WHITE)
            draw_sticker_text(surface, f"UNLOCKED BADGE: {badge_name}", load_font(21, bold=True), CREAM_WHITE, BLACK, badge_rect.center, border_size=2)
            
            # Click hint at bottom
            if self.cel_time >= 2.5:
                click_lbl = load_font(19, bold=True).render("Click anywhere to return to map 🗺️", True, (139, 69, 19))
                surface.blit(click_lbl, click_lbl.get_rect(center=(W // 2, H - 40)))
