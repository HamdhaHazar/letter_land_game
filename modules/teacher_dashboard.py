import pygame
from game_core import (W, H, CREAM_WHITE, JUNGLE_GREEN, DEEP_SKY, GOLD, WHITE, BLACK, PURPLE,
                       HOT_PINK, SUNNY_YELLOW, RED, LIME_GREEN,
                       WARM_BG_TOP, WARM_BG_BOT, WARM_ACCENT, WARM_HEADER, WARM_CARD,
                       WARM_CORAL, WARM_GREEN,
                       load_font, draw_rounded_rect_with_shadow, draw_gradient_rect, draw_sticker_text)

# Categorized words lists for matching tracker lookup
LEVEL_WORDS = {
    0: ["CAT", "DOG", "PIG", "FOX", "OWL", "HEN"],
    1: ["APPLE", "PEAR", "BANANA", "CAKE", "MILK", "EGG"],
    2: ["CAR", "BUS", "CUP", "HAT", "BOX", "BALL"],
    3: ["RED", "BLUE", "GREEN", "YELLOW", "PINK"],
    4: ["RUN", "JUMP", "FLY", "WALK", "SWIM"],
    5: ["STAR", "MOON", "ROCKET", "SUN", "UFO"]
}

class TeacherDashboard:
    def __init__(self, voice_system, audio_manager, progress_tracker):
        self.voice = voice_system
        self.audio = audio_manager
        self.progress = progress_tracker
        
        # Say greeting
        self.voice.speak("Welcome to the teacher dashboard! Let's check your progress.")

    def handle_click(self, pos):
        """Returns True if 'close' is clicked, otherwise None."""
        mx, my = pos
        # Close button rect
        close_rect = pygame.Rect(W // 2 - 100, H - 75, 200, 52)
        if close_rect.collidepoint(mx, my):
            self.audio.play_sfx("click")
            return True
        return False

    def draw(self, surface):
        # 1. Warm golden background
        draw_gradient_rect(surface, WARM_BG_TOP, WARM_BG_BOT, (0, 0, W, H))
        pygame.draw.rect(surface, (180, 120, 50), (0, 0, W, H), 16) # Warm wooden border
        
        # Pinned paper sheets
        paper_color = (255, 255, 245)
        # Left sheet: Stats & Graph
        sheet1 = pygame.Rect(40, 90, 450, 560)
        draw_rounded_rect_with_shadow(surface, paper_color, sheet1, radius=10, shadow_offset=(3, 5))
        pygame.draw.rect(surface, (210, 210, 200), sheet1, 2, border_radius=10)
        
        # Right sheet: Weak words & Badges
        sheet2 = pygame.Rect(530, 90, 450, 560)
        draw_rounded_rect_with_shadow(surface, paper_color, sheet2, radius=10, shadow_offset=(3, 5))
        pygame.draw.rect(surface, (210, 210, 200), sheet2, 2, border_radius=10)
        
        # Title Board (warm amber)
        title_rect = pygame.Rect(W//2 - 250, 20, 500, 60)
        draw_rounded_rect_with_shadow(surface, WARM_HEADER, title_rect, radius=15, shadow_offset=(2, 3), border_width=3, border_color=GOLD)
        draw_sticker_text(surface, "TEACHER DASHBOARD", load_font(28, bold=True), CREAM_WHITE, BLACK, title_rect.center, border_size=2)
        
        # --- LEFT SHEET CONTENT ---
        lbl_font = load_font(22, bold=True)
        body_font = load_font(18, bold=True)
        small_font = load_font(15, bold=True)
        
        # Title of Left sheet
        surface.blit(lbl_font.render("Learning Progress Report", True, PURPLE), (65, 110))
        pygame.draw.line(surface, DEEP_SKY, (65, 140), (460, 140), 2)
        
        # Stats summary block
        stats = [
            f"Explorer Name: {self.progress.get_nickname()}",
            f"Total Stars: {self.progress.data['stars']}",
            f"Total Bananas: {self.progress.data['bananas']}",
            f"Levels Completed: {len(self.progress.data['completed_levels'])} / 6"
        ]
        for idx, stat in enumerate(stats):
            surface.blit(body_font.render(stat, True, BLACK), (70, 155 + idx * 30))
            
        # Accuracy Graph / Bars
        graph_y = 310
        surface.blit(lbl_font.render("Level Accuracy rates", True, PURPLE), (65, graph_y))
        pygame.draw.line(surface, DEEP_SKY, (65, graph_y + 30), (460, graph_y + 30), 2)
        
        for i in range(6):
            # Get words for level
            words = LEVEL_WORDS[i]
            acc = self.progress.get_level_accuracy(words)
            
            lvl_lbl = f"Lvl {i+1}:"
            # Draw label
            surface.blit(small_font.render(lvl_lbl, True, BLACK), (70, graph_y + 50 + i * 42))
            
            # Draw bar background
            bar_w = 260
            bar_h = 16
            pygame.draw.rect(surface, (230, 230, 220), (130, graph_y + 52 + i * 42, bar_w, bar_h), border_radius=8)
            # Draw bar fill
            fill_w = int(bar_w * (acc / 100.0))
            bar_color = LIME_GREEN if acc >= 80 else (GOLD if acc >= 50 else RED)
            if fill_w > 0:
                pygame.draw.rect(surface, bar_color, (130, graph_y + 52 + i * 42, fill_w, bar_h), border_radius=8)
            pygame.draw.rect(surface, BLACK, (130, graph_y + 52 + i * 42, bar_w, bar_h), 1, border_radius=8)
            
            # Draw percentage text
            surface.blit(small_font.render(f"{acc}%", True, BLACK), (400, graph_y + 50 + i * 42))
            
        # --- RIGHT SHEET CONTENT ---
        # Title of Right sheet
        surface.blit(lbl_font.render("Struggling Vocabulary Words", True, PURPLE), (555, 110))
        pygame.draw.line(surface, DEEP_SKY, (555, 140), (950, 140), 2)
        
        weak_words = self.progress.get_weak_words(limit=5)
        if not weak_words:
            surface.blit(body_font.render("Great job! No weak words logged yet!", True, JUNGLE_GREEN), (565, 160))
        else:
            for idx, (word, count) in enumerate(weak_words):
                txt = f"{idx + 1}. {word}  -  {count} Mistakes"
                surface.blit(body_font.render(txt, True, RED), (565, 160 + idx * 30))
                
        # Strongest Category
        # Calculate errors per category
        cat_errors = {}
        for idx, name in enumerate(["Animals", "Food", "Objects", "Colors", "Actions", "Space"]):
            words = LEVEL_WORDS[idx]
            cat_errors[name] = sum(self.progress.data["mistakes_tracker"].get(w, 0) for w in words)
            
        # Select category with lowest errors that has actually been played
        played_categories = []
        for idx, name in enumerate(["Animals", "Food", "Objects", "Colors", "Actions", "Space"]):
            words = LEVEL_WORDS[idx]
            if any(w in self.progress.data["mistakes_tracker"] for w in words):
                played_categories.append(name)
                
        strongest = "None"
        if played_categories:
            strongest = min(played_categories, key=lambda c: cat_errors[c])
            
        surface.blit(lbl_font.render("Strongest Vocabulary Area", True, PURPLE), (555, 330))
        pygame.draw.line(surface, DEEP_SKY, (555, 360), (950, 360), 2)
        surface.blit(body_font.render(f"Category:  {strongest.upper()}", True, JUNGLE_GREEN), (565, 380))
        
        # Badges Unlocked Block
        surface.blit(lbl_font.render("Explorer Badges Unlocked", True, PURPLE), (555, 430))
        pygame.draw.line(surface, DEEP_SKY, (555, 460), (950, 460), 2)
        
        badges = self.progress.data.get("badges", [])
        if not badges:
            surface.blit(body_font.render("Complete levels to earn badges!", True, (130, 130, 130)), (565, 475))
        else:
            # Render badges
            for idx, badge in enumerate(badges[:4]):
                bx = 560 + (idx % 2) * 190
                by = 475 + (idx // 2) * 45
                draw_rounded_rect_with_shadow(surface, GOLD, (bx, by, 175, 36), radius=8, shadow_offset=(1, 2), border_width=2, border_color=WHITE)
                surface.blit(small_font.render(badge, True, BLACK), (bx + 10, by + 8))
                
        # Close / Return Button (warm coral)
        close_rect = pygame.Rect(W // 2 - 100, H - 75, 200, 52)
        draw_rounded_rect_with_shadow(surface, WARM_CORAL, close_rect, radius=15, shadow_offset=(2, 3), border_width=3, border_color=WHITE)
        draw_sticker_text(surface, "BACK TO MAP 🗺️", load_font(22, bold=True), CREAM_WHITE, BLACK, close_rect.center, border_size=2)
