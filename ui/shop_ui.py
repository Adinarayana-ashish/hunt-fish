import pygame
from settings import COLORS, UPGRADES, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.buttons import Button
from ui.widgets import Panel, TextDisplay


class ShopUI:
    def __init__(self, game_ref):
        self.game = game_ref
        self.items = []
        self.buttons = []
        self.coins = 0
        self.current_levels = {}
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 20)
        self._create_buttons()

    def _create_buttons(self):
        self.buttons.clear()
        cx = SCREEN_WIDTH // 2
        self.back_btn = Button(
            (cx - 100, SCREEN_HEIGHT - 70, 200, 45),
            "Continue Fishing",
            lambda: self.game.resume_game(),
            color=(30, 80, 30),
            hover_color=(50, 140, 50),
            font_size=22,
        )
        self.buttons.append(self.back_btn)
        self.shop_buttons = []

    def enter(self, coins, levels):
        self.coins = coins
        self.current_levels = dict(levels)
        self._create_shop_items()

    def _create_shop_items(self):
        self.shop_buttons.clear()
        self.items.clear()
        cx = SCREEN_WIDTH // 2
        y = 150
        for key, info in UPGRADES.items():
            level = self.current_levels.get(key, 0)
            maxed = level >= info["max_level"]
            cost = info["base_cost"] * (level + 1)
            item = {
                "key": key,
                "name": info["name"],
                "desc": info["desc"],
                "level": level,
                "max_level": info["max_level"],
                "cost": cost,
                "maxed": maxed,
            }
            self.items.append(item)

            def make_cb(k=key):
                def cb():
                    self.game.buy_upgrade(k)
                return cb

            if not maxed and cost <= self.coins:
                btn = Button(
                    (cx + 150, y, 90, 35),
                    f"${cost}",
                    make_cb(),
                    color=(40, 80, 40),
                    hover_color=(60, 140, 60),
                    font_size=18,
                )
            else:
                label = "MAX" if maxed else "---"
                btn = Button(
                    (cx + 150, y, 90, 35),
                    label,
                    None,
                    color=(40, 40, 40),
                    hover_color=(40, 40, 40),
                    font_size=18,
                )
                btn.active = not maxed and cost <= self.coins
            self.shop_buttons.append(btn)
            y += 55

    def handle_event(self, event):
        self.back_btn.handle_event(event)
        for btn in self.shop_buttons:
            btn.handle_event(event)

    def update(self, dt):
        self.back_btn.update(dt)
        for btn in self.shop_buttons:
            btn.update(dt)

    def draw(self, surface):
        surface.fill((15, 20, 40))
        # Panel bg
        panel = Panel((50, 50, SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100),
                     (10, 15, 35, 200), COLORS["GOLD"])
        panel.draw(surface)

        title = self.font.render("SHOP - Buy Upgrades", True, COLORS["GOLD"])
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 65))

        coin_txt = self.small_font.render(f"Coins: {self.coins}", True, COLORS["YELLOW"])
        surface.blit(coin_txt, (SCREEN_WIDTH - 180, 65))

        cx = SCREEN_WIDTH // 2
        y = 150
        for i, item in enumerate(self.items):
            maxed = item["maxed"]
            color = COLORS["LIGHT_GRAY"] if maxed else COLORS["WHITE"]
            name = self.small_font.render(item["name"], True, color)
            desc = self.small_font.render(f'Lv.{item["level"]}/{item["max_level"]} {item["desc"]}',
                                        True, COLORS["LIGHT_GRAY"])
            surface.blit(name, (cx - 250, y))
            surface.blit(desc, (cx - 250, y + 20))
            if i < len(self.shop_buttons):
                self.shop_buttons[i].draw(surface)
            # Level bar
            bar_w = 100
            bar_h = 6
            bar_x = cx + 30
            bar_y = y + 12
            pygame.draw.rect(surface, COLORS["DARK_GRAY"],
                           (bar_x, bar_y, bar_w, bar_h), border_radius=3)
            if item["max_level"] > 0:
                fill_w = int(bar_w * item["level"] / item["max_level"])
                if fill_w > 0:
                    fill_color = COLORS["GOLD"] if maxed else COLORS["BLUE"]
                    pygame.draw.rect(surface, fill_color,
                                   (bar_x, bar_y, fill_w, bar_h), border_radius=3)
            y += 55

        self.back_btn.draw(surface)
