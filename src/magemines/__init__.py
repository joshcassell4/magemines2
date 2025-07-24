"""
MageMines - A terminal-based roguelike god-game.

Guide your mages through procedurally generated dungeons using divine powers.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# Import key classes for easier access
from .game.game_loop import run_game
from .game.map import GameMap
from .game.player import Player

__all__ = ["run_game", "GameMap", "Player"]