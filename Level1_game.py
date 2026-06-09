
import pygame
import pyttsx3
import random
import math
import threading
import sys
import time

# ── Init ────────────────────────────────────────────────────────────────────
pygame.init()
pygame.mixer.init()

W, H = 1024, 768
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Letter Land – Stage 1")
clock = pygame.time.Clock()

# ── Character Class ──────────────────────────────────────────────────────────
class Character:
    def __init__(self, name, emoji, color, voice_pitch=130):
        self.name = name
        self.emoji = emoji
        self.color = color
        self.voice_pitch = voice_pitch
        self.selected = False
        
    def draw(self, surf, x, y, size=120, selected=False):
        card_rect = pygame.Rect(x, y, size, size + 50)
        color = self.color if not selected else (255, 215, 0)
        pygame.draw.rect(surf, color, card_rect, border_radius=20)
        pygame.draw.rect(surf, (255,255,255), card_rect, 3, border_radius=20)
        
        font = pygame.font.Font(None, 70)
        try:
            emoji_text = font.render(self.emoji, True, (255,255,255))
        except:
            emoji_text = font.render("🐻", True, (255,255,255))
        surf.blit(emoji_text, emoji_text.get_rect(center=(x + size//2, y + size//2 - 20)))
        
        name_font = pygame.font.Font(None, 30)
        name_text = name_font.render(self.name, True, (255,255,255))
        surf.blit(name_text, name_text.get_rect(center=(x + size//2, y + size - 20)))
        
        if selected:
            star_font = pygame.font.Font(None, 40)
            star_text = star_font.render("⭐", True, (255, 255, 0))
            surf.blit(star_text, (x + size - 30, y - 10))

# ── TTS with character voice ─────────────────────────────────────────────────
tts_engine = pyttsx3.init()
_tts_lock = threading.Lock()
current_character = None

def speak(text, character=None):
    def _run():
        with _tts_lock:
            engine = pyttsx3.init()
            rate = 130
            if character:
                if character.name == "Benny the Bear":
                    rate = 100
                elif character.name == "Leo the Lion":
                    rate = 140
                elif character.name == "Tyler the Tiger":
                    rate = 150
                elif character.name == "Max the Monkey":
                    rate = 170
            engine.setProperty('rate', rate)
            engine.setProperty('volume', 1.0)
            engine.say(text)
            engine.runAndWait()
    threading.Thread(target=_run, daemon=True).start()

# ── Function to draw simple pictures for each word ──────────────────────────
def draw_simple_picture(word, center_x, center_y):
    if word == "CAT":
        pygame.draw.circle(screen, (255, 200, 150), (center_x, center_y), 70)
        pygame.draw.circle(screen, (200, 150, 100), (center_x, center_y), 70, 3)
        
        pygame.draw.polygon(screen, (255, 180, 130), 
                          [(center_x - 50, center_y - 40), (center_x - 25, center_y - 70), 
                           (center_x - 15, center_y - 35)])
        pygame.draw.polygon(screen, (255, 180, 130), 
                          [(center_x + 50, center_y - 40), (center_x + 25, center_y - 70), 
                           (center_x + 15, center_y - 35)])
        
        pygame.draw.circle(screen, (0, 0, 0), (center_x - 25, center_y - 15), 10)
        pygame.draw.circle(screen, (0, 0, 0), (center_x + 25, center_y - 15), 10)
        pygame.draw.circle(screen, (255, 255, 255), (center_x - 28, center_y - 18), 4)
        pygame.draw.circle(screen, (255, 255, 255), (center_x + 22, center_y - 18), 4)
        
        pygame.draw.polygon(screen, (255, 100, 100), 
                          [(center_x, center_y - 5), (center_x - 10, center_y + 8), 
                           (center_x + 10, center_y + 8)])
        
        pygame.draw.line(screen, (0, 0, 0), (center_x - 45, center_y), (center_x - 20, center_y), 2)
        pygame.draw.line(screen, (0, 0, 0), (center_x + 45, center_y), (center_x + 20, center_y), 2)

    elif word == "DOG":
        pygame.draw.circle(screen, (200, 170, 120), (center_x, center_y), 70)
        pygame.draw.circle(screen, (150, 120, 70), (center_x, center_y), 70, 3)
        
        pygame.draw.ellipse(screen, (150, 100, 50), 
                          (center_x - 70, center_y - 20, 35, 60))
        pygame.draw.ellipse(screen, (150, 100, 50), 
                          (center_x + 35, center_y - 20, 35, 60))
        
        pygame.draw.circle(screen, (0, 0, 0), (center_x - 25, center_y - 15), 10)
        pygame.draw.circle(screen, (0, 0, 0), (center_x + 25, center_y - 15), 10)
        pygame.draw.circle(screen, (255, 255, 255), (center_x - 28, center_y - 18), 4)
        pygame.draw.circle(screen, (255, 255, 255), (center_x + 22, center_y - 18), 4)
        
        pygame.draw.circle(screen, (0, 0, 0), (center_x, center_y + 5), 12)
        pygame.draw.ellipse(screen, (255, 100, 100), 
                          (center_x - 12, center_y + 15, 24, 25))

    elif word == "SUN":
        pygame.draw.circle(screen, (255, 255, 100), (center_x, center_y), 60)
        pygame.draw.circle(screen, (255, 200, 0), (center_x, center_y), 60, 4)
        
        for angle in range(0, 360, 30):
            rad = math.radians(angle)
            x1 = center_x + 75 * math.cos(rad)
            y1 = center_y + 75 * math.sin(rad)
            x2 = center_x + 100 * math.cos(rad)
            y2 = center_y + 100 * math.sin(rad)
            pygame.draw.line(screen, (255, 220, 0), (x1, y1), (x2, y2), 8)
        
        pygame.draw.circle(screen, (0, 0, 0), (center_x - 20, center_y - 15), 8)
        pygame.draw.circle(screen, (0, 0, 0), (center_x + 20, center_y - 15), 8)
        pygame.draw.arc(screen, (0, 0, 0), 
                       (center_x - 25, center_y - 5, 50, 30), 0, math.pi, 3)

    elif word == "HAT":
        pygame.draw.ellipse(screen, (100, 80, 180), 
                          (center_x - 70, center_y - 25, 140, 35))
        pygame.draw.rect(screen, (80, 60, 160), 
                        (center_x - 45, center_y - 90, 90, 70), border_radius=5)
        pygame.draw.rect(screen, (255, 100, 0), 
                        (center_x - 45, center_y - 45, 90, 12))

    elif word == "BUS":
        pygame.draw.rect(screen, (255, 200, 0), 
                        (center_x - 80, center_y - 40, 160, 80), border_radius=15)
        
        for i in range(4):
            pygame.draw.rect(screen, (100, 200, 255), 
                            (center_x - 65 + i * 40, center_y - 35, 30, 35), border_radius=5)
        
        pygame.draw.circle(screen, (50, 50, 50), (center_x - 50, center_y + 35), 18)
        pygame.draw.circle(screen, (50, 50, 50), (center_x + 50, center_y + 35), 18)

    elif word == "CUP":
        pygame.draw.rect(screen, (150, 200, 255), 
                        (center_x - 40, center_y - 50, 80, 85), border_radius=15)
        pygame.draw.arc(screen, (100, 150, 205), 
                       (center_x + 35, center_y - 40, 35, 60), 
                       -math.pi/3, math.pi/3, 10)

    elif word == "FAN":
        pygame.draw.circle(screen, (200, 200, 200), (center_x, center_y), 45)
        pygame.draw.circle(screen, (100, 100, 100), (center_x, center_y), 15)
        
        for i in range(4):
            angle = math.radians(i * 90 + 45)
            points = []
            for offset in [-15, 15]:
                rad = angle + math.radians(offset)
                x = center_x + 60 * math.cos(rad)
                y = center_y + 60 * math.sin(rad)
                points.append((x, y))
            points.append((center_x, center_y))
            pygame.draw.polygon(screen, (180, 180, 220), points)

    elif word == "MAP":
        pygame.draw.rect(screen, (220, 200, 140), 
                        (center_x - 65, center_y - 50, 130, 100), border_radius=5)
        
        pygame.draw.lines(screen, (100, 80, 40), False, 
                         [(center_x - 40, center_y - 30), (center_x - 10, center_y - 10),
                          (center_x + 20, center_y + 10), (center_x + 40, center_y + 30)], 4)
        
        pygame.draw.line(screen, (255, 50, 50), (center_x + 30, center_y + 20), 
                        (center_x + 50, center_y + 40), 5)
        pygame.draw.line(screen, (255, 50, 50), (center_x + 50, center_y + 20), 
                        (center_x + 30, center_y + 40), 5)

    elif word == "PIG":
        pygame.draw.circle(screen, (255, 200, 210), (center_x, center_y), 65)
        
        pygame.draw.polygon(screen, (255, 200, 210), 
                          [(center_x - 45, center_y - 40), (center_x - 60, center_y - 70), 
                           (center_x - 30, center_y - 55)])
        pygame.draw.polygon(screen, (255, 200, 210), 
                          [(center_x + 45, center_y - 40), (center_x + 60, center_y - 70), 
                           (center_x + 30, center_y - 55)])
        
        pygame.draw.circle(screen, (0, 0, 0), (center_x - 25, center_y - 20), 8)
        pygame.draw.circle(screen, (0, 0, 0), (center_x + 25, center_y - 20), 8)
        
        pygame.draw.ellipse(screen, (230, 150, 170), 
                          (center_x - 22, center_y - 5, 44, 35))

    elif word == "BOX":
        pygame.draw.rect(screen, (200, 100, 50), 
                        (center_x - 55, center_y - 45, 110, 90), border_radius=10)
        
        pygame.draw.rect(screen, (255, 50, 50), (center_x - 12, center_y - 45, 24, 90))
        pygame.draw.rect(screen, (255, 50, 50), (center_x - 55, center_y - 12, 110, 24))
        
        pygame.draw.polygon(screen, (255, 50, 50), 
                          [(center_x, center_y - 45), (center_x - 25, center_y - 65),
                           (center_x - 10, center_y - 45)])
        pygame.draw.polygon(screen, (255, 50, 50), 
                          [(center_x, center_y - 45), (center_x + 25, center_y - 65),
                           (center_x + 10, center_y - 45)])

# ── Character Selection Screen ───────────────────────────────────────────────
def show_character_selection():
    global current_character
    
    characters = [
        Character("Benny the Bear", "🐻", (139, 69, 19), 100),
        Character("Leo the Lion", "🦁", (255, 140, 0), 140),
        Character("Tyler the Tiger", "🐯", (255, 69, 0), 150),
        Character("Max the Monkey", "🐵", (160, 82, 45), 170)
    ]
    
    selected_index = 0
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    selected_index = (selected_index - 1) % 4
                elif event.key == pygame.K_RIGHT:
                    selected_index = (selected_index + 1) % 4
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    current_character = characters[selected_index]
                    speak(f"Hi! I'm {current_character.name}! Let's learn letters together!", current_character)
                    return
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                for i, char in enumerate(characters):
                    char_x = 150 + (i * 190)
                    char_rect = pygame.Rect(char_x, H//2 - 100, 120, 170)
                    if char_rect.collidepoint(mx, my):
                        selected_index = i
                        current_character = characters[selected_index]
                        speak(f"Hi! I'm {current_character.name}! Let's learn letters together!", current_character)
                        return
        
        screen.fill((100, 150, 200))
        
        title_font = pygame.font.Font(None, 80)
        title = title_font.render("Choose Your Friend!", True, (255, 215, 0))
        screen.blit(title, title.get_rect(center=(W//2, 100)))
        
        sub_font = pygame.font.Font(None, 40)
        subtitle = sub_font.render("Use LEFT/RIGHT arrows or click, then press ENTER", True, (255, 255, 255))
        screen.blit(subtitle, subtitle.get_rect(center=(W//2, 170)))
        
        for i, char in enumerate(characters):
            char.draw(screen, 150 + (i * 190), H//2 - 100, 120, i == selected_index)
        
        pygame.display.flip()
        clock.tick(60)

# ── Game Setup ──────────────────────────────────────────────────────────────
PHONICS = {
    'A': 'ay', 'B': 'buh', 'C': 'kuh', 'D': 'duh', 'E': 'eh',
    'F': 'fuh', 'G': 'guh', 'H': 'huh', 'I': 'ih', 'J': 'juh',
    'K': 'kuh', 'L': 'luh', 'M': 'muh', 'N': 'nuh', 'O': 'oh',
    'P': 'puh', 'Q': 'kwuh', 'R': 'ruh', 'S': 'suh', 'T': 'tuh',
    'U': 'uh', 'V': 'vuh', 'W': 'wuh', 'X': 'ks', 'Y': 'yuh', 'Z': 'zuh'
}

WORDS = [
    ("CAT", "A furry friend that says meow!"),
    ("DOG", "A loyal pet that says woof!"),
    ("SUN", "The bright star in the sky!"),
    ("HAT", "Something you wear on your head!"),
    ("BUS", "A big vehicle that takes you to school!"),
    ("CUP", "You drink water from this!"),
    ("FAN", "Makes you cool when it's hot!"),
    ("MAP", "Helps you find your way!"),
    ("PIG", "A pink farm animal that says oink!"),
    ("BOX", "You put things inside this!")
]

SLOT_EMPTY = (255, 235, 200)
SLOT_FILLED = (144, 238, 144)
SLOT_BORDER = (255, 140, 0)
TILE_COLS = [(255, 100, 100), (100, 200, 255), (100, 255, 100), (255, 200, 50), (255, 100, 200), (50, 200, 200)]

WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
PURPLE = (138, 43, 226)
GOLD = (255, 215, 0)

def load_font(size, bold=False):
    try:
        return pygame.font.SysFont('Comic Sans MS', size, bold=bold)
    except:
        return pygame.font.Font(None, size)

class LetterTile:
    SIZE = 80
    def __init__(self, letter, color):
        self.letter = letter
        self.color = color
        self.reset_float()
        self.dragging = False
        self.placed = False
        self.scale = 1.0
        self.bob_offset = random.uniform(0, math.pi * 2)
    
    def reset_float(self):
        margin = 60
        self.x = random.randint(margin, W - margin - self.SIZE)
        self.y = random.randint(int(H * 0.55), H - margin - self.SIZE)
        self.vx = random.uniform(-1.2, 1.2)
        self.vy = random.uniform(-0.8, 0.8)
    
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.SIZE, self.SIZE)
    
    def update(self, t):
        if self.placed or self.dragging:
            return
        self.x += self.vx
        self.y += self.vy + math.sin(t * 2 + self.bob_offset) * 0.4
        if self.x < 30: self.x = 30; self.vx = abs(self.vx)
        if self.x > W - 30 - self.SIZE: self.x = W - 30 - self.SIZE; self.vx = -abs(self.vx)
        if self.y < H * 0.52: self.y = H * 0.52; self.vy = abs(self.vy)
        if self.y > H - 30 - self.SIZE: self.y = H - 30 - self.SIZE; self.vy = -abs(self.vy)
    
    def draw(self, surf):
        if self.placed:
            return
        s = int(self.SIZE * self.scale)
        rx = int(self.x + (self.SIZE - s) / 2)
        ry = int(self.y + (self.SIZE - s) / 2)
        tile_rect = pygame.Rect(rx, ry, s, s)
        pygame.draw.rect(surf, self.color, tile_rect, border_radius=16)
        pygame.draw.rect(surf, WHITE, tile_rect, 3, border_radius=16)
        font = load_font(60, True)
        lbl = font.render(self.letter, True, WHITE)
        surf.blit(lbl, lbl.get_rect(center=tile_rect.center))

class Slot:
    SIZE = 86
    def __init__(self, letter, cx, cy):
        self.letter = letter
        self.cx = cx
        self.cy = cy
        self.filled = False
        self.flash = 0
    
    def rect(self):
        return pygame.Rect(self.cx - self.SIZE//2, self.cy - self.SIZE//2, self.SIZE, self.SIZE)
    
    def draw(self, surf):
        r = self.rect()
        if self.filled:
            color = SLOT_FILLED
            font = load_font(60, True)
            lbl = font.render(self.letter, True, (0, 100, 0))
        else:
            color = SLOT_EMPTY
            font = load_font(60, True)
            lbl = font.render(self.letter, True, (150, 150, 150))
        
        pygame.draw.rect(surf, color, r, border_radius=18)
        pygame.draw.rect(surf, SLOT_BORDER, r, 4, border_radius=18)
        surf.blit(lbl, lbl.get_rect(center=r.center))
        
        if self.flash > 0:
            flash_surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            flash_surf.fill((255, 255, 100, 100))
            surf.blit(flash_surf, r.topleft)
            self.flash -= 1

class Star:
    def __init__(self, cx, cy):
        self.x = cx + random.randint(-20, 20)
        self.y = cy + random.randint(-20, 20)
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-8, -2)
        self.life = random.randint(30, 60)
        self.color = random.choice([GOLD, (255, 100, 100), (100, 255, 100)])
        self.size = random.randint(5, 12)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3
        self.life -= 1
    
    def draw(self, surf):
        if self.life <= 0:
            return
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.size)

class ScoreBoard:
    def __init__(self):
        self.score = 0
    
    def add(self, pts=10):
        self.score += pts
    
    def draw(self, surf):
        panel = pygame.Rect(W - 200, 10, 180, 60)
        pygame.draw.rect(surf, (255, 255, 255, 200), panel, border_radius=15)
        pygame.draw.rect(surf, GOLD, panel, 3, border_radius=15)
        font = load_font(32, True)
        score_text = font.render(f"⭐ {self.score}", True, PURPLE)
        surf.blit(score_text, score_text.get_rect(center=panel.center))

# ── Main Game Functions ──────────────────────────────────────────────────────
def show_instructions():
    speak(f"Welcome to Letter Land, {current_character.name}! Let's learn to spell!", current_character)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                return
        
        screen.fill((100, 150, 200))
        
        title_font = load_font(80, True)
        title = title_font.render(f"Letter Land with {current_character.name}!", True, GOLD)
        screen.blit(title, title.get_rect(center=(W//2, 100)))
        
        box = pygame.Rect(W//2 - 300, 200, 600, 300)
        pygame.draw.rect(screen, WHITE, box, border_radius=30)
        pygame.draw.rect(screen, GOLD, box, 5, border_radius=30)
        
        instructions = [
            f"Hey! I'm {current_character.name}! 🎉",
            "",
            "1. Look at the picture",
            "2. Drag the floating letters",
            "3. Match them to the boxes!",
            "4. Spell the word to win!",
            "",
            "Click anywhere to start!"
        ]
        
        font = load_font(28)
        for i, line in enumerate(instructions):
            text = font.render(line, True, BLACK)
            screen.blit(text, text.get_rect(center=(W//2, 240 + i * 35)))
        
        pygame.display.flip()
        clock.tick(60)

def play_word(word, description, word_num, total_words, scoreboard):
    n = len(word)
    tiles = []
    letters_list = list(word)
    random.shuffle(letters_list)
    
    for i, letter in enumerate(letters_list):
        color = TILE_COLS[i % len(TILE_COLS)]
        tile = LetterTile(letter, color)
        tiles.append(tile)
    
    slot_spacing = 110
    total_slot_w = n * slot_spacing
    start_x = W//2 - total_slot_w//2 + slot_spacing//2
    slot_y = int(H * 0.35)
    slots = [Slot(word[i], start_x + i * slot_spacing, slot_y) for i in range(n)]
    
    dragging_tile = None
    drag_offset = (0, 0)
    stars = []
    celebration = False
    celebration_timer = 0
    word_completed = False
    t = 0
    
    speak(f"Can you spell {word}? {description}", current_character)
    
    while True:
        dt = clock.tick(60) / 1000.0
        t += dt
        mx, my = pygame.mouse.get_pos()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            
            if not celebration:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for tile in reversed(tiles):
                        if not tile.placed and tile.rect().collidepoint(mx, my):
                            dragging_tile = tile
                            tile.dragging = True
                            drag_offset = (mx - tile.x, my - tile.y)
                            tile.scale = 1.15
                            break
                
                if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if dragging_tile:
                        dragging_tile.dragging = False
                        dragging_tile.scale = 1.0
                        dropped = False
                        for slot in slots:
                            if not slot.filled and slot.letter == dragging_tile.letter and slot.rect().collidepoint(mx, my):
                                slot.filled = True
                                slot.flash = 15
                                dragging_tile.placed = True
                                dragging_tile.x = slot.cx - LetterTile.SIZE//2
                                dragging_tile.y = slot.cy - LetterTile.SIZE//2
                                speak(PHONICS.get(dragging_tile.letter, dragging_tile.letter), current_character)
                                dropped = True
                                stars.extend([Star(slot.cx, slot.cy) for _ in range(10)])
                                break
                        
                        if not dropped:
                            dragging_tile.reset_float()
                        dragging_tile = None
                        
                        if all(s.filled for s in slots) and not word_completed:
                            word_completed = True
                            celebration = True
                            scoreboard.add(10)
        
        if dragging_tile:
            dragging_tile.x = mx - drag_offset[0]
            dragging_tile.y = my - drag_offset[1]
        
        for tile in tiles:
            tile.update(t)
        
        stars = [s for s in stars if s.life > 0]
        for s in stars:
            s.update()
        
        if celebration:
            celebration_timer += dt
            if random.random() < 0.3:
                stars.append(Star(random.randint(100, W-100), random.randint(100, H-200)))
            if celebration_timer > 2.0:
                break
        
        # Draw everything
        screen.fill((100, 150, 200))
        
        # Draw character in corner
        if current_character:
            char_font = load_font(50)
            try:
                char_text = char_font.render(current_character.emoji, True, WHITE)
            except:
                char_text = char_font.render("🐻", True, WHITE)
            screen.blit(char_text, (20, H - 70))
            name_font = load_font(20)
            name_text = name_font.render(current_character.name, True, WHITE)
            screen.blit(name_text, (20, H - 40))
        
        # Progress
        progress_font = load_font(24)
        progress_text = progress_font.render(f"Word {word_num+1}/{total_words}", True, WHITE)
        screen.blit(progress_text, (30, 20))
        
        scoreboard.draw(screen)
        
        # Draw picture for the word
        draw_simple_picture(word, W//2, 140)
        
        # Word hint
        word_font = load_font(36, True)
        word_text = word_font.render(f"Spell: {word}", True, PURPLE)
        screen.blit(word_text, word_text.get_rect(center=(W//2, 220)))
        
        # Divider
        pygame.draw.line(screen, GOLD, (60, int(H*0.48)), (W-60, int(H*0.48)), 3)
        
        # Hint
        hint_font = load_font(24)
        hint_text = hint_font.render("Drag letters to the boxes!", True, (100, 100, 100))
        screen.blit(hint_text, hint_text.get_rect(center=(W//2, int(H*0.5) + 10)))
        
        for slot in slots:
            slot.draw(screen)
        
        for tile in tiles:
            tile.draw(screen)
        
        for star in stars:
            star.draw(screen)
        
        if celebration:
            banner = pygame.Rect(W//2 - 250, H//2 - 50, 500, 100)
            pygame.draw.rect(screen, GOLD, banner, border_radius=25)
            pygame.draw.rect(screen, PURPLE, banner, 5, border_radius=25)
            complete_font = load_font(50, True)
            complete_text = complete_font.render(f"⭐ {word}! ⭐", True, PURPLE)
            screen.blit(complete_text, complete_text.get_rect(center=banner.center))
        
        pygame.display.flip()
    
    return 'ok'

def run_stage1():
    scoreboard = ScoreBoard()
    word_order = list(range(len(WORDS)))
    random.shuffle(word_order)
    
    for word_num, wi in enumerate(word_order):
        word, description = WORDS[wi]
        result = play_word(word, description, word_num, len(WORDS), scoreboard)
        if result == 'quit':
            return
    
    # Stage complete celebration
    speak(f"Amazing! You finished Stage 1 with {scoreboard.score} points! You're a superstar, {current_character.name}!", current_character)
    
    waiting = True
    start_time = time.time()
    while waiting and time.time() - start_time < 5:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                waiting = False
        
        screen.fill((100, 150, 200))
        
        celebration_font = load_font(60, True)
        text = celebration_font.render(f"Congratulations {current_character.name}!", True, GOLD)
        screen.blit(text, text.get_rect(center=(W//2, H//2)))
        
        score_font = load_font(40, True)
        score_text = score_font.render(f"Score: {scoreboard.score} ⭐", True, WHITE)
        screen.blit(score_text, score_text.get_rect(center=(W//2, H//2 + 80)))
        
        again_font = load_font(30, True)
        again_text = again_font.render("Click anywhere to play again!", True, WHITE)
        screen.blit(again_text, again_text.get_rect(center=(W//2, H//2 + 160)))
        
        pygame.display.flip()
        clock.tick(30)

# ── Main ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    show_character_selection()
    while True:
        show_instructions()
        run_stage1()