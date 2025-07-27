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
    # Resources
    RESOURCE_WOOD = auto()
    RESOURCE_STONE = auto()
    RESOURCE_ORE = auto()
    RESOURCE_CRYSTAL = auto()
    RESOURCE_ESSENCE = auto()
    RESOURCE_MUSHROOM = auto()
    RESOURCE_HERBS = auto()


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
    
    # Resource placement parameters
    resource_density: float = 0.02   # Percentage of floor tiles that have resources
    resource_clustering: float = 0.6  # How much resources cluster together (0-1)
    depth_resource_bonus: float = 0.1  # Extra resources per depth level


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
    
    def place_resources(self, depth: int = 1) -> None:
        """Place resources on the map based on depth and configuration."""
        import random
        from ...game.resources import ResourceType, RESOURCE_PROPERTIES
        
        # Calculate resource density based on depth
        density = self.config.resource_density * (1 + depth * self.config.depth_resource_bonus)
        
        # Get all floor positions
        floor_positions = []
        for y in range(self.height):
            for x in range(self.width):
                if self.tiles[y][x] == TileType.FLOOR:
                    floor_positions.append((x, y))
        
        if not floor_positions:
            return
        
        # Calculate number of resources to place
        num_resources = int(len(floor_positions) * density)
        
        # Resource type to tile type mapping
        resource_tile_map = {
            ResourceType.WOOD: TileType.RESOURCE_WOOD,
            ResourceType.STONE: TileType.RESOURCE_STONE,
            ResourceType.ORE: TileType.RESOURCE_ORE,
            ResourceType.CRYSTAL: TileType.RESOURCE_CRYSTAL,
            ResourceType.ESSENCE: TileType.RESOURCE_ESSENCE,
            ResourceType.FOOD: TileType.RESOURCE_MUSHROOM,
            ResourceType.HERBS: TileType.RESOURCE_HERBS,
        }
        
        # Place resources with clustering
        placed_resources = []
        for _ in range(num_resources):
            # Select resource type based on depth and rarity
            available_resources = []
            for res_type, props in RESOURCE_PROPERTIES.items():
                if res_type == ResourceType.WATER:
                    continue  # Water is placed differently
                
                # Adjust rarity based on depth
                adjusted_rarity = props.rarity * (1 - depth * 0.02)  # Rarer resources more common at depth
                if random.random() > adjusted_rarity:
                    available_resources.append(res_type)
            
            if not available_resources:
                continue
                
            resource_type = random.choice(available_resources)
            tile_type = resource_tile_map.get(resource_type)
            
            if not tile_type:
                continue
            
            # Choose position (with clustering)
            if placed_resources and random.random() < self.config.resource_clustering:
                # Place near existing resource
                base_x, base_y = random.choice(placed_resources)
                candidates = []
                for dx in range(-3, 4):
                    for dy in range(-3, 4):
                        x, y = base_x + dx, base_y + dy
                        if (x, y) in floor_positions and self.tiles[y][x] == TileType.FLOOR:
                            candidates.append((x, y))
                
                if candidates:
                    x, y = random.choice(candidates)
                else:
                    x, y = random.choice(floor_positions)
            else:
                # Place randomly
                x, y = random.choice(floor_positions)
            
            # Place the resource
            self.tiles[y][x] = tile_type
            placed_resources.append((x, y))
            floor_positions.remove((x, y))