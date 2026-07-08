import pygame
import math
import random
from utils import clamp, distance, angle_between
from settings import FISH_TYPES, SCREEN_WIDTH, SCREEN_HEIGHT


# ── Strategy Pattern: Fish AI ────────────────────────────────────────────
class FishAI:
    def update(self, fish, dt, player_pos, obstacles):
        raise NotImplementedError

    def on_spawn(self, fish):
        pass


class DartingAI(FishAI):
    def __init__(self):
        self.direction = pygame.Vector2(random.choice([-1, 1]), random.uniform(-0.3, 0.3))
        self.dart_timer = 0.0
        self.rest_timer = random.uniform(0.5, 2.0)

    def update(self, fish, dt, player_pos, obstacles):
        self.dart_timer -= dt
        speed = fish.speed
        if self.dart_timer <= 0:
            self.direction = pygame.Vector2(random.choice([-1, 1]),
                                           random.uniform(-0.5, 0.5)).normalize()
            self.dart_timer = random.uniform(0.3, 0.8)
            speed *= 1.5
        fish.vel = self.direction * speed
        if fish.pos.x < 50:
            self.direction.x = abs(self.direction.x)
        elif fish.pos.x > SCREEN_WIDTH - 50:
            self.direction.x = -abs(self.direction.x)


class PatrolAI(FishAI):
    def __init__(self):
        self.direction = pygame.Vector2(1, 0)
        self.change_timer = random.uniform(1.0, 3.0)

    def update(self, fish, dt, player_pos, obstacles):
        self.change_timer -= dt
        if self.change_timer <= 0:
            self.change_timer = random.uniform(1.0, 3.0)
            self.direction.y = random.uniform(-0.2, 0.2)
        fish.vel = self.direction * fish.speed
        if fish.pos.x > SCREEN_WIDTH - 30:
            self.direction.x = -1
        elif fish.pos.x < 30:
            self.direction.x = 1


class UpstreamAI(FishAI):
    def __init__(self):
        self.direction = pygame.Vector2(0, -1)
        self.jump_timer = random.uniform(2.0, 5.0)
        self.jumping = False
        self.jump_vel = 0

    def update(self, fish, dt, player_pos, obstacles):
        self.jump_timer -= dt
        if self.jumping:
            fish.pos.y += self.jump_vel * dt
            self.jump_vel += 600 * dt
            if fish.pos.y > fish.base_y:
                fish.pos.y = fish.base_y
                self.jumping = False
                self.jump_timer = random.uniform(2.0, 5.0)
            return
        if self.jump_timer <= 0 and fish.pos.y < 400:
            self.jumping = True
            self.jump_vel = -300
            return
        fish.vel = self.direction * fish.speed
        if fish.pos.y < 100:
            self.direction.y = 0.5
        elif fish.pos.y > fish.base_y:
            self.direction.y = -0.5
            if random.random() < 0.01:
                self.direction.x = random.choice([-1, 1])
        if fish.pos.x < 30:
            self.direction.x = 1
        elif fish.pos.x > SCREEN_WIDTH - 30:
            self.direction.x = -1

    def on_spawn(self, fish):
        fish.base_y = fish.pos.y


class ChargeAI(FishAI):
    def __init__(self):
        self.state = "patrol"
        self.charge_timer = 0.0
        self.cooldown = 0.0
        self.direction = pygame.Vector2(1, 0)

    def update(self, fish, dt, player_pos, obstacles):
        self.cooldown -= dt
        dist = distance(fish.pos, player_pos) if player_pos else 999
        if dist < 350 and self.cooldown <= 0:
            self.state = "charge"
            self.charge_timer = 0.8
            self.cooldown = 2.0
        if self.state == "charge":
            if player_pos:
                angle = angle_between(fish.pos, player_pos)
                fish.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * fish.speed * 2
            self.charge_timer -= dt
            if self.charge_timer <= 0:
                self.state = "retreat"
                self.charge_timer = 0.5
        elif self.state == "retreat":
            if player_pos:
                angle = angle_between(fish.pos, player_pos) + math.pi
                fish.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * fish.speed
            self.charge_timer -= dt
            if self.charge_timer <= 0:
                self.state = "patrol"
        else:
            fish.pos += self.direction * fish.speed * dt
            if fish.pos.x < 30:
                self.direction.x = 1
            elif fish.pos.x > SCREEN_WIDTH - 30:
                self.direction.x = -1


class ChaseAI(FishAI):
    def __init__(self):
        self.attack_cooldown = 0.0
        self.base_y = 0

    def update(self, fish, dt, player_pos, obstacles):
        self.attack_cooldown -= dt
        if player_pos:
            dist = distance(fish.pos, player_pos)
            if dist < 500:
                angle = angle_between(fish.pos, player_pos)
                fish.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * fish.speed
            elif fish.pos.y > self.base_y:
                fish.vel = pygame.Vector2(0, -1) * fish.speed
            else:
                fish.vel = pygame.Vector2(0, 1) * fish.speed * 0.3

    def on_spawn(self, fish):
        self.base_y = fish.pos.y


class FleeAI(FishAI):
    def __init__(self):
        self.dir = pygame.Vector2(1, 0)
        self.timer = 0.0

    def update(self, fish, dt, player_pos, obstacles):
        self.timer -= dt
        if player_pos and distance(fish.pos, player_pos) < 400:
            angle = angle_between(fish.pos, player_pos) + math.pi
            fish.vel = pygame.Vector2(math.cos(angle), math.sin(angle)) * fish.speed * 1.8
            fish.vel.x += math.sin(pygame.time.get_ticks() * 0.005) * 50
        else:
            if self.timer <= 0:
                self.dir = pygame.Vector2(random.choice([-1, 1]),
                                        random.uniform(-0.5, 0.5)).normalize()
                self.timer = random.uniform(0.5, 1.5)
            fish.vel = self.dir * fish.speed * 0.7
        if fish.pos.x < 30:
            fish.vel.x = abs(fish.vel.x)
        elif fish.pos.x > SCREEN_WIDTH - 30:
            fish.vel.x = -abs(fish.vel.x)


AI_STRATEGIES = {
    "darting": DartingAI(),
    "patrol": PatrolAI(),
    "upstream": UpstreamAI(),
    "charge": ChargeAI(),
    "chase": ChaseAI(),
    "flee": FleeAI(),
}


# ── Fish Base ─────────────────────────────────────────────────────────────
class Fish(pygame.sprite.Sprite):
    def __init__(self, fish_type, level=1):
        super().__init__()
        info = FISH_TYPES[fish_type]
        self.fish_type = fish_type
        self.info = info
        self.level = level

        # Stats from settings
        speed_range = info["speed"]
        self.base_speed = random.uniform(*speed_range) * (1 + level * 0.05)
        self.speed = self.base_speed
        self.hp = info["hp"] + max(0, level // 5)
        self.max_hp = self.hp
        self.value = info["value"] + level * 2
        self.xp = info.get("xp", self.value)

        # Position
        w, h = info["size"]
        self.width = w
        self.height = h
        depth_lo, depth_hi = info["depth_range"]
        depth = random.randint(depth_lo, depth_hi)
        self.pos = pygame.Vector2(random.uniform(50, SCREEN_WIDTH - 50), depth)
        self.vel = pygame.Vector2(0, 0)
        self.visual_y = depth

        # AI
        ai_name = info["ai"]
        self.ai = AI_STRATEGIES[ai_name]
        self.ai.on_spawn(self)

        # Visual
        self.direction = 1
        self.flip_timer = 0.0
        self.tail_wag = 0.0
        self.caught = False
        self.rare = info.get("rare", False)
        self.dangerous = info.get("dangerous", False)

        # Collision
        self._layer = 3
        self.image = self._create_surface()
        self.rect = self.image.get_rect(center=(self.pos.x, self.visual_y))

    def _create_surface(self):
        color = self.info["color"]
        color2 = self.info.get("color2", color)
        w, h = self.width, self.height
        surf = pygame.Surface((w + 10, h + 10), pygame.SRCALPHA)

        # Body
        body = pygame.Surface((w, h), pygame.SRCALPHA)
        body_rect = pygame.draw.ellipse(body, color, (0, 0, w, h))
        # Belly
        belly = pygame.Surface((w * 0.6, h * 0.5), pygame.SRCALPHA)
        pygame.draw.ellipse(belly, color2, (0, 0, w * 0.6, h * 0.5))
        body.blit(belly, (w * 0.2, h * 0.4))
        # Tail
        tail_pts = [(w, h // 2), (w + 8, h // 2 - 6), (w + 8, h // 2 + 6)]
        pygame.draw.polygon(body, color, tail_pts)
        # Eye
        eye_color = (255, 255, 255) if not self.dangerous else (255, 50, 50)
        pygame.draw.circle(body, eye_color, (w - 6, h // 2 - 2), 2)
        if self.dangerous:
            pygame.draw.circle(body, (0, 0, 0), (w - 6, h // 2 - 2), 1)
        # Special: golden glow
        if self.rare:
            glow = pygame.Surface((w + 8, h + 8), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (255, 215, 0, 40), (2, 2, w + 4, h + 4))
            surf.blit(glow, (0, 0))
        surf.blit(body, (5, 5))
        return surf

    def update(self, dt, player_pos=None, obstacles=None):
        self.ai.update(self, dt, player_pos, obstacles)

        # Apply velocity
        self.pos += self.vel * dt

        # Depth vertical oscillation
        self.visual_y = self.pos.y + math.sin(pygame.time.get_ticks() * 0.001 * self.base_speed * 0.01) * 5

        # Direction
        if abs(self.vel.x) > 5:
            self.direction = 1 if self.vel.x > 0 else -1
        if self.pos.x < -50:
            self.pos.x = SCREEN_WIDTH + 50
        elif self.pos.x > SCREEN_WIDTH + 50:
            self.pos.x = -50

        self.tail_wag += dt * 5
        self.rect.center = (int(self.pos.x), int(self.visual_y))

    def draw(self, surface, offset=(0, 0)):
        px = self.pos.x - offset[0]
        py = self.visual_y - offset[1]
        if px < -100 or px > SCREEN_WIDTH + 100:
            return
        # Shadow
        shadow = pygame.Surface((self.width * 0.8, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 40), (0, 0, self.width * 0.8, 6))
        surface.blit(shadow, (int(px - self.width * 0.4), int(py + self.height * 0.6)))

        # Fish
        img = self.image
        if self.direction < 0:
            img = pygame.transform.flip(img, True, False)
        dest = img.get_rect(center=(int(px), int(py)))
        surface.blit(img, dest)

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.caught = True
            return True
        return False


# ── Fish Spawner ──────────────────────────────────────────────────────────
class FishSpawner:
    def __init__(self, level=1, biome="coral_reef"):
        self.level = level
        self.biome = biome
        self.spawn_timer = 0.0
        self.spawn_interval = 2.0
        self.max_fish = 20 + level * 3

    def get_available_types(self):
        types = ["goldfish", "tuna"]
        if self.level >= 2:
            types.append("salmon")
        if self.level >= 3:
            types.append("swordfish")
        if self.level >= 4:
            types.append("shark")
        if self.level >= 10 and random.random() < 0.01:
            types.append("golden")
        return types

    def update(self, dt, fish_group, player_pos):
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and len(fish_group) < self.max_fish:
            self.spawn_timer = self.spawn_interval
            ftype = random.choice(self.get_available_types())
            fish = Fish(ftype, self.level)
            fish_group.add(fish)
            # Spawn school
            info = FISH_TYPES[ftype]
            school = random.randint(*info["school_size"])
            for _ in range(school - 1):
                f = Fish(ftype, self.level)
                f.pos = fish.pos + pygame.Vector2(random.uniform(-40, 40),
                                                  random.uniform(-20, 20))
                fish_group.add(f)
