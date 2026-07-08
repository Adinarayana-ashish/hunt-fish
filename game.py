import pygame
import sys
import math
import random
from enum import Enum, auto

from settings import (COLORS, SCREEN_WIDTH, SCREEN_HEIGHT, TARGET_FPS, TITLE,
                      PLAYER_MAX_HEALTH, HARPOON_DAMAGE, CRITICAL_CHANCE,
                      CRITICAL_MULTIPLIER, COMBO_TIMEOUT, HARPOON_SPEED,
                      load_config, save_config, BOSS_LEVELS, BIOME_ORDER)
from player import Boat
from fish import Fish, FishSpawner
from enemy import Jellyfish, SeaMine
from boss import KrakenBoss
from weapon import Harpoon
from effects.particles import ParticlePool, ParticleEmitter
from effects.water import WaterSurface, Bubble, Splash
from effects.animation import Animation, Tween
from effects.audio import AudioManager
from ui.hud import HUD
from ui.menu import MainMenu, PauseMenu, SettingsMenu, GameOverScreen, VictoryScreen, AchievementList
from ui.shop_ui import ShopUI
from shop import ShopManager
from level import LevelManager, DailyChallenge
from utils import save_game, load_game, AchievementSystem, Timer, clamp, distance, angle_between


class GameState(Enum):
    MENU = auto()
    PLAYING = auto()
    PAUSED = auto()
    SHOP = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    SETTINGS = auto()
    ACHIEVEMENTS = auto()


class Game:
    def __init__(self):
        pygame.init()
        self.config = load_config()
        self._setup_display()

        self.clock = pygame.time.Clock()
        self.running = True
        self.dt = 0.0
        self.fps = TARGET_FPS

        # Audio
        self.audio_manager = AudioManager()
        self.audio_manager.init()
        self.audio_manager.set_master_volume(self.config.get("master_volume", 0.7))
        self.audio_manager.set_sfx_volume(self.config.get("sfx_volume", 0.8))
        self.audio_manager.set_music_volume(self.config.get("music_volume", 0.5))

        # Save / Achievements
        self.save_data = load_game()
        self.achievement_system = AchievementSystem()

        # Game state
        self.state = GameState.MENU
        self.prev_state = None
        self.state_stack = []

        # Game objects (created fresh per play)
        self.player = None
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.fish_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        self.boss_group = pygame.sprite.GroupSingle()
        self.particle_pool = ParticlePool(800)
        self.water_surface = WaterSurface(SCREEN_WIDTH)
        self.bubbles = [Bubble() for _ in range(30)]
        self.splashes = []
        self.hud = HUD()
        self.level_manager = LevelManager()
        self.shop_manager = ShopManager(self.save_data)
        self.fish_spawner = None
        self.daily_challenge = None

        # Gameplay state
        self.coins = 0
        self.score = 0
        self.combo = 0
        self.combo_timer = 0.0
        self.harpoons_left = 10
        self.stats = dict(self.save_data.get("statistics", {}))
        self.camera_shake = pygame.Vector2(0, 0)
        self.shake_intensity = 0.0
        self.game_paused = False
        self.treasures = []
        self.damage_numbers = []
        self.boss_active = False
        self.boss_defeated = False
        self.screenshot_requested = False
        self.last_shot_time = 0.0

        # Menus / Screens
        self.main_menu = MainMenu(self)
        self.pause_menu = PauseMenu(self)
        self.settings_menu = SettingsMenu(self)
        self.game_over_screen = GameOverScreen(self)
        self.victory_screen = VictoryScreen(self)
        self.shop_ui = ShopUI(self)
        self.achievement_list = AchievementList(self)

        # Particles
        self.splash_emitter = None

    def _setup_display(self):
        flags = pygame.HWSURFACE | pygame.DOUBLEBUF
        if self.config.get("fullscreen", False):
            flags |= pygame.FULLSCREEN
        w = self.config.get("screen_width", SCREEN_WIDTH)
        h = self.config.get("screen_height", SCREEN_HEIGHT)
        self.screen = pygame.display.set_mode((w, h), flags)
        self.display_w = w
        self.display_h = h
        pygame.display.set_caption(TITLE)

    def toggle_fullscreen(self):
        self.config["fullscreen"] = not self.config.get("fullscreen", False)
        pygame.display.toggle_fullscreen()
        save_config(self.config)

    def switch_state(self, state_name):
        state_map = {
            "menu": GameState.MENU,
            "playing": GameState.PLAYING,
            "paused": GameState.PAUSED,
            "shop": GameState.SHOP,
            "game_over": GameState.GAME_OVER,
            "victory": GameState.VICTORY,
            "settings": GameState.SETTINGS,
            "achievements": GameState.ACHIEVEMENTS,
        }
        new = state_map.get(state_name, GameState.MENU)
        if new == GameState.SETTINGS:
            self.prev_state = self.state
        self.state = new
        if new == GameState.MENU:
            self.main_menu.enter()
        elif new == GameState.PAUSED:
            self.pause_menu.enter()
        elif new == GameState.SETTINGS:
            self.settings_menu.enter()
        elif new == GameState.ACHIEVEMENTS:
            self.achievement_list.enter()

    # ── Game lifecycle ────────────────────────────────────────────────────
    def start_game(self):
        self._reset_game()
        self.save_data = load_game()
        self.shop_manager = ShopManager(self.save_data)
        coins = self.save_data.get("player", {}).get("coins", 0)
        self.coins = coins
        self.stats = dict(self.save_data.get("statistics", {}))
        self.state = GameState.PLAYING

    def start_daily(self):
        self._reset_game()
        self.daily_challenge = DailyChallenge()
        self.coins = 0
        self.state = GameState.PLAYING

    def resume_game(self):
        self.state = GameState.PLAYING

    def buy_upgrade(self, key):
        if self.shop_manager.buy(key):
            self.coins = self.shop_manager.player_data.get("coins", 0)
            self.audio_manager.play("buy")
            if self.player:
                self.player.apply_upgrades(self.shop_manager.get_all_levels())
            self.shop_ui.enter(self.coins, self.shop_manager.get_all_levels())
            save_game(self.save_data)
        else:
            self.audio_manager.play("error")

    def show_achievements(self):
        self.switch_state("achievements")

    def _reset_game(self):
        self.player = Boat((SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.player.apply_upgrades(self.shop_manager.get_all_levels())
        self.all_sprites = pygame.sprite.LayeredUpdates()
        self.fish_group = pygame.sprite.Group()
        self.enemy_group = pygame.sprite.Group()
        self.weapon_group = pygame.sprite.Group()
        self.boss_group = pygame.sprite.GroupSingle()
        self.particle_pool = ParticlePool(800)
        self.splashes.clear()
        self.treasures.clear()
        self.damage_numbers.clear()
        self.boss_active = False
        self.boss_defeated = False
        self.combo = 0
        self.combo_timer = 0.0
        self.score = 0
        self.harpoons_left = self.player.max_harpoons
        self.player.harpoons = self.player.max_harpoons
        self.shake_intensity = 0.0
        self.level_manager = LevelManager(self.save_data.get("player", {}).get("level", 1))
        self.fish_spawner = FishSpawner(self.level_manager.level,
                                        BIOME_ORDER[self.level_manager.biome_index])
        self.hud = HUD()
        self.water_surface = WaterSurface(SCREEN_WIDTH)
        self.bubbles = [Bubble() for _ in range(30)]
        self.last_shot_time = 0.0
        self.daily_challenge = None

    # ── Event handling ───────────────────────────────────────────────────
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            # Global keys
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                if event.key == pygame.K_F12:
                    self.screenshot_requested = True
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.PLAYING:
                        self.switch_state("paused")
                    elif self.state == GameState.PAUSED:
                        self.state = GameState.PLAYING
                    elif self.state == GameState.SHOP:
                        self.state = GameState.PLAYING
                    elif self.state == GameState.SETTINGS:
                        self.switch_state(self.prev_state.name.lower() if self.prev_state else "menu")
                    elif self.state == GameState.ACHIEVEMENTS:
                        self.switch_state("menu")

            # Delegate to active state
            if self.state == GameState.MENU:
                self.main_menu.handle_event(event)
            elif self.state == GameState.PLAYING:
                self._handle_playing_events(event)
            elif self.state == GameState.PAUSED:
                self.pause_menu.handle_event(event)
            elif self.state == GameState.SHOP:
                self.shop_ui.handle_event(event)
            elif self.state == GameState.GAME_OVER:
                self.game_over_screen.handle_event(event)
            elif self.state == GameState.VICTORY:
                self.victory_screen.handle_event(event)
            elif self.state == GameState.SETTINGS:
                self.settings_menu.handle_event(event)
            elif self.state == GameState.ACHIEVEMENTS:
                self.achievement_list.handle_event(event)

    def _handle_playing_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._shoot_harpoon()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self._shoot_harpoon()
            if event.key == pygame.e:
                # Toggle dive / surface
                if self.player:
                    self.player.is_diving = not self.player.is_diving

    # ── Shooting ─────────────────────────────────────────────────────────
    def _shoot_harpoon(self):
        if not self.player or not self.player.alive:
            return
        now = pygame.time.get_ticks() / 1000.0
        if now - self.last_shot_time < self.player.reload_time:
            return
        self.last_shot_time = now

        mouse_pos = pygame.mouse.get_pos()
        world_mouse = (mouse_pos[0], mouse_pos[1])
        angle = angle_between(self.player.pos, world_mouse)
        harpoon = Harpoon(self.player.pos, angle,
                         damage=self.player.harpoon_damage,
                         speed=HARPOON_SPEED * (1 + self.shop_manager.get_effect("harpoon_power") * 0.05))
        self.weapon_group.add(harpoon)
        self.all_sprites.add(harpoon)
        self.audio_manager.play("harpoon")
        self.stats["harpoons_shot"] = self.stats.get("harpoons_shot", 0) + 1
        self.player.harpoons -= 1
        if self.player.harpoons <= 0:
            self.player.reloading = True
            self.player.reload_timer.reset(self.player.reload_time)

    # ── Update ────────────────────────────────────────────────────────────
    def update(self):
        dt = min(self.dt, 0.05)  # Cap delta time

        if self.state == GameState.PLAYING:
            self._update_playing(dt)
        elif self.state == GameState.PAUSED:
            self.pause_menu.update(dt)
        elif self.state == GameState.MENU:
            self.main_menu.update(dt)
        elif self.state == GameState.SHOP:
            self.shop_ui.update(dt)
        elif self.state == GameState.GAME_OVER:
            self.game_over_screen.update(dt)
        elif self.state == GameState.VICTORY:
            self.victory_screen.update(dt)
        elif self.state == GameState.SETTINGS:
            self.settings_menu.update(dt)
        elif self.state == GameState.ACHIEVEMENTS:
            self.achievement_list.update(dt)

        # Shake decay
        if self.shake_intensity > 0:
            self.shake_intensity *= 0.92
            if self.shake_intensity < 0.5:
                self.shake_intensity = 0
            self.camera_shake = pygame.Vector2(
                random.uniform(-1, 1) * self.shake_intensity,
                random.uniform(-1, 1) * self.shake_intensity,
            )

    def _update_playing(self, dt):
        if not self.player:
            return

        # Player input
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys, dt)
        self.player.update(dt)

        # Combo timer
        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

        # Level & weather
        self.level_manager.update_weather(dt)
        weather = self.level_manager.weather
        wave_h = weather.get("wave_height", 0.5)
        wave_s = self.level_manager.current_biome.get("wave_speed", 1.0)
        self.water_surface.set_weather(wave_h, wave_s)
        self.water_surface.update(dt)

        # Spawner
        if self.fish_spawner:
            self.fish_spawner.update(dt, self.fish_group, self.player.pos)

        # Enemy spawn
        self._update_enemy_spawning(dt)

        # Fish updates
        for fish in self.fish_group:
            fish.update(dt, self.player.pos, None)
        for enemy in self.enemy_group:
            enemy.update(dt, self.player.pos)

        # Harpoon updates
        self.weapon_group.update(dt)

        # Boss
        if self.boss_active:
            boss = self.boss_group.sprite
            if boss and not boss.defeated:
                boss.update(dt, self.player.pos)
            elif boss and boss.defeated and not boss.alive():
                self._on_boss_defeated()

        # Treasures
        self._update_treasures(dt)

        # Bubbles
        for b in self.bubbles:
            b.update(dt)

        # Splashes
        self.splashes = [s for s in self.splashes if not s.is_dead]
        for s in self.splashes:
            s.update(dt)

        # Particles
        self.particle_pool.update(dt)

        # Damage numbers
        self.damage_numbers = [n for n in self.damage_numbers if n["life"] > 0]
        for n in self.damage_numbers:
            n["pos"].y -= n.get("rise_speed", 60) * dt
            n["life"] -= dt

        # HUD
        self.hud.update(dt, self.player, self.stats, self.boss_group.sprite)

        # Reload
        if self.player.reloading:
            self.player.reload_timer.update(dt)
            if self.player.reload_timer.finished:
                self.player.harpoons = self.player.max_harpoons
                self.player.reloading = False

        # Oxygen / depth
        self.player.is_diving = self.player.pos.y > 50

        # Collisions
        self._check_collisions()

        # Boss trigger
        if self.level_manager.is_boss_level() and not self.boss_active:
            self._spawn_boss()

        # Check game over
        if not self.player.alive:
            self._on_game_over()

        # Daily challenge check
        if self.daily_challenge and self.score >= self.daily_challenge.target_score:
            self._on_daily_complete()

    def _update_enemy_spawning(self, dt):
        rate = self.level_manager.get_enemy_rate_mult()
        if rate <= 0:
            return
        if random.random() < rate * dt * 0.3 and len(self.enemy_group) < 5 + self.level_manager.level:
            if random.random() < 0.4:
                self.enemy_group.add(Jellyfish())
            else:
                mine = SeaMine()
                mine.pos.y = random.uniform(200, SCREEN_HEIGHT - 50)
                self.enemy_group.add(mine)

    def _update_treasures(self, dt):
        treasure_data = self.level_manager.spawn_treasure(dt)
        if treasure_data:
            self.treasures.append(treasure_data)
            self.audio_manager.play("coin")
        for t in self.treasures[:]:
            if not t.get("active", True):
                self.treasures.remove(t)

    def _spawn_boss(self):
        boss = KrakenBoss(self.level_manager.level)
        self.boss_group.add(boss)
        self.boss_active = True
        self.boss_defeated = False
        self.audio_manager.play("boss_roar")
        self.shake_intensity = 15

    def _check_collisions(self):
        if not self.player:
            return

        # Harpoon -> Fish
        hits = pygame.sprite.groupcollide(self.weapon_group, self.fish_group, True, False)
        for harpoon, fish_list in hits.items():
            for fish in fish_list:
                damage = harpoon.damage
                if random.random() < CRITICAL_CHANCE + self.shop_manager.get_effect("harpoon_power") * 0.02:
                    damage = int(damage * CRITICAL_MULTIPLIER)
                    self.stats["critical_hits"] = self.stats.get("critical_hits", 0) + 1
                    self.audio_manager.play("critical")
                    self._add_damage_number(fish.pos, f"CRIT! {damage}", COLORS["YELLOW"])
                fish.take_damage(damage)
                if fish.caught:
                    self._on_fish_caught(fish, harpoon)
                else:
                    self._add_damage_number(fish.pos, str(damage), COLORS["RED"])
                    self.particle_pool.spawn_burst(fish.pos, 5, (30, 60), (0.2, 0.5),
                                                 (255, 100, 100), (2, 4))
                self.audio_manager.play("hit")
                self.particle_pool.spawn_burst(fish.pos, 8, (50, 100), (0.2, 0.5),
                                              (200, 200, 255), (2, 5))

        # Harpoon -> Enemies
        hits = pygame.sprite.groupcollide(self.weapon_group, self.enemy_group, True, False)
        for harpoon, enemies in hits.items():
            for enemy in enemies:
                if hasattr(enemy, 'take_damage'):
                    if enemy.take_damage(harpoon.damage):
                        self._on_enemy_killed(enemy)
                self._add_damage_number(enemy.pos, str(harpoon.damage), COLORS["RED"])

        # Player -> Enemies
        for enemy in self.enemy_group:
            if hasattr(enemy, 'explode') and enemy.explode is not None:
                if isinstance(enemy, SeaMine):
                    if distance(self.player.pos, enemy.pos) < 30:
                        if enemy.explode():
                            self._on_mine_explode(enemy)
                else:
                    if distance(self.player.pos, enemy.pos) < enemy.width:
                        self.player.take_damage(enemy.damage)
                        self.audio_manager.play("hit")
                        self.shake_intensity = 8
            elif hasattr(enemy, 'stun_time'):
                if distance(self.player.pos, enemy.pos) < enemy.width:
                    self.player.take_damage(enemy.damage)
                    self.player.stun(enemy.stun_time)
                    self.audio_manager.play("stun")
                    self.shake_intensity = 5
                    enemy.kill()

        # Boss collisions
        if self.boss_active and self.boss_group.sprite:
            boss = self.boss_group.sprite
            if not boss.defeated and boss.check_tentacle_hit(self.player.pos, 15):
                self.player.take_damage(10 * boss.phase)
                self.shake_intensity = 10
                self.audio_manager.play("hit")

            # Harpoon -> Boss
            hits = pygame.sprite.groupcollide(self.weapon_group, self.boss_group, True, False)
            for harpoon, _ in hits.items():
                crit = random.random() < CRITICAL_CHANCE
                damage = harpoon.damage * (CRITICAL_MULTIPLIER if crit else 1)
                if crit:
                    self.stats["critical_hits"] = self.stats.get("critical_hits", 0) + 1
                    self._add_damage_number(boss.pos, f"CRIT! {int(damage)}", COLORS["YELLOW"])
                    self.audio_manager.play("critical")
                boss.take_damage(damage)
                self.particle_pool.spawn_burst(boss.pos, 10, (60, 120), (0.3, 0.6),
                                              (100, 50, 200), (3, 6))
                self.audio_manager.play("hit")

        # Player -> Treasures
        for t in self.treasures[:]:
            if not t.get("active", True):
                continue
            dx = self.player.pos.x - t["pos"][0]
            dy = self.player.pos.y - t["pos"][1]
            if math.hypot(dx, dy) < 35:
                t["active"] = False
                self.coins += t["value"]
                self.stats["coins_collected"] = self.stats.get("coins_collected", 0) + t["value"]
                self.stats["treasures_found"] = self.stats.get("treasures_found", 0) + 1
                self.audio_manager.play("coin")
                self.particle_pool.spawn_burst(t["pos"], 15, (60, 120), (0.3, 0.8),
                                              COLORS["GOLD"], (3, 6))
                self.hud.add_notification(f"+{t['value']} coins!", COLORS["GOLD"])
                self.score += t["value"]
                # Magnet
                continue

            # Magnet pickup
            if self.player.magnet_range > 0:
                mag = self.player.magnet_range
                if math.hypot(dx, dy) < mag:
                    t["pos"][0] += (self.player.pos.x - t["pos"][0]) * 0.05
                    t["pos"][1] += (self.player.pos.y - t["pos"][1]) * 0.05

    def _on_fish_caught(self, fish, harpoon):
        self.combo += 1
        self.combo_timer = COMBO_TIMEOUT
        mult = 1.0 + min(self.combo - 1, 20) * 0.1
        earned = int(fish.value * mult)
        self.coins += earned
        self.score += earned
        self.stats["fish_caught"] = self.stats.get("fish_caught", 0) + 1
        self.stats["coins_collected"] = self.stats.get("coins_collected", 0) + earned
        self.hud.add_notification(f"+{earned} coins! x{mult:.1f}", COLORS["GOLD"])
        if fish.rare:
            self.stats["golden_caught"] = self.stats.get("golden_caught", 0) + 1
            self.hud.add_notification("LEGENDARY FISH CAUGHT!", COLORS["GOLD"])
        if self.combo > 1:
            self.hud.show_combo(self.combo)
        self.particle_pool.spawn_burst(fish.pos, 12, (40, 100), (0.3, 0.6),
                                      COLORS["GOLD"], (2, 5))
        self.audio_manager.play("coin")
        fish.kill()

    def _on_enemy_killed(self, enemy):
        self.particle_pool.spawn_burst(enemy.pos, 15, (50, 120), (0.3, 0.7),
                                      (200, 100, 100), (3, 6))
        self.shake_intensity = 10
        self.audio_manager.play("explosion")

    def _on_mine_explode(self, mine):
        self.shake_intensity = 15
        self.audio_manager.play("explosion")
        self.particle_pool.spawn_burst(mine.pos, 25, (80, 200), (0.3, 0.8),
                                      (255, 100, 50), (4, 10))
        if distance(self.player.pos, mine.pos) < mine.explosion_radius:
            dist = distance(self.player.pos, mine.pos)
            damage = int(mine.damage * (1 - dist / mine.explosion_radius))
            self.player.take_damage(damage)
            self._add_damage_number(self.player.pos, str(damage), COLORS["RED"])

    def _on_boss_defeated(self):
        self.boss_active = False
        self.boss_defeated = True
        self.audio_manager.play("level_up")
        self.shake_intensity = 20

        bonus = 100 * self.level_manager.level
        self.coins += bonus
        self.score += bonus
        self.stats["bosses_defeated"] = self.stats.get("bosses_defeated", 0) + 1

        # Save progress
        self.save_data["player"]["coins"] = self.coins
        self.save_data["player"]["level"] = self.level_manager.level
        self.save_data["statistics"] = dict(self.stats)
        save_game(self.save_data)

        # Check achievements
        new_ach = self.achievement_system.check(self.stats)
        for aid in new_ach:
            from settings import ACHIEVEMENTS
            info = ACHIEVEMENTS.get(aid, {})
            self.hud.add_notification(f"Achievement: {info.get('name', aid)}!", COLORS["PURPLE"])

        self.state = GameState.VICTORY
        self.victory_screen.enter({
            "Level": self.level_manager.level,
            "Score": self.score,
            "Coins Earned": bonus,
        })

    def _on_game_over(self):
        self.state = GameState.GAME_OVER
        self.save_data["player"]["coins"] = self.coins
        self.save_data["player"]["level"] = self.level_manager.level
        self.save_data["statistics"] = dict(self.stats)
        save_game(self.save_data)

        new_ach = self.achievement_system.check(self.stats)
        for aid in new_ach:
            from settings import ACHIEVEMENTS
            info = ACHIEVEMENTS.get(aid, {})
            self.hud.add_notification(f"Achievement: {info.get('name', aid)}!", COLORS["PURPLE"])

        self.game_over_screen.enter({
            "Score": self.score,
            "Coins": self.coins,
            "Fish Caught": self.stats.get("fish_caught", 0),
            "Level Reached": self.level_manager.level,
            "Max Combo": self.stats.get("max_combo", 0),
        })

    def _on_daily_complete(self):
        bonus = 200
        self.coins += bonus
        self.hud.add_notification(f"Daily Challenge Complete! +{bonus}", COLORS["GOLD"])
        self.daily_challenge = None

    def _add_damage_number(self, pos, text, color):
        self.damage_numbers.append({
            "pos": pygame.Vector2(pos),
            "text": text,
            "color": color,
            "life": 1.0,
            "rise_speed": 60,
        })

    # ── Draw ──────────────────────────────────────────────────────────────
    def draw(self):
        # Calculate camera offset
        offset_x = 0
        offset_y = 0
        if self.player:
            offset_x = int(self.player.pos.x - SCREEN_WIDTH // 2)
            offset_y = int(self.player.pos.y - SCREEN_HEIGHT // 2)

        screen = self.screen
        screen.fill(self.level_manager.current_biome.get("water_color", COLORS["DARK_BLUE"]))

        # Background gradient
        biome = self.level_manager.current_biome
        ambient = self.level_manager.get_ambient_light()
        self._draw_background(screen, biome, ambient)

        if self.state == GameState.PLAYING or self.state in (GameState.PAUSED, GameState.GAME_OVER, GameState.VICTORY):
            # Water surface (front layer)
            self.water_surface.draw(screen, 0)

            # Bubbles
            for b in self.bubbles:
                b.draw(screen, (offset_x if self.state == GameState.PLAYING else 0,
                              offset_y if self.state == GameState.PLAYING else 0))

            # Fish
            for fish in self.fish_group:
                fish.draw(screen, (offset_x, offset_y))

            # Enemies
            for enemy in self.enemy_group:
                enemy.draw(screen, (offset_x, offset_y))

            # Boss
            if self.boss_active and self.boss_group.sprite:
                self.boss_group.sprite.draw(screen, (offset_x, offset_y))

            # Player
            if self.player:
                self.player.draw(screen, (offset_x, offset_y))

            # Harpoons
            for harpoon in self.weapon_group:
                harpoon.draw(screen, (offset_x, offset_y))

            # Treasures
            for t in self.treasures:
                if t.get("active", True):
                    px = int(t["pos"][0] - offset_x)
                    py = int(t["pos"][1] - offset_y)
                    if -50 < px < SCREEN_WIDTH + 50:
                        self._draw_treasure(screen, px, py)

            # Splashes
            for s in self.splashes:
                s.draw(screen, (offset_x, offset_y))

            # Particles
            self.particle_pool.draw(screen, (offset_x, offset_y))

            # Damage numbers
            for n in self.damage_numbers:
                alpha = int(255 * min(1, n["life"] * 2))
                font = pygame.font.Font(None, 22)
                txt = font.render(n["text"], True, n["color"])
                txt.set_alpha(alpha)
                nx = int(n["pos"].x - offset_x)
                ny = int(n["pos"].y - offset_y)
                screen.blit(txt, (nx - txt.get_width() // 2, ny))

            # HUD
            if self.player:
                self.hud.draw(screen, self.player, self.coins, self.score,
                            self.level_manager.level,
                            self.player.harpoons,
                            int(self.clock.get_fps()),
                            self.stats)

            # Pause overlay
            if self.state == GameState.PAUSED:
                self.pause_menu.draw(screen)

            # Game over / victory overlay
            if self.state == GameState.GAME_OVER:
                self.game_over_screen.draw(screen)
            elif self.state == GameState.VICTORY:
                self.victory_screen.draw(screen)

        elif self.state == GameState.MENU:
            self.main_menu.draw(screen)
        elif self.state == GameState.SHOP:
            self.shop_ui.draw(screen)
        elif self.state == GameState.SETTINGS:
            self.settings_menu.draw(screen)
        elif self.state == GameState.ACHIEVEMENTS:
            self.achievement_list.draw(screen)

        # Camera shake
        if self.shake_intensity > 0 and self.config.get("screen_shake", True):
            shake = pygame.Vector2(
                random.uniform(-1, 1) * self.shake_intensity,
                random.uniform(-1, 1) * self.shake_intensity,
            )
            # We apply shake by offsetting the entire surface
            # This needs to be done at the end by capturing to an intermediate surface
            # For simplicity, draw directly with shake offset on the next frame

        # Screenshot
        if self.screenshot_requested:
            self.screenshot_requested = False
            import datetime
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            try:
                pygame.image.save(screen, f"screenshot_{ts}.png")
            except pygame.error:
                pass

        pygame.display.flip()

    def _draw_background(self, surface, biome, ambient):
        # Sky gradient
        sky = biome.get("water_top", COLORS["SKY_BLUE"])
        deep = biome.get("water_color", COLORS["DARK_BLUE"])
        for y in range(SCREEN_HEIGHT):
            t = y / SCREEN_HEIGHT
            r = int(sky[0] * (1 - t) + deep[0] * t)
            g = int(sky[1] * (1 - t) + deep[1] * t)
            b = int(sky[2] * (1 - t) + deep[2] * t)
            r = int(r * ambient)
            g = int(g * ambient)
            b = int(b * ambient)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Light rays
        if ambient > 0.4:
            for i in range(3):
                x = (pygame.time.get_ticks() * 0.01 + i * 200) % (SCREEN_WIDTH + 200) - 100
                for j in range(SCREEN_HEIGHT):
                    alpha = int(10 * (1 - j / SCREEN_HEIGHT) * ambient)
                    if alpha > 0:
                        c = (255, 255, 255, alpha)
                        pygame.draw.line(surface, c, (x, j), (x + 20 + math.sin(j * 0.01) * 10, j), 2)

        # Fog layer
        fog = biome.get("fog_color")
        if fog and self.level_manager.is_foggy():
            fog_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            fog_alpha = int(80 * (1 - self.level_manager.weather.get("visibility", 1.0)))
            fog_overlay.fill((fog[0], fog[1], fog[2], fog_alpha))
            surface.blit(fog_overlay, (0, 0))

        # Rain
        if self.level_manager.is_raining():
            rain_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            for _ in range(self.level_manager.weather.get("particle_rate", 30)):
                rx = random.randint(0, SCREEN_WIDTH)
                ry = (pygame.time.get_ticks() * 0.2 + rx * 10) % (SCREEN_HEIGHT * 2) - 100
                pygame.draw.line(rain_surf, (150, 180, 255, 60), (rx, ry), (rx - 3, ry + 12), 1)
            surface.blit(rain_surf, (0, 0))

    def _draw_treasure(self, surface, x, y):
        t = pygame.time.get_ticks() * 0.003
        bob = math.sin(t) * 5
        chest_surf = pygame.Surface((28, 24), pygame.SRCALPHA)
        pygame.draw.rect(chest_surf, (139, 90, 43), (0, 8, 28, 16), border_radius=2)
        pygame.draw.rect(chest_surf, (180, 120, 50), (0, 0, 28, 10), border_radius=2)
        pygame.draw.rect(chest_surf, (255, 215, 0), (10, 8, 8, 6), border_radius=1)
        glow = pygame.Surface((40, 40), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 215, 0, 30), (20, 20), 20)
        surface.blit(glow, (int(x - 20), int(y - 20 + bob)))
        surface.blit(chest_surf, (int(x - 14), int(y - 12 + bob)))

    # ── Main Loop ─────────────────────────────────────────────────────────
    def run(self):
        while self.running:
            self.dt = self.clock.tick(TARGET_FPS) / 1000.0
            self.handle_events()
            self.update()
            self.draw()
        self._cleanup()

    def _cleanup(self):
        self.save_data["player"]["coins"] = self.coins
        self.save_data["player"]["level"] = self.level_manager.level
        self.save_data["statistics"] = dict(self.stats)
        save_game(self.save_data)
        save_config(self.config)
        pygame.quit()
        sys.exit()


