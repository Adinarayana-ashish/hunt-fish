import json
import os
from pathlib import Path

# ── Screen ──────────────────────────────────────────────────────────────
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
TARGET_FPS = 60
TITLE = "Fish Hunter Pro"
ICON_SIZE = (32, 32)

# ── Colors ───────────────────────────────────────────────────────────────
COLORS = {
    "WHITE":          (255, 255, 255),
    "BLACK":          (0, 0, 0),
    "RED":            (255, 50, 50),
    "GREEN":          (50, 255, 50),
    "BLUE":           (50, 130, 255),
    "DARK_BLUE":      (10, 40, 80),
    "DEEP_BLUE":      (5, 20, 50),
    "SKY_BLUE":       (135, 206, 235),
    "LIGHT_BLUE":     (100, 180, 255),
    "YELLOW":         (255, 220, 50),
    "GOLD":           (255, 215, 0),
    "ORANGE":         (255, 140, 40),
    "PURPLE":         (180, 60, 220),
    "PINK":           (255, 100, 180),
    "BROWN":          (139, 69, 19),
    "GRAY":           (128, 128, 128),
    "LIGHT_GRAY":     (200, 200, 200),
    "DARK_GRAY":      (60, 60, 60),
    "CYAN":           (0, 255, 255),
    "TRANSPARENT":    (0, 0, 0, 0),
}

# ── Player ───────────────────────────────────────────────────────────────
PLAYER_SPEED = 280
PLAYER_ACCELERATION = 600
PLAYER_FRICTION = 0.92
PLAYER_MAX_HEALTH = 100
PLAYER_MAX_OXYGEN = 100
OXYGEN_DRAIN_RATE = 3.0
OXYGEN_REGEN_RATE = 8.0
STAMINA_MAX = 100
STAMINA_DRAIN = 20.0
STAMINA_REGEN = 10.0
PLAYER_SURFACE_DEPTH = 50
HARPOON_MAX = 10
HARPOON_RELOAD_TIME = 1.5

# ── Boat ─────────────────────────────────────────────────────────────────
BOAT_WIDTH = 80
BOAT_HEIGHT = 30

# ── Fish ─────────────────────────────────────────────────────────────────
FISH_TYPES = {
    "goldfish": {
        "name": "Goldfish",
        "speed": (80, 140),
        "hp": 1,
        "value": 5,
        "size": (20, 12),
        "color": (255, 180, 50),
        "color2": (255, 220, 100),
        "ai": "darting",
        "school_size": (5, 8),
        "depth_range": (60, 300),
        "xp": 10,
    },
    "tuna": {
        "name": "Tuna",
        "speed": (60, 90),
        "hp": 2,
        "value": 15,
        "size": (40, 16),
        "color": (50, 80, 180),
        "color2": (80, 120, 220),
        "ai": "patrol",
        "school_size": (2, 4),
        "depth_range": (80, 400),
        "xp": 25,
    },
    "salmon": {
        "name": "Salmon",
        "speed": (70, 110),
        "hp": 3,
        "value": 20,
        "size": (36, 14),
        "color": (200, 100, 100),
        "color2": (220, 140, 130),
        "ai": "upstream",
        "school_size": (3, 5),
        "depth_range": (60, 350),
        "xp": 35,
    },
    "swordfish": {
        "name": "Swordfish",
        "speed": (120, 180),
        "hp": 4,
        "value": 35,
        "size": (55, 18),
        "color": (130, 150, 200),
        "color2": (160, 180, 230),
        "ai": "charge",
        "school_size": (1, 2),
        "depth_range": (100, 500),
        "xp": 50,
    },
    "shark": {
        "name": "Shark",
        "speed": (100, 150),
        "hp": 8,
        "value": 50,
        "size": (60, 25),
        "color": (90, 90, 100),
        "color2": (120, 120, 130),
        "ai": "chase",
        "school_size": (1, 2),
        "depth_range": (100, 600),
        "xp": 80,
        "dangerous": True,
    },
    "golden": {
        "name": "Golden Fish",
        "speed": (150, 220),
        "hp": 3,
        "value": 100,
        "size": (28, 15),
        "color": (255, 215, 0),
        "color2": (255, 255, 150),
        "ai": "flee",
        "school_size": (1, 1),
        "depth_range": (50, 700),
        "xp": 150,
        "rare": True,
    },
}

# ── Enemies ──────────────────────────────────────────────────────────────
ENEMY_TYPES = {
    "jellyfish": {
        "speed": 30,
        "hp": 3,
        "damage": 5,
        "stun_time": 2.0,
        "size": (30, 35),
        "color": (180, 80, 220),
        "color2": (220, 140, 255),
        "depth_range": (100, 500),
    },
    "sea_mine": {
        "speed": 0,
        "hp": 1,
        "damage": 25,
        "explosion_radius": 120,
        "size": (24, 24),
        "color": (60, 60, 60),
        "color2": (200, 50, 50),
        "depth_range": (150, 600),
    },
}

# ── Boss ─────────────────────────────────────────────────────────────────
BOSS_KRAKEN_HP = 200
BOSS_KRAKEN_SPEED = 80
BOSS_TENTACLE_COUNT = 6
BOSS_TENTACLE_REACH = 300
BOSS_INK_CLOUD_DURATION = 5.0
BOSS_PHASES = 3

# ── Upgrades ─────────────────────────────────────────────────────────────
UPGRADES = {
    "harpoon_power":  {"name": "Harpoon Power",  "max_level": 5, "base_cost": 50,  "effect_per_level": 1,   "desc": "+1 damage per level"},
    "boat_speed":     {"name": "Boat Speed",     "max_level": 5, "base_cost": 40,  "effect_per_level": 0.2, "desc": "+20% speed per level"},
    "harpoon_cap":    {"name": "Extra Harpoons", "max_level": 5, "base_cost": 60,  "effect_per_level": 2,   "desc": "+2 harpoons per level"},
    "engine_power":   {"name": "Engine Power",   "max_level": 5, "base_cost": 50,  "effect_per_level": 0.3, "desc": "+30% accel per level"},
    "reload_speed":   {"name": "Reload Speed",   "max_level": 5, "base_cost": 45,  "effect_per_level": 0.15,"desc": "-15% reload per level"},
    "oxygen_tank":    {"name": "Oxygen Tank",    "max_level": 5, "base_cost": 35,  "effect_per_level": 30,  "desc": "+30s oxygen per level"},
    "sonar":          {"name": "Sonar",           "max_level": 3, "base_cost": 75,  "effect_per_level": 0,   "desc": "Reveal hidden fish"},
    "magnet":         {"name": "Coin Magnet",     "max_level": 3, "base_cost": 80,  "effect_per_level": 60,  "desc": "+60px collect range"},
}

# ── Level / Biomes ───────────────────────────────────────────────────────
BIOMES = {
    "coral_reef": {
        "name": "Coral Reef",
        "water_color": (30, 120, 180),
        "water_top": (50, 160, 220),
        "ground_color": (200, 160, 100),
        "fog_color": None,
        "ambient_light": 1.0,
        "wave_speed": 1.0,
        "fish_spawn_rate": 1.0,
        "enemy_spawn_rate": 0.0,
    },
    "deep_ocean": {
        "name": "Deep Ocean",
        "water_color": (10, 50, 120),
        "water_top": (20, 80, 160),
        "ground_color": (60, 40, 80),
        "fog_color": (5, 20, 60),
        "ambient_light": 0.7,
        "wave_speed": 1.3,
        "fish_spawn_rate": 1.2,
        "enemy_spawn_rate": 0.3,
    },
    "kelp_forest": {
        "name": "Kelp Forest",
        "water_color": (20, 100, 60),
        "water_top": (40, 140, 80),
        "ground_color": (80, 60, 30),
        "fog_color": (10, 50, 30),
        "ambient_light": 0.5,
        "wave_speed": 0.8,
        "fish_spawn_rate": 1.5,
        "enemy_spawn_rate": 0.5,
    },
    "abyssal_trench": {
        "name": "Abyssal Trench",
        "water_color": (5, 10, 40),
        "water_top": (10, 20, 60),
        "ground_color": (30, 20, 40),
        "fog_color": (3, 5, 20),
        "ambient_light": 0.3,
        "wave_speed": 1.5,
        "fish_spawn_rate": 0.8,
        "enemy_spawn_rate": 0.8,
    },
    "golden_depths": {
        "name": "Golden Depths",
        "water_color": (40, 30, 10),
        "water_top": (80, 60, 20),
        "ground_color": (100, 80, 30),
        "fog_color": (30, 20, 5),
        "ambient_light": 0.8,
        "wave_speed": 1.0,
        "fish_spawn_rate": 1.5,
        "enemy_spawn_rate": 0.4,
    },
    "ice_biome": {
        "name": "Frozen Trench",
        "water_color": (30, 80, 120),
        "water_top": (50, 130, 180),
        "ground_color": (180, 200, 220),
        "fog_color": (40, 60, 80),
        "ambient_light": 0.9,
        "wave_speed": 0.6,
        "fish_spawn_rate": 0.9,
        "enemy_spawn_rate": 0.6,
    },
    "volcano_biome": {
        "name": "Volcano Depths",
        "water_color": (60, 20, 10),
        "water_top": (100, 40, 20),
        "ground_color": (80, 40, 20),
        "fog_color": (40, 10, 5),
        "ambient_light": 0.6,
        "wave_speed": 1.4,
        "fish_spawn_rate": 0.7,
        "enemy_spawn_rate": 1.0,
    },
}

BIOME_ORDER = ["coral_reef", "deep_ocean", "kelp_forest", "abyssal_trench",
               "golden_depths", "ice_biome", "volcano_biome"]

BOSS_LEVELS = {5, 10, 15, 20, 25, 30, 35, 40, 45, 50}

# ── Weather ──────────────────────────────────────────────────────────────
WEATHER_TYPES = {
    "sunny": {"name": "Sunny", "visibility": 1.0, "wave_height": 0.5, "particle_rate": 0},
    "rain":  {"name": "Rain",  "visibility": 0.6, "wave_height": 1.2, "particle_rate": 30},
    "fog":   {"name": "Fog",   "visibility": 0.4, "wave_height": 0.3, "particle_rate": 0},
    "storm": {"name": "Storm", "visibility": 0.3, "wave_height": 2.0, "particle_rate": 60},
}

# ── Achievements ─────────────────────────────────────────────────────────
ACHIEVEMENTS = {
    "first_fish":       {"name": "First Catch",      "desc": "Catch your first fish",            "icon": "fish"},
    "fish_50":          {"name": "Fisherman",         "desc": "Catch 50 fish",                   "icon": "fish"},
    "fish_500":         {"name": "Master Fisher",     "desc": "Catch 500 fish",                  "icon": "fish"},
    "coins_100":        {"name": "Coin Collector",    "desc": "Collect 100 coins",               "icon": "coin"},
    "coins_1000":       {"name": "Wealthy",           "desc": "Collect 1000 coins",              "icon": "coin"},
    "coins_10000":      {"name": "Millionaire",       "desc": "Collect 10000 coins",             "icon": "coin"},
    "boss_1":           {"name": "Kraken Slayer",     "desc": "Defeat the Kraken once",          "icon": "boss"},
    "boss_5":           {"name": "Legendary Hunter",  "desc": "Defeat the Kraken 5 times",       "icon": "boss"},
    "golden_fish":      {"name": "Golden Touch",      "desc": "Catch the legendary golden fish", "icon": "star"},
    "combo_5":          {"name": "On Fire",           "desc": "Reach a 5x combo",                "icon": "fire"},
    "combo_20":         {"name": "Unstoppable",       "desc": "Reach a 20x combo",               "icon": "fire"},
    "survive_10":       {"name": "Survivor",          "desc": "Survive 10 levels",               "icon": "heart"},
    "survive_25":       {"name": "Veteran",           "desc": "Survive 25 levels",               "icon": "heart"},
    "perfect_boss":     {"name": "No Hit Boss",       "desc": "Defeat a boss without taking damage", "icon": "shield"},
    "treasure_10":      {"name": "Treasure Hunter",   "desc": "Collect 10 treasure chests",      "icon": "chest"},
}

# ── Gameplay constants ───────────────────────────────────────────────────
TREASURE_CHEST_VALUE = (50, 200)
TREASURE_CHEST_SPAWN_CHANCE = 0.001
COMBO_TIMEOUT = 5.0
CRITICAL_CHANCE = 0.1
CRITICAL_MULTIPLIER = 2.5
DIVE_MAX_DEPTH = 800
HARPOON_SPEED = 600
HARPOON_LIFETIME = 3.0
HARPOON_DAMAGE = 1
DAMAGE_NUMBER_FLOAT_TIME = 1.0
DAMAGE_NUMBER_RISE_SPEED = 60

# ── Save / Config paths ──────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
SAVE_DIR = BASE_DIR / "saves"
SAVE_FILE = SAVE_DIR / "save.json"
CONFIG_FILE = BASE_DIR / "config.json"

# ── Config defaults ──────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "fullscreen": False,
    "screen_width": SCREEN_WIDTH,
    "screen_height": SCREEN_HEIGHT,
    "master_volume": 0.7,
    "sfx_volume": 0.8,
    "music_volume": 0.5,
    "show_fps": True,
    "vibration": True,
    "screen_shake": True,
}


def load_config():
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
            for k in DEFAULT_CONFIG:
                cfg.setdefault(k, DEFAULT_CONFIG[k])
            return cfg
    except (json.JSONDecodeError, OSError):
        pass
    return dict(DEFAULT_CONFIG)


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except OSError:
        pass
