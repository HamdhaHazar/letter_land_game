import pygame
import sys
import os
import time

# Ensure current directory is in system path for clean modular imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core settings & guide assets
from game_core import W, H, load_font, CREAM_WHITE, BLACK, WARM_BG_TOP, draw_rounded_rect_with_shadow
from systems.audio_manager import AudioManager
from systems.voice_system import VoiceSystem
from systems.progress_tracker import ProgressTracker
from systems.ai_adaptive_engine import AIAdaptiveEngine
from systems.animation_engine import ScreenTransition

# Import major navigation screens
from modules.intro_screen import IntroScreen
from modules.nickname_system import NicknameSystem
from modules.map_system import MapSystem
from modules.level_manager import LevelManager
from modules.teacher_dashboard import TeacherDashboard

def main():
    # 1. Initialize Pygame subsystems
    pygame.init()
    pygame.mixer.init()
    
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Words Land - The Great Vocabulary Adventure 🌟")
    clock = pygame.time.Clock()
    
    # 2. Initialize Core Systems
    audio = AudioManager()
    voice = VoiceSystem(audio)
    progress = ProgressTracker()
    ai = AIAdaptiveEngine(progress)
    transition = ScreenTransition()
    
    # Game states: "intro", "nickname", "map", "level", "dashboard"
    game_state = "intro"
    
    # Screen instances (lazy loaded/created as needed)
    intro_screen = IntroScreen(voice, audio)
    nickname_system = None
    map_system = None
    level_manager = None
    dashboard_screen = None
    
    # Transition targets
    next_state = None
    
    # Text wrapping/subtitle font
    subtitle_font = load_font(21, bold=True)
    
    # 3. Main Event and Rendering loop
    running = True
    while running:
        dt = clock.tick(60) / 1000.0 # 60 FPS Cap
        mouse_pos = pygame.mouse.get_pos()
        
        # --- Handle Pygame Global Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
                
            # Intercept events if transitioning
            if transition.transitioning:
                continue
                
            # Dispatch events to active state modules
            if game_state == "intro":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    # Renders button rect
                    btn_rect = intro_screen.run_frame(screen, 0, mouse_pos)
                    if btn_rect.collidepoint(event.pos):
                        audio.play_sfx("click")
                        next_state = "nickname"
                        transition.start_fade_out()
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    audio.play_sfx("click")
                    next_state = "nickname"
                    transition.start_fade_out()
                    
            elif game_state == "nickname":
                if nickname_system:
                    result = nickname_system.handle_event(event)
                    if result == "back":
                        next_state = "intro"
                        transition.start_fade_out()
                    
            elif game_state == "map":
                if map_system:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        action = map_system.handle_click(event.pos)
                        if action == "dashboard":
                            next_state = "dashboard"
                            transition.start_fade_out()
                        elif action == "back":
                            next_state = "nickname"
                            transition.start_fade_out()
                        elif isinstance(action, int):
                            # Selected a level index
                            level_idx = action
                            next_state = f"level_{level_idx}"
                            transition.start_fade_out()
                            
            elif game_state == "level":
                if level_manager:
                    result = level_manager.handle_event(event)
                    if result == "quit" or result == "exit_level":
                        next_state = "map"
                        transition.start_fade_out()
                        
            elif game_state == "dashboard":
                if dashboard_screen:
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        if dashboard_screen.handle_click(event.pos):
                            next_state = "map"
                            transition.start_fade_out()

        if not running:
            break

        # --- Update States ---
        voice.update(dt)
        
        if not transition.transitioning:
            if game_state == "intro":
                pass
            elif game_state == "nickname":
                if nickname_system:
                    completed = nickname_system.update(dt)
                    if completed:
                        next_state = "map"
                        transition.start_fade_out()
            elif game_state == "map":
                if map_system:
                    map_system.update(dt)
            elif game_state == "level":
                if level_manager:
                    level_manager.update(dt)
            elif game_state == "dashboard":
                pass

        # --- Draw Screens ---
        if game_state == "intro":
            intro_screen.run_frame(screen, dt, mouse_pos)
        elif game_state == "nickname":
            if nickname_system:
                nickname_system.draw(screen, dt)
        elif game_state == "map":
            if map_system:
                map_system.draw(screen)
        elif game_state == "level":
            if level_manager:
                level_manager.draw(screen)
        elif game_state == "dashboard":
            if dashboard_screen:
                dashboard_screen.draw(screen)

        # Draw Global subtitles for accessibility narration
        voice.draw_subtitles(screen, subtitle_font, W, H)
        
        # --- Handle Screen Transitions (Fades) ---
        if transition.transitioning:
            completed = transition.update(dt)
            transition.draw(screen, W, H)
            
            if completed:
                if next_state is not None:
                    # Execute state change once faded out
                    if next_state == "intro":
                        audio.play_music("intro")
                        intro_screen = IntroScreen(voice, audio)
                        game_state = "intro"
                    elif next_state == "nickname":
                        nickname_system = NicknameSystem(voice, audio, progress)
                        game_state = "nickname"
                    elif next_state == "map":
                        audio.play_music("intro")
                        map_system = MapSystem(voice, audio, progress)
                        game_state = "map"
                    elif next_state == "dashboard":
                        dashboard_screen = TeacherDashboard(voice, audio, progress)
                        game_state = "dashboard"
                    elif next_state.startswith("level_"):
                        level_idx = int(next_state.split("_")[1])
                        level_manager = LevelManager(level_idx, voice, audio, progress, ai)
                        game_state = "level"
                        
                    transition.start_fade_in()
                    next_state = None

        pygame.display.flip()

    # 4. Clean shutdown of speech thread
    voice.stop()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
