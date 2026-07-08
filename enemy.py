import pygame
import math
import random
from utils import clamp, distance, angle_between
from settings import ENEMY_TYPES, SCREEN_WIDTH, SCREEN_HEIGHT


class Jellyfish(pygame.sprite.Sprite):
    def __init__(self, pos=None):
        super().__init__()
        info = ENEMY_TYPES["jellyfish"]
        self.pos = pos or pygame.Vector2(
            random.uniform(100, SCREEN_WIDTH - 100),
            random.uniform(*info["depth_range"]))
        self.vel = pygame.Vector2(0, 0)
        self.speed = info["speed"]
        self.hp = info["hp"]
        self.damage = info["damage"]
        self.stun_time = info["stun_time"]
        self.width, self.height = info["size"]
        self.base_y = self.pos.y
        self.time = 0.0
        self._layer = 3

        self.image = self._create_surface()
        self.rect = self.image.get_rect(center=self.pos)

    def _create_surface(self):
        info = ENEMY_TYPES["jellyfish"]
        color = info["color"]
        color2 = info["color2"]
        w, h = self.width, self.height
        surf = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)

        # Dome
        pygame.draw.ellipse(surf, color, (5, 0, w, h * 0.6))
        pygame.draw.ellipse(surf, color2, (8, 5, w - 6, h * 0.4))
        # Tentacles
        for i in range(5):
            ox = 8 + i * (w / 5)
            phase = i * 0.8
            pts = []
            for j in range(8):
                tx = ox + math.sin(j * 0.5 + phase) * 4
                ty = h * 0.5 + j * (h * 0.5 / 8)
                pts.append((tx, ty))
            if len(pts) > 1:
                pygame.draw.lines(surf, color, False, pts, 2)
        # Glow
        glow = pygame.Surface((w + 20, h + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (180, 80, 220, 30), (2, 2, w + 16, h + 16))
        surf.blit(glow, (-6, -6))
        return surf

    def update(self, dt, player_pos=None):
        self.time += dt
        # Float up and down
        self.pos.y = self.base_y + math.sin(self.time * 0.5) * 30
        self.pos.x += math.sin(self.time * 0.3) * 0.5

        # Drift toward player slowly
        if player_pos and distance(self.pos, player_pos) > 200:
            angle = angle_between(self.pos, player_pos)
            self.pos.x += math.cos(angle) * self.speed * 0.3 * dt
            self.pos.y += math.sin(angle) * self.speed * 0.3 * dt

        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, surface, offset=(0, 0)):
        px = int(self.pos.x - offset[0])
        py = int(self.pos.y - offset[1])
        if px < -100 or px > SCREEN_WIDTH + 100:
            return
        glow = pygame.Surface((self.width + 20, self.height + 20), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (180, 80, 220, 20), (0, 0, self.width + 20, self.height + 20))
        surface.blit(glow, (px - 10, py - 10))
        surface.blit(self.image, (px - self.width // 2 - 5, py - self.height // 2 - 5))

    def take_damage(self, amount):
        self.hp -= amount
        return self.hp <= 0


class SeaMine(pygame.sprite.Sprite):
    def __init__(self, pos=None):
        super().__init__()
        info = ENEMY_TYPES["sea_mine"]
        self.pos = pos or pygame.Vector2(
            random.uniform(100, SCREEN_WIDTH - 100),
            random.uniform(*info["depth_range"]))
        self.vel = pygame.Vector2(0, 0)
        self.hp = info["hp"]
        self.damage = info["damage"]
        self.explosion_radius = info["explosion_radius"]
        self.width = info["size"][0]
        self.exploded = False
        self.explode_timer = 0.0
        self.time = 0.0
        self._layer = 3

        self.image = self._create_surface()
        self.rect = self.image.get_rect(center=self.pos)

    def _create_surface(self):
        info = ENEMY_TYPES["sea_mine"]
        color = info["color"]
        accent = info["color2"]
        size = info["size"][0]
        surf = pygame.Surface((size + 10, size + 10), pygame.SRCALPHA)
        # Body
        pygame.draw.circle(surf, color, (size // 2 + 5, size // 2 + 5), size // 2)
        # Spikes
        for i in range(8):
            angle = i * math.pi / 4
            sx = size // 2 + 5 + math.cos(angle) * (size // 2)
            sy = size // 2 + 5 + math.sin(angle) * (size // 2)
            ex = size // 2 + 5 + math.cos(angle) * (size // 2 + 6)
            ey = size // 2 + 5 + math.sin(angle) * (size // 2 + 6)
            pygame.draw.line(surf, color, (sx, sy), (ex, ey), 2)
        # Red accent
        pygame.draw.circle(surf, accent, (size // 2 + 5, size // 2 + 5), size // 4)
        return surf

    def update(self, dt, player_pos=None):
        self.time += dt
        if self.exploded:
            self.explode_timer -= dt
            if self.explode_timer <= 0:
                self.kill()
            return
        self.pos.y += math.sin(self.time * 0.3) * 5 * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, surface, offset=(0, 0)):
        px = int(self.pos.x - offset[0])
        py = int(self.pos.y - offset[1])
        if px < -100 or px > SCREEN_WIDTH + 100:
            return
        if self.exploded:
            progress = 1.0 - (self.explode_timer / 1.0)
            r = self.explosion_radius * (1 + progress * 0.5)
            alpha = int(200 * (1 - progress))
            expl = pygame.Surface((int(r * 2), int(r * 2)), pygame.SRCALPHA)
            pygame.draw.circle(expl, (255, 100, 50, alpha), (int(r), int(r)), int(r))
            pygame.draw.circle(expl, (255, 200, 50, alpha // 2), (int(r), int(r)), int(r * 0.6))
            surface.blit(expl, (int(px - r), int(py - r)))
        else:
            surface.blit(self.image, (px - self.width // 2 - 5, py - self.width // 2 - 5))

    def explode(self):
        if not self.exploded:
            self.exploded = True
            self.explode_timer = 1.0
            return True
        return False
