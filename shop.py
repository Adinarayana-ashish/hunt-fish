from settings import UPGRADES


class ShopManager:
    def __init__(self, save_data=None):
        self.save_data = save_data or {}
        self.player_data = self.save_data.get("player", {})
        self.upgrades = self.save_data.setdefault("upgrades", {})

    def get_level(self, key):
        return self.upgrades.get(key, 0)

    def get_cost(self, key):
        level = self.get_level(key)
        info = UPGRADES.get(key)
        if not info or level >= info["max_level"]:
            return None
        return info["base_cost"] * (level + 1)

    def can_afford(self, key, coins):
        cost = self.get_cost(key)
        if cost is None:
            return False
        return coins >= cost

    def buy(self, key):
        info = UPGRADES.get(key)
        if not info:
            return False
        level = self.get_level(key)
        if level >= info["max_level"]:
            return False
        cost = self.get_cost(key)
        coins = self.player_data.get("coins", 0)
        if coins < cost:
            return False
        self.player_data["coins"] = coins - cost
        self.upgrades[key] = level + 1
        return True

    def get_effect(self, key):
        level = self.get_level(key)
        info = UPGRADES.get(key)
        if not info:
            return 0
        return level * info["effect_per_level"]

    def get_all_levels(self):
        return dict(self.upgrades)
