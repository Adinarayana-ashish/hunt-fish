import pygame
import math
import random
from utils import clamp, distance, angle_between, Timer
from settings import (BOSS_KRAKEN_HP, BOSS_KRAKEN_SPEED, BOSS_TENTACLE_COUNT,
                      BOSS_TENTACLE_REACH, BOSS_PHASES, SCREEN_WIDTH, SCREEN_HEIGHT, COLORS)


class Tentacle:
    def __init__(self, origin, length, angle):
        self.origin = pygame.Vector2(origin)
        self.length = length
        self.angle = angle
        self.segments = 10
        self.points = [pygame.Vector2(origin) for _ in range(self.segments)]
        self.target_angle = angle
        self.current_angle = angle
        self.hit_cooldown = 0.0
        self.active = True

    def update(self, dt, target_pos):
        self.hit_cooldown -= dt
        # Aim toward player
        if target_pos:
            desired = angle_between(self.origin, target_pos)
            self.target_angle = desired + math.sin(pygame.time.get_ticks() * 0.001) * 0.3
        self.current_angle += (self.target_angle - self.current_angle) * 2 * dt

        # Update segment positions
        for i in range(self.segments):
            t = i / self.segments
            seg_angle = self.current_angle + math.sin(t * math.pi * 3 +
                       pygame.time.get_ticks() * 0.002) * 0.4
            dist = t * self.length
            if i == 0:
                self.points[i] = pygame.Vector2(self.origin)
            else:
                self.points[i] = self.points[i - 1] + pygame.Vector2(
                    math.cos(seg_angle), math.sin(seg_angle)) * (self.length / self.segments)
        # Tip point (beyond last segment for visual)
        self.tip = self.points[-1] + pygame.Vector2(
            math.cos(self.current_angle), math.sin(self.current_angle)) * 10

    def draw(self, surface, offset=(0, 0)):
        if not self.active:
            return
        for i in range(len(self.points) - 1):
            p1 = (int(self.points[i].x - offset[0]), int(self.points[i].y - offset[1]))
            p2 = (int(self.points[i + 1].x - offset[0]), int(self.points[i + 1].y - offset[1]))
            width = max(2, 12 - i)
            alpha = 200 - i * 15
            color = (80 + i * 5, 40 + i * 3, 60 + i * 2)
            pygame.draw.line(surface, color, p1, p2, width)


class KrakenBoss(pygame.sprite.Sprite):
    def __init__(self, level=5):
        super().__init__()
        self.level = level
        self.max_hp = BOSS_KRAKEN_HP + level * 20
        self.hp = self.max_hp
        self.phase = 1
        self.max_phases = BOSS_PHASES
        self.pos = pygame.Vector2(SCREEN_WIDTH // 2, 200)
        self.vel = pygame.Vector2(0, 0)
        self.speed = BOSS_KRAKEN_SPEED + level * 5
        self.angle = 0
        self.time = 0.0
        self._layer = 10

        # Tentacles
        self.tentacles = []
        for i in range(BOSS_TENTACLE_COUNT):
            angle = (i / BOSS_TENTACLE_COUNT) * math.tau
            t = Tentacle(self.pos, BOSS_TENTACLE_REACH, angle)
            self.tentacles.append(t)

        # Attack state machine
        self.attack_timer = 0.0
        self.attack_pattern = 0
        self.attack_cooldown = 2.0
        self.ink_clouds = []
        self.emerging = True
        self.emerged = False
        self.emerged_timer = 1.0
        self.defeated = False
        self.death_timer = 3.0

        # Visual
        self.body_radius = 60
        self.eye_glow = 0.0
        self.image = self._create_surface()
        self.rect = self.image.get_rect(center=self.pos)

    def _create_surface(self):
        size = self.body_radius * 2 + 40
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        cx = cy = size // 2
        r = self.body_radius
        # Body
        pygame.draw.ellipse(surf, (60, 30, 40), (cx - r, cy - r * 0.7, r * 2, r * 1.4))
        pygame.draw.ellipse(surf, (80, 40, 55), (cx - r + 5, cy - r * 0.7 + 5, r * 2 - 10, r * 1.4 - 10))
        # Eyes
        eye_y = cy - 10
        pygame.draw.circle(surf, (255, 200, 50), (cx - 20, eye_y), 12)
        pygame.draw.circle(surf, (255, 200, 50), (cx + 20, eye_y), 12)
        pygame.draw.circle(surf, (0, 0, 0), (cx - 20, eye_y), 6)
        pygame.draw.circle(surf, (0, 0, 0), (cx + 20, eye_y), 6)
        # Mouth
        pygame.draw.ellipse(surf, (40, 20, 30), (cx - 15, cy + 5, 30, 12))
        # Tentacle attachment
        for i in range(8):
            a = (i / 8) * math.tau
            tx = cx + math.cos(a) * r
            ty = cy + math.sin(a) * r * 0.7
            pygame.draw.circle(surf, (50, 25, 35), (int(tx), int(ty)), 6)
        return surf

    def update(self, dt, player_pos=None):
        self.time += dt
        if self.defeated:
            self.death_timer -= dt
            if self.death_timer <= 0:
                self.kill()
            return

        # Emerge
        if self.emerging:
            self.emerged_timer -= dt
            self.pos.y = 200 + (1 - self.emerged_timer / 1.0) * (-150)
            if self.emerged_timer <= 0:
                self.emerging = False
                self.emerged = True
            return

        if not self.emerged:
            self.emerged_timer -= dt
            if self.emerged_timer <= 0:
                self.emerged = True
            return

        # Movement
        self.pos.x += math.sin(self.time * 0.5) * self.speed * dt
        self.pos.y += math.cos(self.time * 0.3) * self.speed * 0.3 * dt
        self.pos.x = clamp(self.pos.x, 100, SCREEN_WIDTH - 100)
        self.pos.y = clamp(self.pos.y, 80, 350)

        # Update tentacles
        for t in self.tentacles:
            t.update(dt, player_pos)

        # Attack
        self.attack_cooldown -= dt
        if self.attack_cooldown <= 0 and player_pos:
            self.attack_cooldown = random.uniform(2.0, 4.0) / (self.phase * 0.5 + 0.5)
            self.attack_pattern = random.randint(0, 2)
            self._execute_attack(player_pos)

        # Update ink clouds
        for ink in self.ink_clouds[:]:
            ink["timer"] -= dt
            ink["radius"] += 30 * dt
            ink["alpha"] = int(200 * (ink["timer"] / ink["max_time"]))
            if ink["timer"] <= 0:
                self.ink_clouds.remove(ink)

        # Phase check
        hp_ratio = self.hp / self.max_hp
        if hp_ratio < 0.33:
            self.phase = 3
        elif hp_ratio < 0.66:
            self.phase = 2
        else:
            self.phase = 1

        # Eye glow
        self.eye_glow = abs(math.sin(self.time * 2))

        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def _execute_attack(self, player_pos):
        if self.attack_pattern == 0:
            # Tentacle slam
            for t in self.tentacles:
                t.target_angle = angle_between(self.pos, player_pos)
        elif self.attack_pattern == 1:
            # Ink cloud
            self.ink_clouds.append({
                "pos": pygame.Vector2(player_pos),
                "radius": 20,
                "alpha": 200,
                "timer": 3.0,
                "max_time": 3.0,
            })
        elif self.attack_pattern == 2:
            # Spin attack
            for i, t in enumerate(self.tentacles):
                t.target_angle = (self.time * 2 + i * math.tau / len(self.tentacles))

    def draw(self, surface, offset=(0, 0)):
        if self.defeated:
            # Death animation
            alpha = int(255 * (self.death_timer / 3.0))
            if alpha <= 0:
                return
        else:
            alpha = 255

        # Draw ink clouds
        for ink in self.ink_clouds:
            ink_surf = pygame.Surface((int(ink["radius"] * 2), int(ink["radius"] * 2)), pygame.SRCALPHA)
            pygame.draw.circle(ink_surf, (10, 10, 40, min(ink["alpha"], 200)),
                             (int(ink["radius"]), int(ink["radius"])), int(ink["radius"]))
            surface.blit(ink_surf, (int(ink["pos"].x - offset[0] - ink["radius"]),
                                   int(ink["pos"].y - offset[1] - ink["radius"])))

        # Draw tentacles behind body
        for t in self.tentacles:
            t.draw(surface, offset)

        # Body
        px = int(self.pos.x - offset[0])
        py = int(self.pos.y - offset[1])
        if alpha < 255:
            img = self.image.copy()
            img.set_alpha(alpha)
            surface.blit(img, (px - self.body_radius - 20, py - self.body_radius - 20))
        else:
            surface.blit(self.image, (px - self.body_radius - 20, py - self.body_radius - 20))

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.defeated = True
            self.death_timer = 3.0
            return True
        return False

    def check_tentacle_hit(self, point, radius=10):
        for t in self.tentacles:
            for p in t.points:
                if distance(p, point) < radius:
                    return True
        return False
