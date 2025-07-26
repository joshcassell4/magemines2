"""Level management system for multi-level dungeons."""

from typing import Dict, Tuple, Optional
from .dungeon_level import DungeonLevel
from .map_generator import (
    MapGeneratorConfig, DungeonGenerator, CaveGenerator, 
    TownGenerator, GenerationMethod, TileType
)


class LevelManager:
    """Manages multiple dungeon levels and transitions between them."""
    
    def __init__(self, width: int, height: int, max_depth: int = 10):
        """Initialize the level manager.
        
        Args:
            width: Width of each level
            height: Height of each level
            max_depth: Maximum dungeon depth
        """
        self.width = width
        self.height = height
        self.max_depth = max_depth
        self.current_depth = 1
        self.levels: Dict[int, DungeonLevel] = {}
        
        # Generate the first level
        self._generate_level(1)
    
    def _generate_level(self, depth: int) -> DungeonLevel:
        """Generate a new dungeon level.
        
        Args:
            depth: The depth of the level to generate
            
        Returns:
            The generated DungeonLevel
        """
        # Create configuration with depth-based parameters
        config = self._create_config_for_depth(depth)
        
        # Choose generator type based on depth
        if depth == 1:
            # First level is always a town
            generator = TownGenerator(config)
        elif depth % 5 == 0:
            # Every 5th level is a cave
            generator = CaveGenerator(config)
        else:
            # Regular dungeon levels
            generator = DungeonGenerator(config)
        
        # Generate the level
        generator.generate()
        
        # Convert to string tiles
        tiles = self._convert_tiles(generator, depth)
        
        # Create and store the level
        level = DungeonLevel(
            depth=depth,
            width=self.width,
            height=self.height,
            generator=generator,
            tiles=tiles
        )
        
        self.levels[depth] = level
        return level
    
    def _create_config_for_depth(self, depth: int) -> MapGeneratorConfig:
        """Create map generation config based on depth.
        
        Deeper levels have:
        - More rooms
        - Larger rooms possible
        - More complex layouts
        """
        base_rooms = 10
        depth_bonus = depth * 2
        
        config = MapGeneratorConfig(
            width=self.width,
            height=self.height,
            min_room_size=4,
            max_room_size=min(12 + depth // 3, 20),  # Larger rooms deeper
            max_rooms=min(base_rooms + depth_bonus, 30),  # More rooms deeper
            diagonal_corridors=depth > 2,  # Diagonal corridors after level 2
            diagonal_chance=min(0.3 + depth * 0.05, 0.7)  # More diagonals deeper
        )
        
        # Cave-specific parameters
        if depth % 5 == 0:
            config.method = GenerationMethod.CELLULAR_AUTOMATA
            config.initial_density = 0.45 - (depth * 0.01)  # Slightly more open deeper
            
        # Town-specific parameters
        elif depth == 1:
            config.method = GenerationMethod.TOWN
            config.road_width = 3
            
        return config
    
    def _convert_tiles(self, generator, depth: int = None) -> list[list[str]]:
        """Convert TileType enum to string representation."""
        if depth is None:
            depth = self.current_depth
            
        tile_map = {
            TileType.FLOOR: '.',
            TileType.WALL: '#',
            TileType.DOOR: '+',
            TileType.STAIRS_UP: '<',
            TileType.STAIRS_DOWN: '>',
            TileType.WATER: '~',
            TileType.LAVA: '≈',
            TileType.CHEST: '□',
            TileType.ALTAR: '▲',
            TileType.EMPTY: '#'
        }
        
        tiles = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                tile_type = generator.get_tile(x, y)
                row.append(tile_map.get(tile_type, '#'))
            tiles.append(row)
        
        # Ensure the deepest level has no down stairs
        if depth >= self.max_depth:
            for y in range(self.height):
                for x in range(self.width):
                    if tiles[y][x] == '>':
                        tiles[y][x] = '.'
        
        return tiles
    
    def get_current_level(self) -> DungeonLevel:
        """Get the current dungeon level."""
        return self.levels[self.current_depth]
    
    def go_up(self) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """Go up one level.
        
        Returns:
            (success, spawn_position) - success is False if already at top
        """
        if self.current_depth <= 1:
            return False, None
        
        # Store current position on the level we're leaving
        current_level = self.get_current_level()
        # This would be set by the game when moving
        
        self.current_depth -= 1
        new_level = self.get_current_level()
        spawn_pos = new_level.get_spawn_position(from_above=False)
        
        return True, spawn_pos
    
    def go_down(self) -> Tuple[bool, Optional[Tuple[int, int]]]:
        """Go down one level.
        
        Returns:
            (success, spawn_position) - success is False if already at bottom
        """
        if self.current_depth >= self.max_depth:
            return False, None
        
        self.current_depth += 1
        
        # Generate new level if it doesn't exist
        if self.current_depth not in self.levels:
            self._generate_level(self.current_depth)
        
        new_level = self.get_current_level()
        spawn_pos = new_level.get_spawn_position(from_above=True)
        
        return True, spawn_pos
    
    def can_go_up(self) -> bool:
        """Check if we can go up from current level."""
        return self.current_depth > 1
    
    def can_go_down(self) -> bool:
        """Check if we can go down from current level."""
        return self.current_depth < self.max_depth