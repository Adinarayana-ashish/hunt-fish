import random
import math
from settings import (BIOMES, BIOME_ORDER, BOSS_LEVELS, WEATHER_TYPES,
                      SCREEN_WIDTH, SCREEN_HEIGHT, TREASURE_CHEST_VALUE,
                      TREASURE_CHEST_SPAWN_CHANCE)


class LevelManager:
    def __init__(self, start_level=1):
        self.level = start_level
        self.biome_index = 0
        self.current_biome = BIOMES[BIOME_ORDER[0]]
        self.weather = dict(WEATHER_TYPES["sunny"])
        self.weather_timer = 0.0
        self.weather_duration = random.uniform(30, 60)
        self.next_weather_change = random.uniform(15, 40)
        self.difficulty_mult = 1.0
        self.treasure_timer = 0.0
        self.day_night_cycle = 0.0  # 0 = noon, 0.5 = midnight, 1 = noon
        self.day_length = 120.0  # seconds per full cycle
        self.update_biome()

    def update_biome(self):
        biomes_count = len(BIOME_ORDER)
        idx = ((self.level - 1) // 5) % biomes_count
        self.biome_index = idx
        key = BIOME_ORDER[idx] if idx < len(BIOME_ORDER) else BIOME_ORDER[-1]
        self.current_biome = BIOMES[key]
        self.difficulty_mult = 1.0 + (self.level - 1) * 0.1

    def next_level(self):
        self.level += 1
        self.update_biome()
        return self.is_boss_level()

    def is_boss_level(self):
        return self.level in BOSS_LEVELS or (self.level % 5 == 0)

    def update_weather(self, dt):
        self.weather_timer += dt
        self.next_weather_change -= dt
        self.day_night_cycle += dt / self.day_length
        if self.day_night_cycle >= 1.0:
            self.day_night_cycle -= 1.0

        if self.next_weather_change <= 0:
            self.next_weather_change = random.uniform(20, 50)
            weights = {"sunny": 40, "rain": 25, "fog": 20, "storm": 15}
            if self.level >= 10:
                weights["storm"] = 25
            total = sum(weights.values())
            r = random.random() * total
            cumulative = 0
            chosen = "sunny"
            for wtype, w in weights.items():
                cumulative += w
                if r <= cumulative / total:
                    chosen = wtype
                    break
            self.weather = dict(WEATHER_TYPES[chosen])
            self.weather_duration = random.uniform(15, 40)

    def get_ambient_light(self):
        # Day/night factor (1 at noon, 0.3 at midnight)
        day_factor = 0.7 + 0.3 * math.cos(self.day_night_cycle * math.tau)
        biome_light = self.current_biome.get("ambient_light", 1.0)
        weather_vis = self.weather.get("visibility", 1.0)
        return day_factor * biome_light * weather_vis

    def is_raining(self):
        return self.weather.get("visibility", 1.0) < 0.8

    def is_foggy(self):
        return self.weather.get("visibility", 1.0) < 0.5

    def spawn_treasure(self, dt):
        self.treasure_timer += dt * self.difficulty_mult
        if self.treasure_timer >= 30.0:
            self.treasure_timer = 0
            if random.random() < TREASURE_CHEST_SPAWN_CHANCE * 30:
                return {
                    "pos": [random.uniform(50, SCREEN_WIDTH - 50),
                           random.uniform(100, SCREEN_HEIGHT - 50)],
                    "value": random.randint(*TREASURE_CHEST_VALUE),
                    "active": True,
                }
        return None

    def get_spawn_rate_mult(self):
        return self.current_biome.get("fish_spawn_rate", 1.0)

    def get_enemy_rate_mult(self):
        return self.current_biome.get("enemy_spawn_rate", 0.0)


class DailyChallenge:
    def __init__(self):
        random.seed(self._daily_seed())
        self.target_fish = random.sample(list(range(1, 7)), random.randint(2, 4))
        self.target_score = random.randint(500, 2000) + random.randint(0, 5) * 100
        self.time_limit = random.randint(120, 300)
        self.restrictions = []
        if random.random() < 0.3:
            self.restrictions.append("no_bomb")
        if random.random() < 0.2:
            self.restrictions.append("low_visibility")

    def _daily_seed(self):
        import datetime
        today = datetime.date.today()
        return f"{today.year}{today.month:02d}{today.day:02d}"
