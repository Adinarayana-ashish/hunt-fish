import math
import pygame
from settings import COLORS, SCREEN_WIDTH, SCREEN_HEIGHT
from ui.buttons import Button, ToggleButton
from ui.widgets import Panel, Slider
from utils import ease_out_cubic, clamp


class MainMenu:
    def __init__(self, game_ref):
        self.game = game_ref
        self.buttons = []
        self.alpha = 0
        self.state = "fade_in"
        self.fade_timer = 0.5
        self.bg_waves = 0.0
        self.title_offset = -100
        self._create_buttons()
        self.font_title = pygame.font.Font(None, 72)
        self.font_sub = pygame.font.Font(None, 28)

    def _create_buttons(self):
        cx = SCREEN_WIDTH // 2
        items = [
            ("Start Game", lambda: self.game.start_game()),
            ("Daily Challenge", lambda: self.game.start_daily()),
            ("Settings", lambda: self.game.switch_state("settings")),
            ("Achievements", lambda: self.game.show_achievements()),
            ("Quit", lambda: setattr(self.game, 'running', False)),
        ]
        self.buttons.clear()
        for i, (text, cb) in enumerate(items):
            btn = Button(
                (cx - 120, 350 + i * 55, 240, 45),
                text, cb,
                color=(30, 60, 120),
                hover_color=(50, 100, 200),
                font_size=26,
            )
            self.buttons.append(btn)

    def enter(self):
        self.alpha = 0
        self.state = "fade_in"
        self.fade_timer = 0.5
        self.title_offset = -100

    def handle_event(self, event):
        if self.state == "active":
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt):
        self.bg_waves += dt * 1.5
        if self.state == "fade_in":
            self.fade_timer -= dt
            self.alpha = int(255 * (1 - self.fade_timer / 0.5))
            self.title_offset = ease_out_cubic(1 - self.fade_timer / 0.5) * 100 - 100
            if self.fade_timer <= 0:
                self.state = "active"
                self.alpha = 255
                self.title_offset = 0
        for btn in self.buttons:
            btn.update(dt)

    def draw(self, surface):
        surface.fill((10, 20, 50))

        # Wave BG
        for i in range(5):
            pygame.draw.ellipse(surface, (20, 50, 100, 60),
                              (-50, 200 + math.sin(self.bg_waves + i) * 20 + i * 60,
                               SCREEN_WIDTH + 100, 80), 2)

        # Title
        title = self.font_title.render("FISH HUNTER", True, COLORS["GOLD"])
        title.set_alpha(self.alpha)
        tw = title.get_width()
        surface.blit(title, (SCREEN_WIDTH // 2 - tw // 2,
                           200 + self.title_offset))

        sub = self.font_sub.render("PRO", True, COLORS["CYAN"])
        sub.set_alpha(self.alpha)
        sw = sub.get_width()
        surface.blit(sub, (SCREEN_WIDTH // 2 - sw // 2, 260))

        for btn in self.buttons:
            btn.draw(surface)


class PauseMenu:
    def __init__(self, game_ref):
        self.game = game_ref
        self.buttons = []
        self.alpha = 0
        self.state = "fade_in"
        self.fade_timer = 0.2
        self._create_buttons()

    def _create_buttons(self):
        cx = SCREEN_WIDTH // 2
        items = [
            ("Resume", lambda: self.game.resume_game()),
            ("Settings", lambda: self.game.switch_state("settings")),
            ("Main Menu", lambda: self.game.switch_state("menu")),
        ]
        self.buttons.clear()
        for i, (text, cb) in enumerate(items):
            btn = Button(
                (cx - 100, 300 + i * 55, 200, 45),
                text, cb,
                color=(40, 40, 60),
                hover_color=(60, 60, 120),
                font_size=24,
            )
            self.buttons.append(btn)

    def enter(self):
        self.alpha = 0
        self.state = "fade_in"
        self.fade_timer = 0.2

    def handle_event(self, event):
        if self.state == "active":
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt):
        if self.state == "fade_in":
            self.fade_timer -= dt
            self.alpha = int(255 * (1 - self.fade_timer / 0.2))
            if self.fade_timer <= 0:
                self.state = "active"
                self.alpha = 255
        for btn in self.buttons:
            btn.update(dt)

    def draw(self, surface):
        # Overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        title = pygame.font.Font(None, 48).render("PAUSED", True, COLORS["WHITE"])
        title.set_alpha(self.alpha)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 200))
        for btn in self.buttons:
            btn.draw(surface)


class SettingsMenu:
    def __init__(self, game_ref):
        self.game = game_ref
        self.buttons = []
        self.sliders = []
        self.font = pygame.font.Font(None, 32)
        self._create_ui()

    def _create_ui(self):
        cx = SCREEN_WIDTH // 2
        y = 180
        self.sliders.clear()
        self.buttons.clear()

        for label, key in [("Master Volume", "master_volume"),
                          ("SFX Volume", "sfx_volume"),
                          ("Music Volume", "music_volume")]:
            sl = Slider(
                (cx - 100, y, 200, 20), label,
                current=self.game.config.get(key, 0.7),
                callback=lambda v, k=key: self._set_setting(k, v),
            )
            self.sliders.append(sl)
            y += 50

        tb = ToggleButton(
            (cx - 100, y, 200, 40),
            "Fullscreen",
            lambda: self.game.config.get("fullscreen", False),
            lambda v: self._set_setting("fullscreen", v),
            color=(40, 40, 60),
            hover_color=(60, 60, 120),
        )
        self.buttons.append(tb)
        y += 55

        tb2 = ToggleButton(
            (cx - 100, y, 200, 40),
            "Screen Shake",
            lambda: self.game.config.get("screen_shake", True),
            lambda v: self._set_setting("screen_shake", v),
            color=(40, 40, 60),
            hover_color=(60, 60, 120),
        )
        self.buttons.append(tb2)
        y += 55

        tb3 = ToggleButton(
            (cx - 100, y, 200, 40),
            "Show FPS",
            lambda: self.game.config.get("show_fps", True),
            lambda v: self._set_setting("show_fps", v),
            color=(40, 40, 60),
            hover_color=(60, 60, 120),
        )
        self.buttons.append(tb3)
        y += 70

        btn = Button(
            (cx - 100, y, 200, 45),
            "Back",
            lambda: self.game.switch_state(self.game._prev_state or "menu"),
            color=(40, 40, 60),
            hover_color=(60, 60, 120),
            font_size=24,
        )
        self.buttons.append(btn)

    def _set_setting(self, key, value):
        self.game.config[key] = value
        if hasattr(self.game, 'audio_manager'):
            if key == "master_volume":
                self.game.audio_manager.set_master_volume(value)
            elif key == "sfx_volume":
                self.game.audio_manager.set_sfx_volume(value)
            elif key == "music_volume":
                self.game.audio_manager.set_music_volume(value)

    def enter(self):
        pass

    def handle_event(self, event):
        for sl in self.sliders:
            sl.handle_event(event)
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt):
        for btn in self.buttons:
            btn.update(dt)

    def draw(self, surface):
        surface.fill((15, 25, 55))
        title = self.font.render("Settings", True, COLORS["WHITE"])
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))
        for sl in self.sliders:
            sl.draw(surface)
        for btn in self.buttons:
            btn.draw(surface)


class GameOverScreen:
    def __init__(self, game_ref):
        self.game = game_ref
        self.buttons = []
        self.alpha = 0
        self.state = "fade_in"
        self.fade_timer = 1.0
        self.stats = {}
        self._create_buttons()

    def _create_buttons(self):
        cx = SCREEN_WIDTH // 2
        items = [
            ("Try Again", lambda: self.game.start_game()),
            ("Main Menu", lambda: self.game.switch_state("menu")),
        ]
        self.buttons.clear()
        for i, (text, cb) in enumerate(items):
            btn = Button(
                (cx - 100, 400 + i * 55, 200, 45),
                text, cb,
                color=(80, 30, 30),
                hover_color=(140, 50, 50),
                font_size=24,
            )
            self.buttons.append(btn)

    def enter(self, stats=None):
        self.alpha = 0
        self.state = "fade_in"
        self.fade_timer = 1.0
        self.stats = stats or {}

    def handle_event(self, event):
        if self.state == "active":
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt):
        if self.state == "fade_in":
            self.fade_timer -= dt
            self.alpha = int(255 * (1 - self.fade_timer / 1.0))
            if self.fade_timer <= 0:
                self.state = "active"
                self.alpha = 255
        for btn in self.buttons:
            btn.update(dt)

    def draw(self, surface):
        surface.fill((10, 5, 20))
        title = pygame.font.Font(None, 64).render("GAME OVER", True, COLORS["RED"])
        title.set_alpha(self.alpha)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

        font = pygame.font.Font(None, 24)
        y = 250
        for k, v in self.stats.items():
            txt = font.render(f"{k}: {v}", True, COLORS["LIGHT_GRAY"])
            txt.set_alpha(self.alpha)
            surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, y))
            y += 30

        for btn in self.buttons:
            btn.draw(surface)


class VictoryScreen:
    def __init__(self, game_ref):
        self.game = game_ref
        self.buttons = []
        self.alpha = 0
        self.state = "fade_in"
        self.fade_timer = 1.0
        self.stats = {}
        self._create_buttons()

    def _create_buttons(self):
        cx = SCREEN_WIDTH // 2
        items = [
            ("Continue", lambda: self.game.switch_state("menu")),
        ]
        self.buttons.clear()
        for i, (text, cb) in enumerate(items):
            btn = Button(
                (cx - 100, 450 + i * 55, 200, 45),
                text, cb,
                color=(30, 80, 30),
                hover_color=(50, 140, 50),
                font_size=24,
            )
            self.buttons.append(btn)

    def enter(self, stats=None):
        self.alpha = 0
        self.state = "fade_in"
        self.fade_timer = 1.0
        self.stats = stats or {}

    def handle_event(self, event):
        if self.state == "active":
            for btn in self.buttons:
                btn.handle_event(event)

    def update(self, dt):
        if self.state == "fade_in":
            self.fade_timer -= dt
            self.alpha = int(255 * (1 - self.fade_timer / 1.0))
            if self.fade_timer <= 0:
                self.state = "active"
                self.alpha = 255
        for btn in self.buttons:
            btn.update(dt)

    def draw(self, surface):
        surface.fill((10, 20, 10))
        title = pygame.font.Font(None, 64).render("VICTORY!", True, COLORS["GOLD"])
        title.set_alpha(self.alpha)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        sub = pygame.font.Font(None, 28).render("Boss Defeated! New region unlocked.", True, COLORS["GREEN"])
        sub.set_alpha(self.alpha)
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 200))

        font = pygame.font.Font(None, 24)
        y = 280
        for k, v in self.stats.items():
            txt = font.render(f"{k}: {v}", True, COLORS["LIGHT_GRAY"])
            surface.blit(txt, (SCREEN_WIDTH // 2 - txt.get_width() // 2, y))
            y += 30

        for btn in self.buttons:
            btn.draw(surface)


class AchievementList:
    def __init__(self, game_ref):
        self.game = game_ref
        self.buttons = []
        self.achievements = []
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)
        self._create_buttons()

    def _create_buttons(self):
        btn = Button(
            (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 80, 200, 45),
            "Back",
            lambda: self.game.switch_state("menu"),
            color=(40, 40, 60),
            hover_color=(60, 60, 120),
            font_size=24,
        )
        self.buttons = [btn]

    def enter(self):
        from settings import ACHIEVEMENTS
        from utils import load_game
        data = load_game()
        unlocked = data.get("achievements", [])
        self.achievements = []
        for aid, info in ACHIEVEMENTS.items():
            self.achievements.append({
                "id": aid,
                "name": info["name"],
                "desc": info["desc"],
                "unlocked": aid in unlocked,
            })

    def handle_event(self, event):
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt):
        for btn in self.buttons:
            btn.update(dt)

    def draw(self, surface):
        surface.fill((15, 20, 40))
        title = self.font.render("Achievements", True, COLORS["GOLD"])
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 60))

        y = 110
        for ach in self.achievements:
            color = COLORS["GREEN"] if ach["unlocked"] else COLORS["DARK_GRAY"]
            name = self.small_font.render(ach["name"], True, color)
            desc = self.small_font.render(ach["desc"], True,
                                          COLORS["LIGHT_GRAY"] if ach["unlocked"] else COLORS["DARK_GRAY"])
            surface.blit(name, (SCREEN_WIDTH // 2 - 200, y))
            surface.blit(desc, (SCREEN_WIDTH // 2 - 200, y + 22))
            status = self.small_font.render("✓" if ach["unlocked"] else "✗",
                                          True, color)
            surface.blit(status, (SCREEN_WIDTH // 2 + 200, y))
            y += 50
            if y > SCREEN_HEIGHT - 100:
                break

        for btn in self.buttons:
            btn.draw(surface)


