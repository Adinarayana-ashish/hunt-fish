import pygame
from utils import clamp
from settings import COLORS, SCREEN_WIDTH


class HUD:
    def __init__(self):
        self.font = pygame.font.Font(None, 22)
        self.big_font = pygame.font.Font(None, 32)
        self.anim_coin = 0.0
        self.boss_hp = 0
        self.boss_max_hp = 0
        self.show_boss_hp = False
        self.notifications = []
        self.combo_display = 0
        self.combo_timer = 0.0

        # Bar dimensions
        self.bar_w = 180
        self.bar_h = 16
        self.margin = 10

    def update(self, dt, player, stats, boss=None):
        self.anim_coin += dt * 3
        self.combo_timer -= dt
        if self.combo_timer <= 0:
            self.combo_display = 0

        # Boss HP
        if boss and boss.emerged and not boss.defeated:
            self.show_boss_hp = True
            self.boss_hp = boss.hp
            self.boss_max_hp = boss.max_hp
        else:
            self.show_boss_hp = False

        # Update notifications
        self.notifications = [n for n in self.notifications if n["timer"] > 0]
        for n in self.notifications:
            n["timer"] -= dt
            n["y"] -= 30 * dt

    def add_notification(self, text, color=COLORS["YELLOW"]):
        self.notifications.append({
            "text": text,
            "color": color,
            "timer": 2.0,
            "y": SCREEN_WIDTH // 2,
        })

    def show_combo(self, combo):
        self.combo_display = combo
        self.combo_timer = 3.0

    def _draw_bar(self, surface, x, y, current, maximum, color, label):
        # Background
        bg_rect = pygame.Rect(x, y, self.bar_w, self.bar_h)
        pygame.draw.rect(surface, COLORS["DARK_GRAY"], bg_rect, border_radius=4)
        # Fill
        if maximum > 0:
            ratio = clamp(current / maximum, 0, 1)
            fill_w = int(self.bar_w * ratio)
            if fill_w > 0:
                fill_rect = pygame.Rect(x, y, fill_w, self.bar_h)
                pygame.draw.rect(surface, color, fill_rect, border_radius=4)
        # Border
        pygame.draw.rect(surface, COLORS["WHITE"], bg_rect, 1, border_radius=4)
        # Label
        txt = self.font.render(f"{label} {int(current)}/{int(maximum)}", True, COLORS["WHITE"])
        surface.blit(txt, (x + 3, y + 1))

    def draw(self, surface, player, coins, score, level, harpoons, fps, stats):
        # ── Left side bars ──
        y = self.margin
        # Health
        hp_color = COLORS["GREEN"] if player.health > 50 else (COLORS["YELLOW"] if player.health > 25 else COLORS["RED"])
        self._draw_bar(surface, self.margin, y, player.health, player.max_health, hp_color, "HP")
        y += self.bar_h + 4
        # Oxygen
        ox_color = COLORS["BLUE"] if player.oxygen > 50 else COLORS["CYAN"]
        self._draw_bar(surface, self.margin, y, player.oxygen, player.max_oxygen, ox_color, "O2")
        y += self.bar_h + 4
        # Stamina
        self._draw_bar(surface, self.margin, y, player.stamina, player.max_stamina, COLORS["ORANGE"], "STM")
        y += self.bar_h + 8

        # ── Stats ──
        info_items = [
            f"Coins: {coins}", f"Score: {score}", f"Level: {level}",
            f"Harpoons: {harpoons}", f"FPS: {fps}",
        ]
        for item in info_items:
            txt = self.font.render(item, True, COLORS["WHITE"])
            surface.blit(txt, (self.margin, y))
            y += 22

        # ── Combo ──
        if self.combo_display > 1:
            combo_alpha = min(255, int(255 * (self.combo_timer / 3.0)))
            combo_text = f"{self.combo_display}x Combo!"
            txt = self.big_font.render(combo_text, True, COLORS["YELLOW"])
            txt.set_alpha(combo_alpha)
            surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, 60))

        # ── Notifications ──
        for n in self.notifications:
            alpha = int(255 * min(1, n["timer"] / 0.5))
            txt = self.font.render(n["text"], True, n["color"])
            txt.set_alpha(alpha)
            surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, 80))

        # ── Boss HP ──
        if self.show_boss_hp:
            bar_x = SCREEN_WIDTH // 2 - 200
            bar_y = 10
            bw = 400
            pygame.draw.rect(surface, COLORS["DARK_GRAY"],
                           (bar_x, bar_y, bw, 22), border_radius=6)
            ratio = self.boss_hp / self.boss_max_hp if self.boss_max_hp > 0 else 0
            fill_w = int(bw * ratio)
            if fill_w > 0:
                boss_color = COLORS["RED"] if ratio < 0.33 else (COLORS["YELLOW"] if ratio < 0.66 else COLORS["PURPLE"])
                pygame.draw.rect(surface, boss_color,
                               (bar_x, bar_y, fill_w, 22), border_radius=6)
            pygame.draw.rect(surface, COLORS["WHITE"],
                           (bar_x, bar_y, bw, 22), 2, border_radius=6)
            boss_txt = self.font.render(f"Kraken Lv.{boss.level if hasattr(boss, 'level') else '?'}",
                                      True, COLORS["WHITE"])
            surface.blit(boss_txt, (bar_x + 5, bar_y + 2))

        # ── Depth indicator ──
        depth = abs(player.pos.y) if hasattr(player, 'pos') else 0
        depth_txt = self.font.render(f"Depth: {int(depth)}m", True, COLORS["CYAN"])
        surface.blit(depth_txt, (SCREEN_WIDTH - 120, self.margin))
