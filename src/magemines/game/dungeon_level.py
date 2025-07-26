"""Dungeon level management system."""

from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any
from .map_generator import MapGenerator, TileType


@dataclass
class DungeonLevel:
    """Represents a single dungeon level."""
    depth: int
    width: int
    height: int
    generator: MapGenerator
    tiles: list[list[str]]
    
    # Entity positions on this level
    entities: Dict[Tuple[int, int], Any] = None
    
    # Items on the floor
    items: Dict[Tuple[int, int], list] = None
    
    # Player's last position when leaving this level
    last_player_pos: Optional[Tuple[int, int]] = None
    
    # Stairs positions
    stairs_up_pos: Optional[Tuple[int, int]] = None
    stairs_down_pos: Optional[Tuple[int, int]] = None
    
    def __post_init__(self):
        """Initialize empty collections if not provided."""
        if self.entities is None:
            self.entities = {}
        if self.items is None:
            self.items = {}
        
        # Find and cache stair positions
        self._find_stairs()
    
    def _find_stairs(self):
        """Find and cache the positions of stairs."""
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == '<':
                    self.stairs_up_pos = (x, y)
                elif self.tiles[y][x] == '>':
                    self.stairs_down_pos = (x, y)
    
    def get_tile(self, x: int, y: int) -> str:
        """Get the tile at the given position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return '#'  # Out of bounds is wall
    
    def is_stairs_up(self, x: int, y: int) -> bool:
        """Check if the position is stairs up."""
        return self.tiles[y][x] == '<'
    
    def is_stairs_down(self, x: int, y: int) -> bool:
        """Check if the position is stairs down."""
        return self.tiles[y][x] == '>'
    
    def get_spawn_position(self, from_above: bool) -> Tuple[int, int]:
        """Get the spawn position when entering this level.
        
        Args:
            from_above: True if coming from level above, False if from below
            
        Returns:
            Spawn position (x, y)
        """
        if from_above and self.stairs_up_pos:
            return self.stairs_up_pos
        elif not from_above and self.stairs_down_pos:
            return self.stairs_down_pos
        else:
            # Fallback to finding any floor tile
            for y in range(self.height):
                for x in range(self.width):
                    if self.tiles[y][x] == '.':
                        return (x, y)
            return (1, 1)  # Last resort