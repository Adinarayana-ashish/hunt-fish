import pygame
import math
from utils import clamp, Timer
from settings import (COLORS, PLAYER_SPEED, PLAYER_ACCELERATION, PLAYER_FRICTION,
                      PLAYER_MAX_HEALTH, PLAYER_MAX_OXYGEN, OXYGEN_DRAIN_RATE,
                      OXYGEN_REGEN_RATE, STAMINA_MAX, STAMINA_DRAIN, STAMINA_REGEN,
                       BOAT_WIDTH, BOAT_HEIGHT, HARPOON_MAX, HARPOON_RELOAD_TIME,
                       SCREEN_WIDTH, SCREEN_HEIGHT, PLAYER_SURFACE_DEPTH)


class Boat(pygame.sprite.Sprite):
    def __init__(self, pos=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)):
        super().__init__()
        self.pos = pygame.Vector2(pos)
        self.vel = pygame.Vector2(0, 0)
        self.angle = 0
        self.target_angle = 0
        self.speed = PLAYER_SPEED
        self.acceleration = PLAYER_ACCELERATION
        self.friction = PLAYER_FRICTION
        self.width = BOAT_WIDTH
        self.height = BOAT_HEIGHT
        self.depth = -PLAYER_SURFACE_DEPTH
        self.surface_depth = 50

        # Stats
        self.health = PLAYER_MAX_HEALTH
        self.max_health = PLAYER_MAX_HEALTH
        self.oxygen = PLAYER_MAX_OXYGEN
        self.max_oxygen = PLAYER_MAX_OXYGEN
        self.stamina = STAMINA_MAX
        self.max_stamina = STAMINA_MAX

        # Harpoons
        self.harpoons = HARPOON_MAX
        self.max_harpoons = HARPOON_MAX
        self.reload_time = HARPOON_RELOAD_TIME
        self.reload_timer = Timer(0)
        self.reloading = False
        self.harpoon_damage = 1

        # Upgrades
        self.speed_mult = 1.0
        self.accel_mult = 1.0
        self.reload_mult = 1.0
        self.magnet_range = 0
        self.has_sonar = False

        # State
        self.is_diving = False
        self.stunned = False
        self.stun_timer = 0.0
        self.sprint_active = False
        self.oxygen_drain_mult = 1.0

        # Visual
        self.image = self._create_surface()
        self.rect = self.image.get_rect(center=self.pos)
        self.shadow_offset = pygame.Vector2(5, 5)

    def _create_surface(self):
        surf = pygame.Surface((self.width, self.height + 10), pygame.SRCALPHA)
        w, h = self.width, self.height
        # Hull
        hull_color = (120, 80, 40)
        pts = [(5, h), (w - 5, h), (w - 10, h - 10), (10, h - 10)]
        pygame.draw.polygon(surf, hull_color, pts)
        pygame.draw.polygon(surf, (90, 60, 30), pts, 2)
        # Deck
        pygame.draw.rect(surf, (150, 120, 80), (10, h - 15, w - 20, 10))
        # Cabin
        cabin_color = (180, 160, 130)
        pygame.draw.rect(surf, cabin_color, (w // 2 - 12, h - 25, 24, 15))
        pygame.draw.rect(surf, (200, 220, 255), (w // 2 - 8, h - 22, 8, 8))
        pygame.draw.rect(surf, (200, 220, 255), (w // 2 + 1, h - 22, 8, 8))
        # Mast
        pygame.draw.line(surf, (80, 60, 40), (w // 2, h - 8), (w // 2, h - 45), 2)
        # Flag
        flag_pts = [(w // 2, h - 45), (w // 2 + 15, h - 40), (w // 2, h - 35)]
        pygame.draw.polygon(surf, (200, 50, 50), flag_pts)
        return surf

    def apply_upgrades(self, upgrades):
        if "boat_speed" in upgrades:
            self.speed_mult = 1.0 + upgrades["boat_speed"] * 0.2
        if "engine_power" in upgrades:
            self.accel_mult = 1.0 + upgrades["engine_power"] * 0.3
        if "harpoon_cap" in upgrades:
            self.max_harpoons = HARPOON_MAX + upgrades["harpoon_cap"] * 2
        if "reload_speed" in upgrades:
            self.reload_mult = 1.0 - upgrades["reload_speed"] * 0.15
        if "oxygen_tank" in upgrades:
            self.oxygen_drain_mult = max(0.2, 1.0 - upgrades["oxygen_tank"] * 0.15)
        if "harpoon_power" in upgrades:
            self.harpoon_damage = 1 + upgrades["harpoon_power"]
        if "magnet" in upgrades:
            self.magnet_range = upgrades["magnet"] * 60
        if "sonar" in upgrades and upgrades["sonar"] > 0:
            self.has_sonar = True
        self.speed = PLAYER_SPEED * self.speed_mult
        self.acceleration = PLAYER_ACCELERATION * self.accel_mult
        self.reload_time = HARPOON_RELOAD_TIME * self.reload_mult

    def handle_input(self, keys, dt):
        if self.stunned:
            return
        dx = dy = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1
        if dx != 0 or dy != 0:
            length = math.hypot(dx, dy)
            dx /= length
            dy /= length
        self.vel.x += dx * self.acceleration * dt
        self.vel.y += dy * self.acceleration * dt

        # Sprint
        if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.stamina > 0:
            self.sprint_active = True
            self.stamina -= STAMINA_DRAIN * dt
            self.vel.x *= 1.5
            self.vel.y *= 1.5
            if "sprint" in keys:  # placeholder for external sprint bind
                pass
        else:
            self.sprint_active = False
            self.stamina = min(self.max_stamina, self.stamina + STAMINA_REGEN * dt)

    def update(self, dt):
        # Apply friction
        self.vel *= self.friction ** (dt * 60)
        if abs(self.vel.x) < 1:
            self.vel.x = 0
        if abs(self.vel.y) < 1:
            self.vel.y = 0

        self.pos += self.vel * dt

        # Angle
        if self.vel.length() > 5:
            self.target_angle = math.degrees(math.atan2(-self.vel.x, -self.vel.y))
        self.angle = lerp_angle(self.angle, self.target_angle, 5 * dt)

        # Reload
        if self.reloading:
            self.reload_timer.update(dt)
            if self.reload_timer.finished:
                self.harpoons = self.max_harpoons
                self.reloading = False

        # Stun
        if self.stunned:
            self.stun_timer -= dt
            if self.stun_timer <= 0:
                self.stunned = False

        # Oxygen
        if self.is_diving:
            self.oxygen -= OXYGEN_DRAIN_RATE * self.oxygen_drain_mult * dt
            if self.oxygen <= 0:
                self.oxygen = 0
                self.health -= 5 * dt
        else:
            self.oxygen = min(self.max_oxygen, self.oxygen + OXYGEN_REGEN_RATE * dt)

        # Clamp
        self.oxygen = clamp(self.oxygen, 0, self.max_oxygen)
        self.health = clamp(self.health, 0, self.max_health)
        self.stamina = clamp(self.stamina, 0, self.max_stamina)

        # Update rect
        self.rect.center = (int(self.pos.x), int(self.pos.y))

    def draw(self, surface, offset=(0, 0)):
        # Shadow
        shadow_surf = pygame.Surface((self.width * 0.8, self.height * 0.5), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60),
                          (0, 0, self.width * 0.8, self.height * 0.5))
        shadow_pos = (self.pos.x - offset[0] + self.shadow_offset.x,
                     self.pos.y - offset[1] + self.shadow_offset.y + 40)
        surface.blit(shadow_surf, shadow_pos)

        # Boat
        rotated = pygame.transform.rotate(self.image, self.angle)
        rot_rect = rotated.get_rect(center=(int(self.pos.x - offset[0]),
                                           int(self.pos.y - offset[1])))
        surface.blit(rotated, rot_rect)

    def shoot(self):
        if self.harpoons <= 0 or self.reloading:
            return None
        self.harpoons -= 1
        if self.harpoons <= 0:
            self.reloading = True
            self.reload_timer.reset(self.reload_time)
        return self.pos + pygame.Vector2(0, 0)

    def take_damage(self, amount):
        self.health -= amount
        if self.health < 0:
            self.health = 0

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def stun(self, duration):
        self.stunned = True
        self.stun_timer = duration
        self.vel *= 0.1

    @property
    def alive(self):
        return self.health > 0

    @property
    def can_dive(self):
        return self.oxygen > 0


def lerp_angle(a, b, t):
    diff = b - a
    while diff > 180:
        diff -= 360
    while diff < -180:
        diff += 360
    return a + diff * t
