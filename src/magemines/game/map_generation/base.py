"""Base classes and enums for map generation system."""

from enum import Enum, auto
from typing import Optional, Tuple
from dataclasses import dataclass


class TileType(Enum):
    """Types of tiles in the game."""
    EMPTY = auto()
    FLOOR = auto()
    WALL = auto()
    DOOR = auto()
    STAIRS_UP = auto()
    STAIRS_DOWN = auto()
    WATER = auto()
    LAVA = auto()
    CHEST = auto()
    ALTAR = auto()


class GenerationMethod(Enum):
    """Map generation algorithms."""
    ROOMS_AND_CORRIDORS = auto()
    CELLULAR_AUTOMATA = auto()
    TOWN = auto()


@dataclass
class MapGeneratorConfig:
    """Configuration for map generation."""
    width: int = 80
    height: int = 50
    min_room_size: int = 4
    max_room_size: int = 12
    max_rooms: int = 20
    method: GenerationMethod = GenerationMethod.ROOMS_AND_CORRIDORS
    
    # Cave generation parameters
    initial_density: float = 0.45
    smoothing_iterations: int = 5
    
    # Town generation parameters
    road_width: int = 3
    building_padding: int = 2
    
    # Corridor style parameters
    diagonal_corridors: bool = True  # Enable diagonal corridors
    diagonal_chance: float = 0.5     # Chance of diagonal vs L-shaped corridor
    corridor_width: int = 1          # Width of corridors (1 for thin, 2+ for wider)


class MapGenerator:
    """Base class for map generators."""
    
    def __init__(self, config: MapGeneratorConfig):
        """Initialize the map generator."""
        self.config = config
        self.width = config.width
        self.height = config.height
        self.tiles = [[TileType.EMPTY for _ in range(self.width)] 
                      for _ in range(self.height)]
    
    def clear(self, tile_type: TileType) -> None:
        """Clear the map with a specific tile type."""
        for y in range(self.height):
            for x in range(self.width):
                self.tiles[y][x] = tile_type
    
    def set_tile(self, x: int, y: int, tile_type: TileType) -> None:
        """Set a tile at the given position."""
        if self.in_bounds(x, y):
            self.tiles[y][x] = tile_type
    
    def get_tile(self, x: int, y: int) -> TileType:
        """Get the tile at the given position."""
        if self.in_bounds(x, y):
            return self.tiles[y][x]
        return TileType.EMPTY
    
    def in_bounds(self, x: int, y: int) -> bool:
        """Check if a position is within map bounds."""
        return 0 <= x < self.width and 0 <= y < self.height
    
    def generate(self) -> None:
        """Generate the map. Override in subclasses."""
        raise NotImplementedError
    
    def find_empty_position(self) -> Optional[Tuple[int, int]]:
        """Find a random empty floor position."""
        import random
        floor_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == TileType.FLOOR:
                    floor_positions.append((x, y))
        
        if floor_positions:
            return random.choice(floor_positions)
        return None