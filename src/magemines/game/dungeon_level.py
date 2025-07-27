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
        # First try to use stairs
        spawn_pos = None
        if from_above and self.stairs_up_pos:
            spawn_pos = self.stairs_up_pos
        elif not from_above and self.stairs_down_pos:
            spawn_pos = self.stairs_down_pos
        
        # Verify the spawn position is actually accessible
        if spawn_pos:
            x, y = spawn_pos
            if self.tiles[y][x] in ['.', '<', '>']:
                return spawn_pos
        
        # If stairs position is invalid, find the largest connected area
        # This ensures player spawns in the main area of the map
        from collections import deque
        
        # Find all connected components
        visited = [[False for _ in range(self.width)] for _ in range(self.height)]
        components = []
        
        for start_y in range(self.height):
            for start_x in range(self.width):
                if not visited[start_y][start_x] and self.tiles[start_y][start_x] in ['.', '<', '>']:
                    # Flood fill to find connected component
                    component = []
                    queue = deque([(start_x, start_y)])
                    
                    while queue:
                        x, y = queue.popleft()
                        if visited[y][x] or not (0 <= x < self.width and 0 <= y < self.height):
                            continue
                        if self.tiles[y][x] not in ['.', '<', '>', '+']:
                            continue
                        
                        visited[y][x] = True
                        component.append((x, y))
                        
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                queue.append((nx, ny))
                    
                    if component:
                        components.append(component)
        
        # Use the largest component
        if components:
            largest = max(components, key=len)
            # Return a position near the center of the largest component
            return largest[len(largest) // 2]
        
        # Ultimate fallback - find any floor tile
        for y in range(self.height):
            for x in range(self.width):
                    if self.tiles[y][x] == '.':
                        return (x, y)
            return (1, 1)  # Last resort