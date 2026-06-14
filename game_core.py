import pygame
import math
import random
import sys

# Screen Settings
W, H = 1024, 768

# Colors Palette (Warm Yellow Kids Theme)
SKY_BLUE = (176, 224, 230)
DEEP_SKY = (30, 144, 255)
JUNGLE_GREEN = (34, 139, 34)
SUNNY_YELLOW = (255, 223, 0)
SOFT_YELLOW = (255, 239, 150)
CREAM_WHITE = (255, 253, 240)
BROWN = (139, 69, 19)
PEACH_BROWN = (210, 105, 30)
PEACH_SKIN = (255, 218, 185)
PURPLE = (138, 43, 226)
SOFT_PURPLE = (230, 210, 250)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GOLD = (255, 215, 0)
SHADOW_COLOR = (15, 30, 45, 80)
RED = (255, 69, 0)
ORANGE = (255, 140, 0)
LIME_GREEN = (50, 205, 50)
HOT_PINK = (255, 105, 180)

# Warm Yellow Theme Colors
WARM_BG_TOP = (255, 243, 176)      # Light warm yellow
WARM_BG_BOT = (255, 220, 100)      # Deeper golden yellow
WARM_CARD = (255, 250, 230)        # Warm cream for cards
WARM_ACCENT = (255, 183, 77)       # Amber accent
WARM_HEADER = (255, 167, 38)       # Deep amber for headers
WARM_GREEN = (129, 199, 132)       # Soft mint green
WARM_CORAL = (255, 138, 101)       # Soft coral button
WARM_PEACH = (255, 224, 178)       # Peach background

# Init Fonts
pygame.font.init()
def load_font(size, bold=False):
    try:
        return pygame.font.SysFont('Comic Sans MS', size, bold=bold)
    except:
        return pygame.font.Font(None, size)

# --- Visual Drawing Helpers ---
def draw_rounded_rect_with_shadow(surface, color, rect, radius=20, shadow_offset=(4, 6), border_width=0, border_color=WHITE, thickness=6):
    """Draws a premium 3D styled rounded rectangle with layered drop shadow and bevel depth."""
    rect = pygame.Rect(rect)
    
    # 1. Layered soft shadow
    for i in range(3):
        so_x = shadow_offset[0] + i * 2
        so_y = shadow_offset[1] + i * 2
        shadow_rect = pygame.Rect(rect.x + so_x, rect.y + so_y, rect.w, rect.h)
        shadow_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        alpha = max(10, 45 - i * 12)
        pygame.draw.rect(shadow_surf, (0, 0, 0, alpha), (0, 0, rect.w, rect.h), border_radius=radius)
        surface.blit(shadow_surf, shadow_rect.topleft)
        
    # 2. 3D extrusion/thickness bottom layer (slightly darker shade of base color)
    if thickness > 0:
        r, g, b = color[:3]
        darker_color = (max(0, int(r * 0.72)), max(0, int(g * 0.72)), max(0, int(b * 0.72)))
        thick_rect = pygame.Rect(rect.x, rect.y + thickness, rect.w, rect.h)
        pygame.draw.rect(surface, darker_color, thick_rect, border_radius=radius)
        
    # 3. Main face box
    pygame.draw.rect(surface, color, rect, border_radius=radius)
    
    # 4. Glossy specular shine on top
    if rect.h > 10 and rect.w > 10:
        shine_surf = pygame.Surface((rect.w, rect.h // 2), pygame.SRCALPHA)
        pygame.draw.rect(shine_surf, (255, 255, 255, 40), (0, 0, rect.w, rect.h // 2), 
                         border_bottom_left_radius=0, border_bottom_right_radius=0, 
                         border_top_left_radius=radius, border_top_right_radius=radius)
        surface.blit(shine_surf, rect.topleft)
    
    # 5. Outer border sticker style
    if border_width > 0:
        pygame.draw.rect(surface, border_color, rect, border_width, border_radius=radius)

def draw_rainbow(surface, cx, cy, start_radius=320, width=12):
    """Draws a beautiful translucent rainbow arching over the landscape."""
    rainbow_colors = [
        (255, 60, 60, 60),      # Red
        (255, 140, 0, 65),     # Orange
        (255, 220, 40, 70),     # Yellow
        (60, 220, 60, 65),      # Green
        (60, 140, 255, 60),     # Blue
        (100, 60, 255, 55),     # Indigo
        (180, 60, 255, 50)      # Violet
    ]
    rainbow_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    for idx, col in enumerate(rainbow_colors):
        r = start_radius + idx * width
        rect = pygame.Rect(cx - r, cy - r, r * 2, r * 2)
        pygame.draw.arc(rainbow_surf, col, rect, 0, math.pi, width + 1)
    surface.blit(rainbow_surf, (0, 0))

def draw_gradient_rect(surface, color1, color2, rect, radius=0):
    """Draws a vertical linear gradient inside a rect."""
    rect = pygame.Rect(rect)
    grad_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    for y in range(rect.h):
        t = y / float(rect.h - 1) if rect.h > 1 else 0
        r = int(color1[0] * (1 - t) + color2[0] * t)
        g = int(color1[1] * (1 - t) + color2[1] * t)
        b = int(color1[2] * (1 - t) + color2[2] * t)
        a = 255
        if len(color1) == 4 and len(color2) == 4:
            a = int(color1[3] * (1 - t) + color2[3] * t)
        pygame.draw.line(grad_surf, (r, g, b, a), (0, y), (rect.w, y))
    
    if radius > 0:
        # Mask to rounded rect
        mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.w, rect.h), border_radius=radius)
        grad_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    
    surface.blit(grad_surf, rect.topleft)

def draw_sticker_text(surface, text, font, text_color, bg_color, center_pos, border_size=4):
    """Draws bubble/sticker style text with a thick border around it."""
    lbl_bg = font.render(text, True, bg_color)
    lbl_fg = font.render(text, True, text_color)
    cx, cy = center_pos
    
    # Draw outline in 8 directions
    for dx in range(-border_size, border_size + 1):
        for dy in range(-border_size, border_size + 1):
            if dx*dx + dy*dy <= border_size*border_size:
                surface.blit(lbl_bg, lbl_bg.get_rect(center=(cx + dx, cy + dy)))
    
    # Draw foreground
    surface.blit(lbl_fg, lbl_fg.get_rect(center=(cx, cy)))

def draw_glow_circle(surface, color, center, radius, glow_width=8):
    """Draws a glowing light effect around a circle."""
    cx, cy = center
    for r in range(radius, radius + glow_width):
        alpha = int(100 * (1.0 - (r - radius) / float(glow_width)))
        glow_color = (color[0], color[1], color[2], alpha)
        glow_surf = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, glow_color, (r, r), r, 2)
        surface.blit(glow_surf, (cx - r, cy - r))

# --- Programmatic Cartoon Drawing Engine for Vocabulary Words ---
def draw_vocabulary_picture(surface, word, cx, cy, radius=65):
    """Draws a programmatically generated, beautiful cartoon picture of a vocabulary word."""
    # Draw background circular placard
    draw_rounded_rect_with_shadow(surface, CREAM_WHITE, (cx - radius, cy - radius, radius*2, radius*2), radius=30, shadow_offset=(3, 5), border_width=4, border_color=GOLD)
    
    # 3D gloss diagonal sheen
    sheen_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.polygon(sheen_surf, (255, 255, 255, 30), [(0, 0), (radius * 2, 0), (0, radius * 2)])
    mask = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, radius * 2, radius * 2), border_radius=30)
    sheen_surf.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surface.blit(sheen_surf, (cx - radius, cy - radius))
    
    word = word.upper()
    
    if word == "CAT":
        # Head
        pygame.draw.circle(surface, (255, 204, 153), (cx, cy + 10), 45)
        # Ears
        pygame.draw.polygon(surface, (255, 178, 102), [(cx - 35, cy - 20), (cx - 40, cy - 45), (cx - 15, cy - 25)])
        pygame.draw.polygon(surface, (255, 178, 102), [(cx + 35, cy - 20), (cx + 40, cy - 45), (cx + 15, cy - 25)])
        # Eyes
        pygame.draw.circle(surface, BLACK, (cx - 15, cy + 5), 8)
        pygame.draw.circle(surface, BLACK, (cx + 15, cy + 5), 8)
        pygame.draw.circle(surface, WHITE, (cx - 17, cy + 3), 3)
        pygame.draw.circle(surface, WHITE, (cx + 13, cy + 3), 3)
        # Nose
        pygame.draw.polygon(surface, (255, 102, 102), [(cx, cy + 18), (cx - 6, cy + 12), (cx + 6, cy + 12)])
        # Mouth
        pygame.draw.arc(surface, BLACK, (cx - 12, cy + 16, 12, 10), math.pi, 2*math.pi, 2)
        pygame.draw.arc(surface, BLACK, (cx, cy + 16, 12, 10), math.pi, 2*math.pi, 2)
        # Whiskers
        pygame.draw.line(surface, BLACK, (cx - 30, cy + 12), (cx - 50, cy + 10), 2)
        pygame.draw.line(surface, BLACK, (cx - 30, cy + 18), (cx - 52, cy + 20), 2)
        pygame.draw.line(surface, BLACK, (cx + 30, cy + 12), (cx + 50, cy + 10), 2)
        pygame.draw.line(surface, BLACK, (cx + 30, cy + 18), (cx + 52, cy + 20), 2)

    elif word == "DOG":
        # Head
        pygame.draw.circle(surface, (210, 180, 140), (cx, cy + 10), 45)
        # Ears
        pygame.draw.ellipse(surface, (165, 42, 42), (cx - 48, cy - 15, 20, 45))
        pygame.draw.ellipse(surface, (165, 42, 42), (cx + 28, cy - 15, 20, 45))
        # Eyes
        pygame.draw.circle(surface, BLACK, (cx - 15, cy + 5), 8)
        pygame.draw.circle(surface, BLACK, (cx + 15, cy + 5), 8)
        pygame.draw.circle(surface, WHITE, (cx - 17, cy + 3), 3)
        pygame.draw.circle(surface, WHITE, (cx + 13, cy + 3), 3)
        # Nose Snout
        pygame.draw.ellipse(surface, (245, 222, 179), (cx - 18, cy + 12, 36, 22))
        pygame.draw.circle(surface, BLACK, (cx, cy + 16), 7)
        # Tongue
        pygame.draw.ellipse(surface, (255, 102, 102), (cx - 6, cy + 28, 12, 16))

    elif word == "PIG":
        # Face
        pygame.draw.circle(surface, (255, 192, 203), (cx, cy + 10), 45)
        # Ears
        pygame.draw.polygon(surface, (255, 150, 170), [(cx - 35, cy - 22), (cx - 45, cy - 42), (cx - 15, cy - 35)])
        pygame.draw.polygon(surface, (255, 150, 170), [(cx + 35, cy - 22), (cx + 45, cy - 42), (cx + 15, cy - 35)])
        # Eyes
        pygame.draw.circle(surface, BLACK, (cx - 16, cy + 5), 7)
        pygame.draw.circle(surface, BLACK, (cx + 16, cy + 5), 7)
        pygame.draw.circle(surface, WHITE, (cx - 18, cy + 3), 2)
        pygame.draw.circle(surface, WHITE, (cx + 14, cy + 3), 2)
        # Snout
        pygame.draw.ellipse(surface, (255, 130, 150), (cx - 18, cy + 12, 36, 26))
        pygame.draw.circle(surface, (150, 50, 70), (cx - 6, cy + 25), 4)
        pygame.draw.circle(surface, (150, 50, 70), (cx + 6, cy + 25), 4)

    elif word == "FOX":
        # Main Head (Orange)
        pygame.draw.circle(surface, ORANGE, (cx, cy + 10), 45)
        # Cheeks (White patches)
        pygame.draw.circle(surface, WHITE, (cx - 25, cy + 25), 20)
        pygame.draw.circle(surface, WHITE, (cx + 25, cy + 25), 20)
        # Redraw top to cover white overlay overlap
        pygame.draw.ellipse(surface, ORANGE, (cx - 30, cy - 5, 60, 40))
        # Ears
        pygame.draw.polygon(surface, (139, 69, 19), [(cx - 40, cy - 15), (cx - 45, cy - 45), (cx - 15, cy - 25)])
        pygame.draw.polygon(surface, (139, 69, 19), [(cx + 40, cy - 15), (cx + 45, cy - 45), (cx + 15, cy - 25)])
        pygame.draw.polygon(surface, PEACH_SKIN, [(cx - 33, cy - 18), (cx - 38, cy - 38), (cx - 18, cy - 24)])
        pygame.draw.polygon(surface, PEACH_SKIN, [(cx + 33, cy - 18), (cx + 38, cy - 38), (cx + 18, cy - 24)])
        # Eyes
        pygame.draw.circle(surface, BLACK, (cx - 14, cy + 5), 8)
        pygame.draw.circle(surface, BLACK, (cx + 14, cy + 5), 8)
        pygame.draw.circle(surface, WHITE, (cx - 16, cy + 3), 3)
        pygame.draw.circle(surface, WHITE, (cx + 12, cy + 3), 3)
        # Snout / Nose
        pygame.draw.polygon(surface, ORANGE, [(cx - 12, cy + 12), (cx + 12, cy + 12), (cx, cy + 28)])
        pygame.draw.circle(surface, BLACK, (cx, cy + 26), 6)

    elif word == "OWL":
        # Body
        pygame.draw.ellipse(surface, (139, 69, 19), (cx - 35, cy - 25, 70, 80))
        # Chest patch
        pygame.draw.ellipse(surface, PEACH_SKIN, (cx - 22, cy - 5, 44, 50))
        # Eye Rings
        pygame.draw.circle(surface, GOLD, (cx - 18, cy - 5), 18)
        pygame.draw.circle(surface, GOLD, (cx + 18, cy - 5), 18)
        # Eyes
        pygame.draw.circle(surface, BLACK, (cx - 18, cy - 5), 10)
        pygame.draw.circle(surface, BLACK, (cx + 18, cy - 5), 10)
        pygame.draw.circle(surface, WHITE, (cx - 20, cy - 7), 3)
        pygame.draw.circle(surface, WHITE, (cx + 16, cy - 7), 3)
        # Beak
        pygame.draw.polygon(surface, ORANGE, [(cx - 5, cy + 8), (cx + 5, cy + 8), (cx, cy + 20)])
        # Wings
        pygame.draw.ellipse(surface, (100, 50, 10), (cx - 45, cy - 10, 16, 45))
        pygame.draw.ellipse(surface, (100, 50, 10), (cx + 29, cy - 10, 16, 45))

    elif word == "HEN":
        # Body
        pygame.draw.circle(surface, (240, 240, 240), (cx - 10, cy + 15), 38)
        # Head
        pygame.draw.circle(surface, (240, 240, 240), (cx + 15, cy - 10), 25)
        # Neck connection
        pygame.draw.polygon(surface, (240, 240, 240), [(cx - 15, cy + 5), (cx + 15, cy - 20), (cx + 5, cy + 25)])
        # Comb (Red crown)
        pygame.draw.circle(surface, RED, (cx + 10, cy - 32), 7)
        pygame.draw.circle(surface, RED, (cx + 18, cy - 35), 7)
        pygame.draw.circle(surface, RED, (cx + 26, cy - 31), 7)
        # Beak
        pygame.draw.polygon(surface, GOLD, [(cx + 28, cy - 15), (cx + 38, cy - 10), (cx + 28, cy - 7)])
        # Eye
        pygame.draw.circle(surface, BLACK, (cx + 14, cy - 14), 4)
        # Wing
        pygame.draw.ellipse(surface, (255, 255, 255), (cx - 28, cy + 5, 30, 20))
        # Tail feathers
        pygame.draw.polygon(surface, RED, [(cx - 40, cy + 10), (cx - 55, cy - 5), (cx - 35, cy + 25)])

    elif word == "APPLE":
        # Stem
        pygame.draw.rect(surface, BROWN, (cx - 3, cy - 45, 6, 25))
        # Leaf
        pygame.draw.ellipse(surface, LIME_GREEN, (cx, cy - 45, 25, 12))
        # Apple Body (double overlapping circles for cute indent)
        pygame.draw.circle(surface, RED, (cx - 20, cy + 5), 35)
        pygame.draw.circle(surface, RED, (cx + 20, cy + 5), 35)
        pygame.draw.ellipse(surface, RED, (cx - 30, cy - 15, 60, 45))
        # Highlight glint
        pygame.draw.ellipse(surface, (255, 120, 120), (cx - 24, cy - 15, 12, 25))

    elif word == "PEAR":
        # Stem
        pygame.draw.rect(surface, BROWN, (cx - 3, cy - 45, 6, 20))
        # Leaf
        pygame.draw.ellipse(surface, LIME_GREEN, (cx - 20, cy - 45, 20, 10))
        # Pear body (big bottom, small top)
        pygame.draw.circle(surface, LIME_GREEN, (cx, cy + 15), 38)
        pygame.draw.circle(surface, LIME_GREEN, (cx, cy - 15), 26)
        pygame.draw.ellipse(surface, LIME_GREEN, (cx - 26, cy - 20, 52, 50))

    elif word == "BANANA":
        # Yellow curve (overlapping arcs/polygons)
        banana_surf = pygame.Surface((130, 130), pygame.SRCALPHA)
        pygame.draw.circle(banana_surf, GOLD, (65, 65), 50, 16)
        pygame.draw.rect(banana_surf, (0, 0, 0, 0), (0, 0, 130, 60)) # Cut top half
        # Draw stem tips
        pygame.draw.circle(surface, GOLD, (cx - 25, cy - 15), 10)
        pygame.draw.circle(surface, GOLD, (cx + 25, cy - 15), 10)
        pygame.draw.ellipse(surface, GOLD, (cx - 45, cy - 15, 90, 45))
        pygame.draw.ellipse(surface, CREAM_WHITE, (cx - 35, cy - 25, 70, 40)) # Hollow inside
        # End cap (brown)
        pygame.draw.circle(surface, (100, 50, 10), (cx - 42, cy + 2), 6)
        pygame.draw.circle(surface, (100, 50, 10), (cx + 42, cy + 2), 6)

    elif word == "CAKE":
        # Cake Stand / Plate
        pygame.draw.ellipse(surface, DEEP_SKY, (cx - 50, cy + 30, 100, 18))
        # Cake body (sponge cylinder)
        pygame.draw.rect(surface, SOFT_YELLOW, (cx - 42, cy - 15, 84, 45))
        pygame.draw.ellipse(surface, SOFT_YELLOW, (cx - 42, cy + 15, 84, 20))
        pygame.draw.ellipse(surface, HOT_PINK, (cx - 42, cy - 25, 84, 20)) # Frosting top
        # Draw layers details (frosting lines)
        pygame.draw.rect(surface, HOT_PINK, (cx - 42, cy + 5, 84, 6))
        # Candle
        pygame.draw.rect(surface, RED, (cx - 3, cy - 45, 6, 25))
        # Flame
        pygame.draw.ellipse(surface, SUNNY_YELLOW, (cx - 5, cy - 58, 10, 16))

    elif word == "MILK":
        # Milk Carton Body
        pygame.draw.rect(surface, (220, 240, 255), (cx - 25, cy - 20, 50, 60), border_radius=4)
        # Triangle folding top
        pygame.draw.polygon(surface, (220, 240, 255), [(cx - 25, cy - 20), (cx + 25, cy - 20), (cx + 15, cy - 38), (cx - 15, cy - 38)])
        # Straw
        pygame.draw.line(surface, RED, (cx + 5, cy - 48), (cx + 5, cy - 10), 4)
        pygame.draw.line(surface, RED, (cx + 5, cy - 48), (cx + 18, cy - 48), 4)
        # Cow spots (Decoration)
        pygame.draw.ellipse(surface, PEACH_BROWN, (cx - 15, cy, 14, 18))
        pygame.draw.ellipse(surface, PEACH_BROWN, (cx + 5, cy + 15, 12, 10))
        # Label text placeholder
        lbl_font = load_font(16, bold=True)
        lbl = lbl_font.render("MILK", True, DEEP_SKY)
        surface.blit(lbl, lbl.get_rect(center=(cx, cy - 5)))

    elif word == "EGG":
        # Nest/Egg holder
        pygame.draw.arc(surface, PEACH_BROWN, (cx - 30, cy + 12, 60, 30), math.pi, 2*math.pi, 10)
        # Egg body (Oval)
        egg_rect = pygame.Rect(cx - 22, cy - 32, 44, 60)
        pygame.draw.ellipse(surface, WHITE, egg_rect)
        pygame.draw.ellipse(surface, (230, 230, 230), egg_rect, 2)
        # Glint
        pygame.draw.ellipse(surface, (255,255,255, 150), (cx - 12, cy - 22, 10, 18))

    elif word == "CAR":
        # Wheels
        pygame.draw.circle(surface, BLACK, (cx - 25, cy + 28), 15)
        pygame.draw.circle(surface, BLACK, (cx + 25, cy + 28), 15)
        pygame.draw.circle(surface, WHITE, (cx - 25, cy + 28), 6)
        pygame.draw.circle(surface, WHITE, (cx + 25, cy + 28), 6)
        # Car Body
        pygame.draw.rect(surface, RED, (cx - 45, cy - 2, 90, 24), border_radius=6)
        # Cabin
        pygame.draw.polygon(surface, RED, [(cx - 30, cy - 2), (cx - 15, cy - 22), (cx + 15, cy - 22), (cx + 30, cy - 2)])
        # Windows
        pygame.draw.polygon(surface, SKY_BLUE, [(cx - 22, cy - 4), (cx - 12, cy - 18), (cx, cy - 18), (cx, cy - 4)])
        pygame.draw.polygon(surface, SKY_BLUE, [(cx + 2, cy - 4), (cx + 2, cy - 18), (cx + 12, cy - 18), (cx + 22, cy - 4)])
        # Light (yellow headlight)
        pygame.draw.circle(surface, SUNNY_YELLOW, (cx + 42, cy + 6), 5)

    elif word == "BUS":
        # Wheels
        pygame.draw.circle(surface, BLACK, (cx - 30, cy + 30), 14)
        pygame.draw.circle(surface, BLACK, (cx + 30, cy + 30), 14)
        pygame.draw.circle(surface, WHITE, (cx - 30, cy + 30), 5)
        pygame.draw.circle(surface, WHITE, (cx + 30, cy + 30), 5)
        # Bus Body
        pygame.draw.rect(surface, SUNNY_YELLOW, (cx - 52, cy - 25, 104, 50), border_radius=8)
        # Windows
        for i in range(3):
            pygame.draw.rect(surface, SKY_BLUE, (cx - 40 + i*26, cy - 15, 18, 18), border_radius=2)
        # Headlight
        pygame.draw.circle(surface, WHITE, (cx + 48, cy + 12), 6)
        # Bumper
        pygame.draw.rect(surface, BLACK, (cx - 54, cy + 20, 108, 6), border_radius=2)

    elif word == "CUP":
        # Cup body
        pygame.draw.rect(surface, DEEP_SKY, (cx - 28, cy - 22, 56, 52), border_radius=8)
        # Rim ellipse
        pygame.draw.ellipse(surface, DEEP_SKY, (cx - 28, cy - 28, 56, 12))
        pygame.draw.ellipse(surface, CREAM_WHITE, (cx - 24, cy - 26, 48, 8))
        # Handle
        pygame.draw.arc(surface, DEEP_SKY, (cx - 45, cy - 16, 25, 36), math.pi/2, 3*math.pi/2, 6)
        # Steam lines
        pygame.draw.arc(surface, DEEP_SKY, (cx - 10, cy - 46, 10, 16), -math.pi/2, math.pi/2, 2)
        pygame.draw.arc(surface, DEEP_SKY, (cx + 4, cy - 46, 10, 16), -math.pi/2, math.pi/2, 2)

    elif word == "HAT":
        # Brim (Base ellipse)
        pygame.draw.ellipse(surface, ORANGE, (cx - 52, cy + 12, 104, 22))
        # Cap crown
        pygame.draw.rect(surface, ORANGE, (cx - 32, cy - 32, 64, 46), border_radius=8)
        # Hat band / ribbon (Purple)
        pygame.draw.rect(surface, PURPLE, (cx - 32, cy + 2, 64, 10))

    elif word == "BOX":
        # Drawing 2.5D Carton Box
        # Back base
        pygame.draw.rect(surface, (205, 133, 63), (cx - 35, cy - 15, 70, 50), border_radius=4)
        # Flaps opening (top-left, top-right)
        pygame.draw.polygon(surface, (244, 164, 96), [(cx - 35, cy - 15), (cx - 55, cy - 28), (cx - 15, cy - 28), (cx - 15, cy - 15)])
        pygame.draw.polygon(surface, (244, 164, 96), [(cx + 35, cy - 15), (cx + 55, cy - 28), (cx + 15, cy - 28), (cx + 15, cy - 15)])
        # Shadow / Interior dark brown cavity
        pygame.draw.rect(surface, (139, 69, 19), (cx - 31, cy - 15, 62, 12))
        # Front flap folded down
        pygame.draw.polygon(surface, (222, 184, 135), [(cx - 35, cy - 3), (cx - 35, cy + 15), (cx + 35, cy + 15), (cx + 35, cy - 3)])

    elif word == "BALL":
        # Main Sphere
        pygame.draw.circle(surface, SUNNY_YELLOW, (cx, cy + 10), 45)
        # Colored stripes (using arcs or overlapping ellipses)
        # Left slice (Red)
        pygame.draw.ellipse(surface, RED, (cx - 45, cy - 35, 35, 90))
        # Right slice (Blue)
        pygame.draw.ellipse(surface, DEEP_SKY, (cx + 10, cy - 35, 35, 90))
        # Redraw center circle to crop inside
        # Mask layer can also work, but simple layered ellipses is very clean
        pygame.draw.circle(surface, SUNNY_YELLOW, (cx, cy + 10), 45, 6)

    elif word in ["RED", "BLUE", "GREEN", "YELLOW", "PINK"]:
        color_map = {
            "RED": RED, "BLUE": DEEP_SKY, "GREEN": LIME_GREEN, "YELLOW": SUNNY_YELLOW, "PINK": HOT_PINK
        }
        fill_color = color_map.get(word, RED)
        # Paint Bucket
        # Spilled puddle
        pygame.draw.ellipse(surface, fill_color, (cx - 45, cy + 22, 90, 20))
        # Bucket body
        pygame.draw.polygon(surface, (180, 180, 180), [(cx - 25, cy - 25), (cx + 25, cy - 25), (cx + 18, cy + 15), (cx - 18, cy + 15)])
        # Rim
        pygame.draw.ellipse(surface, (180, 180, 180), (cx - 25, cy - 28, 50, 8))
        # Interior color inside bucket
        pygame.draw.ellipse(surface, fill_color, (cx - 22, cy - 27, 44, 6))
        # Paint spill line
        pygame.draw.rect(surface, fill_color, (cx - 8, cy - 24, 16, 42), border_radius=4)
        # Handle (metallic grey wire)
        pygame.draw.arc(surface, (100, 100, 100), (cx - 30, cy - 35, 60, 30), 0, math.pi, 2)

    elif word in ["RUN", "JUMP", "FLY", "WALK", "SWIM"]:
        # Action Drawings (Detailed Cartoon Styles)
        if word == "RUN":
            # Running cute cartoon character (Peach head, red shirt, blue shorts, gold shoes, speed dust)
            # Torso / Shirt (Red)
            pygame.draw.ellipse(surface, RED, (cx - 14, cy - 12, 28, 22))
            # Shorts (Blue)
            pygame.draw.rect(surface, DEEP_SKY, (cx - 10, cy + 8, 20, 10))
            # Head (Peach skin)
            pygame.draw.circle(surface, PEACH_SKIN, (cx - 4, cy - 23), 11)
            # Hair/Cap (Brown)
            pygame.draw.ellipse(surface, BROWN, (cx - 10, cy - 31, 14, 10))
            # Back Leg
            pygame.draw.line(surface, PEACH_SKIN, (cx - 6, cy + 16), (cx - 18, cy + 28), 5)
            pygame.draw.circle(surface, GOLD, (cx - 18, cy + 28), 5)
            # Front Leg
            pygame.draw.line(surface, PEACH_SKIN, (cx + 6, cy + 16), (cx + 18, cy + 22), 5)
            pygame.draw.circle(surface, GOLD, (cx + 18, cy + 22), 5)
            # Back Arm
            pygame.draw.line(surface, PEACH_SKIN, (cx - 8, cy - 8), (cx - 22, cy), 5)
            pygame.draw.circle(surface, PEACH_SKIN, (cx - 22, cy), 4)
            # Front Arm
            pygame.draw.line(surface, PEACH_SKIN, (cx + 8, cy - 8), (cx + 18, cy - 2), 5)
            pygame.draw.circle(surface, PEACH_SKIN, (cx + 18, cy - 2), 4)
            # Speed Dust clouds
            pygame.draw.circle(surface, (235, 235, 235), (cx - 30, cy + 22), 7)
            pygame.draw.circle(surface, (235, 235, 235), (cx - 38, cy + 25), 4)
            
        elif word == "JUMP":
            # Jumping cute cartoon character (Yellow shirt, green shorts, peach head/arms/legs, red shoes)
            # Torso / Shirt (Yellow)
            pygame.draw.ellipse(surface, SUNNY_YELLOW, (cx - 14, cy - 16, 28, 22))
            # Shorts (Green)
            pygame.draw.rect(surface, LIME_GREEN, (cx - 10, cy + 4, 20, 8))
            # Head (Peach skin)
            pygame.draw.circle(surface, PEACH_SKIN, (cx, cy - 27), 11)
            # Left Arm raised
            pygame.draw.line(surface, PEACH_SKIN, (cx - 12, cy - 10), (cx - 25, cy - 22), 5)
            pygame.draw.circle(surface, PEACH_SKIN, (cx - 25, cy - 22), 4)
            # Right Arm raised
            pygame.draw.line(surface, PEACH_SKIN, (cx + 12, cy - 10), (cx + 25, cy - 22), 5)
            pygame.draw.circle(surface, PEACH_SKIN, (cx + 25, cy - 22), 4)
            # Left Leg bent
            pygame.draw.line(surface, PEACH_SKIN, (cx - 6, cy + 10), (cx - 16, cy + 22), 5)
            pygame.draw.circle(surface, RED, (cx - 16, cy + 22), 5)
            # Right Leg bent
            pygame.draw.line(surface, PEACH_SKIN, (cx + 6, cy + 10), (cx + 16, cy + 22), 5)
            pygame.draw.circle(surface, RED, (cx + 16, cy + 22), 5)
            # Spring jump lines
            pygame.draw.arc(surface, ORANGE, (cx - 18, cy + 18, 36, 12), 0, math.pi, 2)
            pygame.draw.arc(surface, ORANGE, (cx - 10, cy + 23, 20, 8), 0, math.pi, 1)
            
        elif word == "FLY":
            # Beautiful cartoon airplane flying (Clouds backdrop, red fuselage, gold wings/spinner, sky-blue window)
            # Cloud background
            pygame.draw.circle(surface, (230, 245, 255), (cx - 24, cy + 16), 16)
            pygame.draw.circle(surface, (230, 245, 255), (cx + 24, cy + 16), 16)
            pygame.draw.circle(surface, (230, 245, 255), (cx, cy + 10), 22)
            
            # Wings (Gold vertical ellipse behind fuselage)
            pygame.draw.ellipse(surface, GOLD, (cx - 10, cy - 20, 20, 42))
            # Fuselage / Body (Red horizontal ellipse)
            pygame.draw.ellipse(surface, RED, (cx - 36, cy - 8, 72, 22))
            # Tail fin (Red polygon)
            pygame.draw.polygon(surface, RED, [(cx - 36, cy - 4), (cx - 44, cy - 20), (cx - 26, cy - 4)])
            # Cockpit Window (Sky Blue circle)
            pygame.draw.circle(surface, SKY_BLUE, (cx + 16, cy - 2), 6)
            pygame.draw.circle(surface, WHITE, (cx + 16, cy - 2), 6, 1)
            # Propeller Spinner (Gold)
            pygame.draw.ellipse(surface, GOLD, (cx + 34, cy - 6, 5, 14))
            
        elif word == "WALK":
            # Walking cartoon character (Peach head, orange shirt, brown trousers, blue shoes, green pathway)
            # Torso / Shirt (Orange)
            pygame.draw.ellipse(surface, ORANGE, (cx - 12, cy - 10, 24, 24))
            # Pants (Brown)
            pygame.draw.rect(surface, PEACH_BROWN, (cx - 10, cy + 10, 20, 10))
            # Head (Peach skin)
            pygame.draw.circle(surface, PEACH_SKIN, (cx, cy - 22), 11)
            # Back Leg
            pygame.draw.line(surface, PEACH_SKIN, (cx - 5, cy + 18), (cx - 12, cy + 30), 5)
            pygame.draw.circle(surface, DEEP_SKY, (cx - 12, cy + 30), 5)
            # Front Leg
            pygame.draw.line(surface, PEACH_SKIN, (cx + 5, cy + 18), (cx + 12, cy + 30), 5)
            pygame.draw.circle(surface, DEEP_SKY, (cx + 12, cy + 30), 5)
            # Arms
            pygame.draw.line(surface, PEACH_SKIN, (cx - 6, cy - 6), (cx - 14, cy + 6), 5)
            pygame.draw.circle(surface, PEACH_SKIN, (cx - 14, cy + 6), 4)
            pygame.draw.line(surface, PEACH_SKIN, (cx + 6, cy - 6), (cx + 14, cy + 6), 5)
            pygame.draw.circle(surface, PEACH_SKIN, (cx + 14, cy + 6), 4)
            # Path below
            pygame.draw.line(surface, JUNGLE_GREEN, (cx - 38, cy + 32), (cx + 38, cy + 32), 3)

        elif word == "SWIM":
            # Swim cartoon character (Translucent blue water waves, peach head, pink cap, black goggles, splashes)
            # Waves (water lines)
            pygame.draw.ellipse(surface, DEEP_SKY, (cx - 45, cy + 12, 90, 22))
            pygame.draw.ellipse(surface, CREAM_WHITE, (cx - 40, cy + 16, 80, 14))
            # Swimming person
            # Head (Peach skin)
            pygame.draw.circle(surface, PEACH_SKIN, (cx, cy - 10), 12)
            # Goggles (Black)
            pygame.draw.rect(surface, BLACK, (cx - 8, cy - 12, 16, 4), border_radius=2)
            # Swim Cap (Pink)
            pygame.draw.arc(surface, HOT_PINK, (cx - 13, cy - 22, 26, 18), 0, math.pi, 4)
            # Paddling Arm
            pygame.draw.arc(surface, PEACH_SKIN, (cx - 28, cy - 24, 42, 28), 0, math.pi, 4)
            # Splash drops
            pygame.draw.circle(surface, DEEP_SKY, (cx + 25, cy - 14), 4)
            pygame.draw.circle(surface, DEEP_SKY, (cx - 20, cy - 20), 3)

    elif word == "STAR":
        # Glowing Golden Star
        points = []
        for i in range(10):
            r = 45 if i % 2 == 0 else 20
            angle = math.pi * 2 * i / 10 - math.pi / 2
            x = cx + r * math.cos(angle)
            y = cy + 5 + r * math.sin(angle)
            points.append((x, y))
        pygame.draw.polygon(surface, GOLD, points)
        pygame.draw.polygon(surface, WHITE, points, 3)

    elif word == "MOON":
        # Crescent moon (overlapping circles)
        pygame.draw.circle(surface, SOFT_YELLOW, (cx, cy + 8), 42)
        pygame.draw.circle(surface, CREAM_WHITE, (cx + 18, cy + 2), 38) # cut out background circle
        # Sleeping eye
        pygame.draw.arc(surface, BLACK, (cx - 15, cy + 4, 12, 10), math.pi, 2*math.pi, 2)
        # Tiny cute star next to it
        pygame.draw.polygon(surface, GOLD, [(cx + 25, cy - 22), (cx + 28, cy - 16), (cx + 34, cy - 16), (cx + 29, cy - 12), (cx + 31, cy - 6), (cx + 25, cy - 10), (cx + 19, cy - 6), (cx + 21, cy - 12), (cx + 16, cy - 16), (cx + 22, cy - 16)])

    elif word == "ROCKET":
        # Spaceship body
        # Flame booster
        pygame.draw.polygon(surface, ORANGE, [(cx - 10, cy + 25), (cx + 10, cy + 25), (cx, cy + 48)])
        pygame.draw.polygon(surface, SUNNY_YELLOW, [(cx - 6, cy + 25), (cx + 6, cy + 25), (cx, cy + 40)])
        # Silver capsule body (upward angled ellipse or rectangle with cone)
        pygame.draw.rect(surface, (220, 220, 220), (cx - 16, cy - 25, 32, 50), border_radius=4)
        # Red Cone
        pygame.draw.polygon(surface, RED, [(cx - 16, cy - 25), (cx + 16, cy - 25), (cx, cy - 50)])
        # Side Wings
        pygame.draw.polygon(surface, RED, [(cx - 16, cy + 5), (cx - 30, cy + 25), (cx - 16, cy + 25)])
        pygame.draw.polygon(surface, RED, [(cx + 16, cy + 5), (cx + 30, cy + 25), (cx + 16, cy + 25)])
        # Porthole Window
        pygame.draw.circle(surface, DEEP_SKY, (cx, cy - 5), 8)
        pygame.draw.circle(surface, WHITE, (cx, cy - 5), 8, 2)

    elif word == "SUN":
        # Sun center
        pygame.draw.circle(surface, SUNNY_YELLOW, (cx, cy + 10), 32)
        # Rays
        for angle in range(0, 360, 45):
            rad = math.radians(angle)
            rx1 = cx + 38 * math.cos(rad)
            ry1 = cy + 10 + 38 * math.sin(rad)
            rx2 = cx + 52 * math.cos(rad)
            ry2 = cy + 10 + 52 * math.sin(rad)
            pygame.draw.line(surface, ORANGE, (rx1, ry1), (rx2, ry2), 5)
        # Happy face
        pygame.draw.circle(surface, BLACK, (cx - 10, cy + 6), 4)
        pygame.draw.circle(surface, BLACK, (cx + 10, cy + 6), 4)
        pygame.draw.arc(surface, BLACK, (cx - 10, cy + 10, 20, 12), math.pi, 2*math.pi, 2)

    elif word == "UFO":
        # Space background circle
        # Green Saucer base
        pygame.draw.ellipse(surface, LIME_GREEN, (cx - 45, cy + 12, 90, 22))
        # Glass cockpit dome
        pygame.draw.arc(surface, DEEP_SKY, (cx - 24, cy - 18, 48, 36), 0, math.pi, 4)
        # Fill cockpit dome (alpha translucent overlay)
        glass_surf = pygame.Surface((48, 36), pygame.SRCALPHA)
        pygame.draw.ellipse(glass_surf, (100, 200, 255, 120), (0, 0, 48, 36))
        surface.blit(glass_surf, (cx - 24, cy - 18))
        # Tiny green alien inside
        pygame.draw.circle(surface, LIME_GREEN, (cx, cy - 6), 8)
        pygame.draw.circle(surface, BLACK, (cx - 3, cy - 8), 2)
        pygame.draw.circle(surface, BLACK, (cx + 3, cy - 8), 2)
        # Glowing lights under saucer
        for dx in [-30, 0, 30]:
            pygame.draw.circle(surface, SUNNY_YELLOW, (cx + dx, cy + 20), 4)

# --- Guide Monkey Character Model ---
class MonkeyGuide:
    """Manages rendering, scaling, expressions, and hopping animations for Max the Monkey."""
    def __init__(self, x=200, y=500):
        self.x = x
        self.y = y
        self.target_x = x
        self.target_y = y
        self.hop_t = 0.0
        self.is_hopping = False
        
        # Guide evolution mechanics
        # Stage 0: Small monkey (scale 0.65)
        # Stage 1: Medium monkey (scale 0.9)
        # Stage 2: Large monkey (scale 1.15)
        self.stage = 0
        
        # Expression can be: "neutral", "happy", "sad", "waving", "eating", "dancing"
        self.expression = "neutral"
        self.wave_angle = 0
        self.dance_timer = 0
        
    def set_target(self, tx, ty):
        self.target_x = tx
        self.target_y = ty
        self.is_hopping = True
        self.hop_t = 0.0

    def update(self, dt):
        # 1. Hopping animation (parabolic path)
        if self.is_hopping:
            self.hop_t += dt * 1.8  # Speed of movement
            if self.hop_t >= 1.0:
                self.hop_t = 1.0
                self.x = self.target_x
                self.y = self.target_y
                self.is_hopping = False
            else:
                # Linear interpolation for x
                self.x = self.x * (1.0 - self.hop_t) + self.target_x * self.hop_t
                # Parabolic arc for y
                mid_y = min(self.y, self.target_y) - 120 # Hop height
                t = self.hop_t
                self.y = (1-t)*(1-t)*self.y + 2*(1-t)*t*mid_y + t*t*self.target_y
        
        # 2. Expression-related timer updates
        self.wave_angle = math.sin(pygame.time.get_ticks() * 0.01) * 30
        self.dance_timer += dt

    def draw(self, surface):
        # Determine scale based on stage
        base_scales = [0.65, 0.9, 1.15]
        scale = base_scales[self.stage]
        
        # Calculate bobbing effect
        bob = math.sin(pygame.time.get_ticks() * 0.005) * 4 if not self.is_hopping else 0
        if self.expression == "dancing":
            bob = abs(math.sin(self.dance_timer * 8) * 15)
        
        cx, cy = int(self.x), int(self.y + bob)
        
        # Offset details (scaled)
        def sc(val): return int(val * scale)
        
        # --- Draw Monkey Body Elements ---
        # 1. Shadow below
        shadow_w = sc(90)
        shadow_h = sc(16)
        shadow_rect = pygame.Rect(cx - shadow_w//2, int(self.y + sc(90)), shadow_w, shadow_h)
        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 70), (0, 0, shadow_w, shadow_h))
        surface.blit(shadow_surf, shadow_rect.topleft)

        # 2. Tail
        # Draw tail curve using lines or multiple circles
        tail_color = PEACH_BROWN
        tail_points = []
        for i in range(12):
            angle = math.radians(-120 - i*20 + (math.sin(pygame.time.get_ticks()*0.005)*10))
            dist = sc(30 + i*5)
            tx = cx - sc(20) + int(dist * math.cos(angle))
            ty = cy + sc(40) + int(dist * math.sin(angle))
            tail_points.append((tx, ty))
        if len(tail_points) > 1:
            pygame.draw.lines(surface, tail_color, False, tail_points, sc(12))
            # tail tip
            pygame.draw.circle(surface, tail_color, tail_points[-1], sc(7))

        # 3. Arms
        arm_color = PEACH_BROWN
        if self.expression == "waving" or self.expression == "dancing":
            # Wave active arm
            # Left arm (waving)
            wave_rad = math.radians(-30 + self.wave_angle)
            lx = cx - sc(25) + int(sc(45) * math.cos(wave_rad + math.pi))
            ly = cy + sc(20) + int(sc(45) * math.sin(wave_rad + math.pi))
            pygame.draw.line(surface, arm_color, (cx - sc(25), cy + sc(30)), (lx, ly), sc(14))
            pygame.draw.circle(surface, PEACH_SKIN, (lx, ly), sc(10))
            
            # Right arm (down/dancing)
            rx_rad = math.radians(30 + (self.wave_angle if self.expression=="dancing" else 0))
            rx = cx + sc(25) + int(sc(45) * math.cos(rx_rad))
            ry = cy + sc(20) + int(sc(45) * math.sin(rx_rad))
            pygame.draw.line(surface, arm_color, (cx + sc(25), cy + sc(30)), (rx, ry), sc(14))
            pygame.draw.circle(surface, PEACH_SKIN, (rx, ry), sc(10))
        else:
            # Neutral / resting arms
            pygame.draw.line(surface, arm_color, (cx - sc(25), cy + sc(35)), (cx - sc(55), cy + sc(60)), sc(12)) # L
            pygame.draw.circle(surface, PEACH_SKIN, (cx - sc(55), cy + sc(60)), sc(9))
            
            pygame.draw.line(surface, arm_color, (cx + sc(25), cy + sc(35)), (cx + sc(55), cy + sc(60)), sc(12)) # R
            pygame.draw.circle(surface, PEACH_SKIN, (cx + sc(55), cy + sc(60)), sc(9))

        # 4. Legs
        pygame.draw.line(surface, arm_color, (cx - sc(18), cy + sc(65)), (cx - sc(26), cy + sc(95)), sc(15)) # L
        pygame.draw.ellipse(surface, PEACH_SKIN, (cx - sc(38), cy + sc(90), sc(22), sc(12)))
        pygame.draw.line(surface, arm_color, (cx + sc(18), cy + sc(65)), (cx + sc(26), cy + sc(95)), sc(15)) # R
        pygame.draw.ellipse(surface, PEACH_SKIN, (cx + sc(16), cy + sc(90), sc(22), sc(12)))

        # 5. Torso
        pygame.draw.circle(surface, PEACH_BROWN, (cx, cy + sc(45)), sc(35))
        # Tummy patch (light skin)
        pygame.draw.circle(surface, PEACH_SKIN, (cx, cy + sc(48)), sc(22))

        # 6. Ears
        pygame.draw.circle(surface, PEACH_BROWN, (cx - sc(48), cy), sc(18))
        pygame.draw.circle(surface, PEACH_SKIN, (cx - sc(48), cy), sc(11))
        
        pygame.draw.circle(surface, PEACH_BROWN, (cx + sc(48), cy), sc(18))
        pygame.draw.circle(surface, PEACH_SKIN, (cx + sc(48), cy), sc(11))

        # 7. Head (Brown circle)
        pygame.draw.circle(surface, PEACH_BROWN, (cx, cy), sc(45))

        # 8. Face mask (light skin heart/butterfly shape)
        pygame.draw.circle(surface, PEACH_SKIN, (cx - sc(18), cy - sc(4)), sc(22))
        pygame.draw.circle(surface, PEACH_SKIN, (cx + sc(18), cy - sc(4)), sc(22))
        pygame.draw.ellipse(surface, PEACH_SKIN, (cx - sc(26), cy + sc(4), sc(52), sc(30)))

        # 9. Eyes
        eye_y = cy - sc(6)
        pygame.draw.circle(surface, BLACK, (cx - sc(14), eye_y), sc(7))
        pygame.draw.circle(surface, BLACK, (cx + sc(14), eye_y), sc(7))
        # Glints
        pygame.draw.circle(surface, WHITE, (cx - sc(16), eye_y - sc(2)), sc(2.5))
        pygame.draw.circle(surface, WHITE, (cx + sc(12), eye_y - sc(2)), sc(2.5))

        # 10. Nose (small black oval)
        pygame.draw.ellipse(surface, BLACK, (cx - sc(4), cy + sc(10), sc(8), sc(5)))

        # 11. Mouth / Expressions
        mouth_y = cy + sc(20)
        if self.expression in ["happy", "waving", "dancing"]:
            # Wide open mouth smile
            pygame.draw.arc(surface, RED, (cx - sc(15), cy + sc(12), sc(30), sc(20)), math.pi, 2*math.pi, sc(10))
            pygame.draw.arc(surface, BLACK, (cx - sc(15), cy + sc(12), sc(30), sc(20)), math.pi, 2*math.pi, sc(2))
        elif self.expression == "sad":
            # Frown
            pygame.draw.arc(surface, BLACK, (cx - sc(12), mouth_y, sc(24), sc(16)), 0, math.pi, sc(3))
        elif self.expression == "eating":
            # Chewing (alternating small mouth line)
            chew = int(math.sin(pygame.time.get_ticks() * 0.02) * 5)
            pygame.draw.ellipse(surface, BLACK, (cx - sc(8), mouth_y, sc(16), sc(4) + sc(chew)))
        else:
            # Neutral grin
            pygame.draw.arc(surface, BLACK, (cx - sc(12), cy + sc(10), sc(24), sc(16)), math.pi, 2*math.pi, sc(3))
