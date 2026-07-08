import pygame
import math
import random
from utils import clamp, lerp


class Particle:
    __slots__ = ("pos", "vel", "life", "max_life", "color", "size",
                 "start_color", "end_color", "alpha", "active", "shape")

    def __init__(self):
        self.pos = pygame.Vector2(0, 0)
        self.vel = pygame.Vector2(0, 0)
        self.life = 0.0
        self.max_life = 1.0
        self.color = (255, 255, 255)
        self.start_color = (255, 255, 255)
        self.end_color = (0, 0, 0)
        self.size = 4.0
        self.alpha = 255
        self.active = False
        self.shape = "circle"

    def activate(self, pos, vel, life, color, size, end_color=None, shape="circle"):
        self.pos.update(pos)
        self.vel.update(vel)
        self.life = life
        self.max_life = life
        self.start_color = color
        self.end_color = end_color or (color[0] // 2, color[1] // 2, color[2] // 2)
        self.size = size
        self.alpha = 255
        self.active = True
        self.shape = shape

    def update(self, dt):
        if not self.active:
            return
        self.pos += self.vel * dt
        self.vel *= 0.98
        self.life -= dt
        self.alpha = clamp(int(255 * (self.life / self.max_life)), 0, 255)
        t = 1.0 - (self.life / self.max_life) if self.max_life > 0 else 1.0
        r = int(lerp(self.start_color[0], self.end_color[0], t))
        g = int(lerp(self.start_color[1], self.end_color[1], t))
        b = int(lerp(self.start_color[2], self.end_color[2], t))
        self.color = (r, g, b)
        if self.life <= 0:
            self.active = False

    def draw(self, surface, offset=(0, 0)):
        if not self.active:
            return
        draw_pos = (int(self.pos.x - offset[0]), int(self.pos.y - offset[1]))
        s = max(1, int(self.size))
        color = (self.color[0], self.color[1], self.color[2], self.alpha)
        try:
            if self.shape == "circle":
                surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (s, s), s)
            elif self.shape == "square":
                surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
                pygame.draw.rect(surf, color, (0, 0, s * 2, s * 2))
            elif self.shape == "star":
                surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (s, s), s)
            surface.blit(surf, draw_pos)
        except (ValueError, pygame.error):
            pass


class ParticlePool:
    def __init__(self, capacity=500):
        self.capacity = capacity
        self.particles = [Particle() for _ in range(capacity)]

    def spawn(self, pos, vel, life, color, size, end_color=None, shape="circle"):
        for p in self.particles:
            if not p.active:
                p.activate(pos, vel, life, color, size, end_color, shape)
                return p
        return None

    def spawn_burst(self, pos, count, speed_range, life_range, color, size_range, end_color=None, shape="circle"):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            speed = random.uniform(*speed_range)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            life = random.uniform(*life_range)
            size = random.uniform(*size_range)
            self.spawn(pos, vel, life, color, size, end_color, shape)

    def update(self, dt):
        for p in self.particles:
            p.update(dt)

    def draw(self, surface, offset=(0, 0)):
        for p in self.particles:
            p.draw(surface, offset)

    def active_count(self):
        return sum(1 for p in self.particles if p.active)


class ParticleEmitter:
    def __init__(self, pool, pos, rate=10, lifetime=1.0,
                 speed_range=(20, 60), size_range=(2, 5),
                 color=(255, 255, 255), end_color=None, shape="circle",
                 spread=math.tau):
        self.pool = pool
        self.pos = pos
        self.rate = rate
        self.lifetime = lifetime
        self.speed_range = speed_range
        self.size_range = size_range
        self.color = color
        self.end_color = end_color
        self.shape = shape
        self.spread = spread
        self.accumulator = 0.0
        self.active = True
        self.angle = 0.0

    def update(self, dt):
        if not self.active:
            return
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return
        self.accumulator += self.rate * dt
        while self.accumulator >= 1.0:
            self.accumulator -= 1.0
            angle = self.angle + random.uniform(-self.spread / 2, self.spread / 2)
            speed = random.uniform(*self.speed_range)
            vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            size = random.uniform(*self.size_range)
            self.pool.spawn(pygame.Vector2(self.pos),
                           vel, random.uniform(0.3, 0.8),
                           self.color, size, self.end_color, self.shape)
