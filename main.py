#!/usr/bin/env python3
"""
Fish Hunter Pro — A 2D fish hunting arcade game built with Pygame.

Usage:
    pip install pygame
    python main.py

Controls:
    WASD / Arrow keys  — Move boat
    Mouse              — Aim
    Left click / Space — Shoot harpoon
    E                  — Dive / surface
    Shift              — Sprint
    Escape             — Pause
    F11                — Toggle fullscreen
    F12                — Screenshot
"""

import sys
import os

# Ensure the project directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game import Game


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
