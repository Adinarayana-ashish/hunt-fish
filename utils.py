import json
import math
import random
from pathlib import Path
from settings import SAVE_DIR, SAVE_FILE


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(val, lo, hi):
    return max(lo, min(hi, val))


def ease_out_cubic(t):
    return 1 - (1 - t) ** 3


def ease_in_out_quad(t):
    return 2 * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 2 / 2


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def angle_between(a, b):
    return math.atan2(b[1] - a[1], b[0] - a[0])


def normalize(v):
    mag = math.hypot(v[0], v[1])
    if mag == 0:
        return (0, 0)
    return (v[0] / mag, v[1] / mag)


def point_in_rect(px, py, rect):
    return rect.left <= px <= rect.right and rect.top <= py <= rect.bottom


# ── Timer ────────────────────────────────────────────────────────────────
class Timer:
    def __init__(self, duration=0.0):
        self.duration = duration
        self.elapsed = 0.0
        self.finished = False
        self.paused = False

    def update(self, dt):
        if self.paused or self.finished:
            return
        self.elapsed += dt
        if self.elapsed >= self.duration:
            self.finished = True

    def reset(self, duration=None):
        if duration is not None:
            self.duration = duration
        self.elapsed = 0.0
        self.finished = False
        self.paused = False

    def progress(self):
        if self.duration == 0:
            return 1.0
        return min(self.elapsed / self.duration, 1.0)

    def remaining(self):
        return max(self.duration - self.elapsed, 0.0)


# ── Save / Load ──────────────────────────────────────────────────────────
SAVE_VERSION = 1

DEFAULT_SAVE = {
    "version": SAVE_VERSION,
    "player": {
        "coins": 0,
        "level": 1,
        "experience": 0,
        "health": 100,
        "max_health": 100,
    },
    "upgrades": {k: 0 for k in [
        "harpoon_power", "boat_speed", "harpoon_cap",
        "engine_power", "reload_speed", "oxygen_tank",
        "sonar", "magnet",
    ]},
    "statistics": {
        "fish_caught": 0,
        "bosses_defeated": 0,
        "distance_traveled": 0,
        "coins_collected": 0,
        "harpoons_shot": 0,
        "treasures_found": 0,
        "critical_hits": 0,
        "max_combo": 0,
        "total_score": 0,
        "play_time": 0.0,
    },
    "achievements": [],
    "settings": {},
}


def load_game():
    try:
        if SAVE_FILE.exists():
            with open(SAVE_FILE) as f:
                data = json.load(f)
            data = migrate_save(data)
            return data
    except (json.JSONDecodeError, OSError, KeyError):
        pass
    return dict(DEFAULT_SAVE)


def save_game(data):
    data["version"] = SAVE_VERSION
    try:
        SAVE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = SAVE_FILE.with_suffix(".json.tmp")
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        tmp.replace(SAVE_FILE)
    except OSError:
        pass


def migrate_save(data):
    ver = data.get("version", 0)
    if ver < SAVE_VERSION:
        for k in DEFAULT_SAVE:
            if k not in data:
                data[k] = DEFAULT_SAVE[k]
        for k in DEFAULT_SAVE["player"]:
            data.setdefault("player", {}).setdefault(k, DEFAULT_SAVE["player"][k])
        for k in DEFAULT_SAVE["upgrades"]:
            data.setdefault("upgrades", {}).setdefault(k, 0)
        for k in DEFAULT_SAVE["statistics"]:
            data.setdefault("statistics", {}).setdefault(k, 0)
        data.setdefault("achievements", [])
        data["version"] = SAVE_VERSION
    return data


# ── Achievement System ──────────────────────────────────────────────────
class AchievementSystem:
    def __init__(self):
        self.save_data = load_game()

    def is_unlocked(self, achievement_id):
        return achievement_id in self.save_data.get("achievements", [])

    def unlock(self, achievement_id):
        if not self.is_unlocked(achievement_id):
            self.save_data.setdefault("achievements", []).append(achievement_id)
            save_game(self.save_data)
            return True
        return False

    def check(self, stats):
        from settings import ACHIEVEMENTS
        new_achievements = []
        checks = {
            "first_fish":   lambda s: s.get("fish_caught", 0) >= 1,
            "fish_50":      lambda s: s.get("fish_caught", 0) >= 50,
            "fish_500":     lambda s: s.get("fish_caught", 0) >= 500,
            "coins_100":    lambda s: s.get("coins_collected", 0) >= 100,
            "coins_1000":   lambda s: s.get("coins_collected", 0) >= 1000,
            "coins_10000":  lambda s: s.get("coins_collected", 0) >= 10000,
            "boss_1":       lambda s: s.get("bosses_defeated", 0) >= 1,
            "boss_5":       lambda s: s.get("bosses_defeated", 0) >= 5,
            "golden_fish":  lambda s: s.get("golden_caught", 0) >= 1,
            "combo_5":      lambda s: s.get("max_combo", 0) >= 5,
            "combo_20":     lambda s: s.get("max_combo", 0) >= 20,
            "survive_10":   lambda s: s.get("level", 1) >= 10,
            "survive_25":   lambda s: s.get("level", 1) >= 25,
            "treasure_10":  lambda s: s.get("treasures_found", 0) >= 10,
        }
        for ach_id, condition in checks.items():
            if not self.is_unlocked(ach_id) and condition(stats):
                if self.unlock(ach_id):
                    new_achievements.append(ach_id)
        return new_achievements
