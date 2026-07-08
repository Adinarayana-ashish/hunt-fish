import pygame
import math
from settings import HARPOON_SPEED, HARPOON_LIFETIME, HARPOON_DAMAGE, COLORS


class Harpoon(pygame.sprite.Sprite):
    def __init__(self, pos, angle, damage=1, speed=HARPOON_SPEED):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
        self.damage = damage
        self.lifetime = HARPOON_LIFETIME
        self.age = 0.0
        self.traveled = 0.0
        self.angle = math.degrees(angle)

        self.image = self._create_surface()
        self.rect = self.image.get_rect(center=self.pos)
        self._layer = 5

    def _create_surface(self):
        surf = pygame.Surface((30, 6), pygame.SRCALPHA)
        # Spear tip
        pygame.draw.polygon(surf, (180, 180, 180), [(28, 3), (22, 1), (22, 5)])
        # Shaft
        pygame.draw.rect(surf, (120, 100, 80), (5, 2, 18, 2))
        # Fletching
        pygame.draw.polygon(surf, (200, 50, 50), [(0, 0), (5, 3), (0, 6)])
        # Rope
        pygame.draw.line(surf, (80, 60, 40), (28, 3), (30, 3), 1)
        return surf

    def update(self, dt):
        self.age += dt
        if self.age >= self.lifetime:
            self.kill()
            return
        self.pos += self.vel * dt
        self.traveled += self.vel.length() * dt
        self.rect.center = (int(self.pos.x), int(self.pos.y))

        # Drag
        self.vel *= 0.999

    def draw(self, surface, offset=(0, 0)):
        rotated = pygame.transform.rotate(self.image, self.angle)
        dest = (int(self.pos.x - offset[0]), int(self.pos.y - offset[1]))
        surface.blit(rotated, rotated.get_rect(center=dest))
