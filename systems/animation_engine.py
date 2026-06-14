import math
import random
import pygame

class Easing:
    @staticmethod
    def ease_out_back(t):
        """Creates a nice overshoot bounce effect."""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * math.pow(t - 1, 3) + c1 * math.pow(t - 1, 2)
        
    @staticmethod
    def ease_out_quad(t):
        return t * (2 - t)

    @staticmethod
    def ease_in_out_quad(t):
        if t < 0.5:
            return 2 * t * t
        return 1 - math.pow(-2 * t + 2, 2) / 2

class Particle:
    def __init__(self, x, y, shape="circle", color=(255, 255, 255), size=None):
        self.x = x
        self.y = y
        self.shape = shape # "circle", "star", "confetti"
        self.color = color
        
        # Physics
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-6, -1)
        self.gravity = 0.2
        
        # Lifespan
        self.life = 1.0 # 100% life
        self.decay = random.uniform(0.015, 0.035)
        
        # Dimensions
        self.size = size or random.randint(6, 12)
        self.angle = random.uniform(0, 360)
        self.rot_speed = random.uniform(-8, 8)
        
    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.angle += self.rot_speed
        self.life -= self.decay
        if self.life < 0:
            self.life = 0

    def draw(self, surface):
        if self.life <= 0:
            return
            
        alpha = int(self.life * 255)
        color_with_alpha = (self.color[0], self.color[1], self.color[2], alpha)
        
        # Render surface with alpha
        p_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        
        if self.shape == "circle":
            pygame.draw.circle(p_surf, color_with_alpha, (self.size, self.size), self.size)
        elif self.shape == "confetti":
            # Draw a rotating rectangle
            # Simple rotated rectangle drawn dynamically
            rot_rect = pygame.Surface((self.size * 2, self.size), pygame.SRCALPHA)
            pygame.draw.rect(rot_rect, color_with_alpha, (0, 0, self.size * 2, self.size))
            rotated = pygame.transform.rotate(rot_rect, self.angle)
            p_surf.blit(rotated, (self.size - rotated.get_width()//2, self.size - rotated.get_height()//2))
        elif self.shape == "star":
            # Draw simple 4-point star polygon
            points = [
                (self.size, 0),
                (self.size + self.size//3, self.size - self.size//3),
                (self.size * 2, self.size),
                (self.size + self.size//3, self.size + self.size//3),
                (self.size, self.size * 2),
                (self.size - self.size//3, self.size + self.size//3),
                (0, self.size),
                (self.size - self.size//3, self.size - self.size//3)
            ]
            pygame.draw.polygon(p_surf, color_with_alpha, points)
            
        surface.blit(p_surf, (int(self.x - self.size), int(self.y - self.size)))

class ParticleSystem:
    def __init__(self):
        self.particles = []
        
    def spawn_burst(self, x, y, count=15, shape="circle", colors=None):
        if not colors:
            colors = [(255, 69, 0), (255, 215, 0), (50, 205, 50), (30, 144, 255), (255, 105, 180)]
            
        for _ in range(count):
            color = random.choice(colors)
            p = Particle(x, y, shape, color)
            # Make confetti spread wider
            if shape == "confetti":
                p.vx = random.uniform(-6, 6)
                p.vy = random.uniform(-9, -3)
            self.particles.append(p)
            
    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        
    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)

class ScreenTransition:
    """Manages simple camera zoom and slide/fade transitions between screens."""
    def __init__(self):
        self.fade_alpha = 255
        self.target_alpha = 0
        self.transitioning = False
        self.speed = 4.0
        
    def start_fade_in(self):
        self.fade_alpha = 255
        self.target_alpha = 0
        self.transitioning = True
        self.speed = 4.0
        
    def start_fade_out(self):
        self.fade_alpha = 0
        self.target_alpha = 255
        self.transitioning = True
        self.speed = 4.0
        
    def update(self, dt):
        if not self.transitioning:
            return False
            
        diff = self.target_alpha - self.fade_alpha
        if abs(diff) < 2:
            self.fade_alpha = self.target_alpha
            self.transitioning = False
            return True # Transition completed
        else:
            self.fade_alpha += (diff * dt * self.speed)
            self.fade_alpha = max(0, min(255, self.fade_alpha))
        return False
        
    def draw(self, surface, width, height):
        if self.fade_alpha > 0:
            overlay = pygame.Surface((width, height), pygame.SRCALPHA)
            overlay.fill((15, 10, 20, int(self.fade_alpha)))
            surface.blit(overlay, (0, 0))
