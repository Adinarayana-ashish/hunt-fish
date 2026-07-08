# Fish Hunter Pro

A 2D fish hunting arcade game built with Pygame. Hunt fish, battle bosses, upgrade your boat, and explore oceanic biomes.

## Installation

```bash
pip install pygame>=2.6.0
```

## Running

```bash
cd fish_hunting_game
python main.py
```

## Controls

| Key | Action |
|---|---|
| WASD / Arrow Keys | Move boat |
| Mouse | Aim harpoon |
| Left Click / Space | Shoot harpoon |
| E | Dive / surface |
| Shift | Sprint (uses stamina) |
| Escape | Pause |
| F11 | Toggle fullscreen |
| F12 | Screenshot |

## Gameplay

- Catch fish to earn coins and score
- Each level gets progressively harder with faster, tougher fish
- Every 5 levels, defeat the Kraken boss to unlock new biomes
- Collect treasure chests for bonus coins
- Manage oxygen when diving; surface to regenerate
- Build combos by catching fish quickly
- Land critical hits for bonus damage

## Fish Species

| Fish | Speed | HP | Value | Behavior |
|---|---|---|---|---|
| Goldfish | Fast | 1 | 5 | Schools, erratic darting |
| Tuna | Medium | 2 | 15 | Horizontal patrol |
| Salmon | Medium | 3 | 20 | Upstream swim, jumps |
| Swordfish | Fast | 4 | 35 | Charges at player |
| Shark | Medium | 8 | 50 | Aggressive chase |
| Golden Fish | Very Fast | 3 | 100 | Flees, very rare |

## Enemies

- **Jellyfish** — Floating, stuns player on contact
- **Sea Mines** — Stationary, explode on touch with large radius
- **Kraken Boss** — Multi-phase tentacle boss every 5 levels

## Biomes

Progress through 7 distinct biomes: Coral Reef, Deep Ocean, Kelp Forest, Abyssal Trench, Golden Depths, Frozen Trench, Volcano Depths.

## Upgrades

Buy upgrades between levels at the shop:
- Harpoon Power, Boat Speed, Extra Harpoons, Engine Power
- Reload Speed, Oxygen Tank, Sonar, Coin Magnet

## Adding External Assets

Place custom images in `assets/images/` and sounds in `assets/sounds/`.
The game will generate placeholder graphics/sounds if no external assets are found.

## Save Data

Progress is saved automatically to `saves/save.json`.
Configuration is stored in `config.json`.

## Project Structure

```
fish_hunting_game/
├── main.py           # Entry point
├── game.py           # Game loop, state machine, collision
├── settings.py       # Constants, colors, config
├── utils.py          # Save/load, achievements, helpers
├── player.py         # Boat class
├── fish.py           # Fish species + AI strategies
├── enemy.py          # Sharks, jellyfish, sea mines
├── boss.py           # Kraken boss
├── weapon.py         # Harpoon projectile
├── shop.py           # Upgrade manager
├── level.py          # Level progression, biomes, weather
├── effects/          # Visual effects
│   ├── particles.py  # Particle system (object pool)
│   ├── animation.py  # Animation + tween system
│   ├── water.py      # Water surface, bubbles, splash
│   └── audio.py      # Placeholder sound generation
├── ui/               # User interface
│   ├── buttons.py    # Button, toggle button
│   ├── widgets.py    # Progress bar, slider, panel
│   ├── hud.py        # In-game HUD
│   ├── menu.py       # Menu screens
│   └── shop_ui.py    # Shop interface
└── saves/            # Save data directory
```

## Requirements

- Python 3.11+
- Pygame 2.6+
