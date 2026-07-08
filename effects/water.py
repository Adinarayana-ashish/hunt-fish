import pygame
import math
import random
from utils import clamp, lerp
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT


class WaterSurface:
    def __init__(self, width=SCREEN_WIDTH):
        self.width = width
        self.amplitude = 8
        self.frequency = 0.03
        self.speed = 2.0
        self.time = 0.0
        self.resolution = 4
        self.points = []
        self.surface = pygame.Surface((width, 120), pygame.SRCALPHA)
        self.top_color = (50, 150, 220, 180)
        self.bottom_color = (20, 60, 120, 200)

    def set_weather(self, wave_height, wave_speed):
        self.amplitude = 8 * wave_height
        self.speed = 2.0 * wave_speed

    def update(self, dt):
        self.time += dt * self.speed
        self.points = []
        for x in range(0, self.width + self.resolution, self.resolution):
            y = math.sin((x * self.frequency) + self.time * 2) * self.amplitude
            y += math.sin((x * self.frequency * 0.5) + self.time) * self.amplitude * 0.3
            self.points.append((x, y))

    def draw(self, surface, offset_y=0):
        self.surface.fill((0, 0, 0, 0))
        if len(self.points) < 2:
            return
        offset_y = int(offset_y)
        pts = [(x, y + 30) for x, y in self.points]
        poly = pts + [(self.width, 120), (0, 120)]
        if len(poly) > 2:
            grad = pygame.Surface((self.width, 90), pygame.SRCALPHA)
            for i in range(90):
                t = i / 90
                r = int(lerp(self.top_color[0], self.bottom_color[0], t))
                g = int(lerp(self.top_color[1], self.bottom_color[1], t))
                b = int(lerp(self.top_color[2], self.bottom_color[2], t))
                a = int(lerp(self.top_color[3], self.bottom_color[3], t))
                pygame.draw.line(grad, (r, g, b, a), (0, i), (self.width, i))
            self.surface.blit(grad, (0, 0))
            clip_rect = self.surface.get_rect()
            mask = pygame.Surface((self.width, 90), pygame.SRCALPHA)
            pygame.draw.polygon(mask, (255, 255, 255, 255), pts + [(self.width, 90), (0, 90)])
            self.surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        for i in range(len(self.points) - 1):
            x1, y1 = self.points[i]
            x2, y2 = self.points[i + 1]
            pygame.draw.line(self.surface, self.top_color,
                           (x1, y1 + 30), (x2, y2 + 30), 2)
        surface.blit(self.surface, (0, offset_y))


class Bubble:
    def __init__(self):
        self.pos = pygame.Vector2(random.uniform(0, SCREEN_WIDTH),
                                  random.uniform(200, SCREEN_HEIGHT))
        self.size = random.uniform(2, 6)
        self.speed = random.uniform(20, 50)
        self.wobble = random.uniform(0, math.tau)
        self.wobble_speed = random.uniform(1, 3)
        self.wobble_amp = random.uniform(0.5, 2)
        self.alpha = random.randint(30, 100)

    def update(self, dt):
        self.pos.y -= self.speed * dt
        self.wobble += self.wobble_speed * dt
        self.pos.x += math.sin(self.wobble) * self.wobble_amp
        if self.pos.y < -10:
            self.pos.y = SCREEN_HEIGHT + 10
            self.pos.x = random.uniform(0, SCREEN_WIDTH)

    def draw(self, surface, offset=(0, 0)):
        pos = (int(self.pos.x - offset[0]), int(self.pos.y - offset[1]))
        s = max(1, int(self.size))
        surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, (255, 255, 255, self.alpha), (s, s), s)
        pygame.draw.circle(surf, (255, 255, 255, self.alpha + 30), (s - 1, s - 1), s - 1)
        surface.blit(surf, pos)


class Splash:
    def __init__(self, pos):
        self.pos = pygame.Vector2(pos)
        self.particles = []
        for _ in range(12):
            angle = random.uniform(-math.pi * 0.8, math.pi * 0.2)
            speed = random.uniform(80, 200)
            self.particles.append({
                "pos": pygame.Vector2(pos),
                "vel": pygame.Vector2(math.cos(angle), math.sin(angle)) * speed,
                "life": random.uniform(0.3, 0.8),
                "max_life": random.uniform(0.3, 0.8),
                "size": random.uniform(2, 5),
                "color": (200, 230, 255, 200),
            })

    def update(self, dt):
        self.particles = [p for p in self.particles if p["life"] > 0]
        for p in self.particles:
            p["pos"] += p["vel"] * dt
            p["vel"] *= 0.95
            p["life"] -= dt
            t = max(0, p["life"] / p["max_life"])
            p["size"] *= 0.98
            p["color"] = (200, 230, 255, int(200 * t))

    def draw(self, surface, offset=(0, 0)):
        for p in self.particles:
            px = int(p["pos"].x - offset[0])
            py = int(p["pos"].y - offset[1])
            s = max(1, int(p["size"]))
            surf = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, p["color"], (s, s), s)
            surface.blit(surf, (px, py))

    @property
    def is_dead(self):
        return len(self.particles) == 0
