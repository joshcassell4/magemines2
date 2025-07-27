"""Level management system for multi-level dungeons."""

import logging
from typing import Dict, Tuple, Optional
from .dungeon_level import DungeonLevel
from .map_generation import (
    MapGeneratorConfig, GenerationMethod, TileType, create_generator
)
from ..core.config import get_config, ConfigSection


class LevelManager:
    """Manages multiple dungeon levels and transitions between them."""
    
    def __init__(self, width: int, height: int, max_depth: int = 10):
        """Initialize the level manager.
        
        Args:
            width: Width of each level
            height: Height of each level
            max_depth: Maximum dungeon depth
        """
        self.logger = logging.getLogger(__name__)
        self.width = width
        self.height = height
        self.max_depth = max_depth
        self.current_depth = 1
        self.levels: Dict[int, DungeonLevel] = {}
        self.message_pane = None  # Will be set later if available
        
        self.logger.info(f"LevelManager initialized: {width}x{height}, max_depth={max_depth}")
        
        # Generate the first level
        self._generate_level(1)
    
    def set_message_pane(self, message_pane):
        """Set the message pane for debug output."""
        self.message_pane = message_pane
    
    def _generate_level(self, depth: int) -> DungeonLevel:
        """Generate a new dungeon level.
        
        Args:
            depth: The depth of the level to generate
            
        Returns:
            The generated DungeonLevel
        """
        self.logger.info(f"Generating level {depth}")
        # Create configuration with depth-based parameters
        config = self._create_config_for_depth(depth)
        
        # Choose generator type based on depth
        if depth == 1:
            # First level is always a town
            config.method = GenerationMethod.TOWN
        elif depth % 5 == 0:
            # Every 5th level is a cave
            config.method = GenerationMethod.CELLULAR_AUTOMATA
        else:
            # Regular dungeon levels
            config.method = GenerationMethod.ROOMS_AND_CORRIDORS
            
        # Create generator using factory
        generator = create_generator(config, self.message_pane)
        
        # Generate the level
        generator.generate()
        
        # Place resources on the map
        generator.place_resources(depth)
        
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
        # Load configuration
        map_config = get_config(ConfigSection.MAP_GENERATION)
        
        # Calculate depth-based scaling
        depth_bonus = int(depth * map_config.rooms_per_level)
        
        config = MapGeneratorConfig(
            width=self.width,
            height=self.height,
            min_room_size=map_config.min_room_size,
            max_room_size=min(map_config.max_room_size + depth // 3, 20),  # Larger rooms deeper
            max_rooms=min(map_config.max_rooms_base + depth_bonus, 30),  # More rooms deeper
            diagonal_corridors=depth > 2 and map_config.corridor_style in ["diagonal", "mixed"],
            diagonal_chance=min(0.3 + depth * 0.05, 0.7) if map_config.corridor_style == "mixed" else 1.0
        )
        
        # Cave-specific parameters
        if depth % map_config.cave_frequency == 0:
            config.method = GenerationMethod.CELLULAR_AUTOMATA
            config.initial_density = map_config.cave_fill_probability - (depth * 0.01)  # Slightly more open deeper
            
        # Town-specific parameters
        elif depth == 1:
            config.method = GenerationMethod.TOWN
            config.road_width = map_config.town_street_width
            
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
            TileType.EMPTY: '#',
            # Resources
            TileType.RESOURCE_WOOD: 't',
            TileType.RESOURCE_STONE: '*',
            TileType.RESOURCE_ORE: 'o',
            TileType.RESOURCE_CRYSTAL: '♦',
            TileType.RESOURCE_ESSENCE: '◊',
            TileType.RESOURCE_MUSHROOM: '♠',
            TileType.RESOURCE_HERBS: '♣'
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
            self.logger.debug("Cannot go up - already at surface level")
            return False, None
        
        # Store current position on the level we're leaving
        current_level = self.get_current_level()
        # This would be set by the game when moving
        
        self.current_depth -= 1
        self.logger.info(f"Moving up to level {self.current_depth}")
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