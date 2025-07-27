import logging
from magemines.ui.colors import ColorPalette
from .map_generation import MapGenerator, DungeonGenerator, MapGeneratorConfig, TileType
from .level_manager import LevelManager
from .dungeon_level import DungeonLevel
from ..core.config import get_config, ConfigSection


class GameMap:
    def __init__(self, width, height, x_offset=0, y_offset=0, use_procedural=True, use_levels=False):
        self.logger = logging.getLogger(__name__)
        self.width = width
        self.height = height
        self.x_offset = x_offset  # Horizontal offset for centering
        self.y_offset = y_offset  # Vertical offset for header bar
        self.tiles = [['.' for _ in range(width)] for _ in range(height)]
        self.color_palette = None  # Will be set when terminal is available
        self.generator = None  # Store generator for finding positions
        self.level_manager = None  # For multi-level dungeons
        self.use_levels = use_levels
        self.message_pane = None  # Will be set later if available
        
        self.logger.info(f"Creating GameMap: {width}x{height}, use_levels={use_levels}, use_procedural={use_procedural}")
        
        if use_levels:
            # Initialize level manager
            self.level_manager = LevelManager(width, height)
            self._load_current_level()
        elif use_procedural:
            # Generate procedural map
            self._generate_procedural_map()
        else:
            # Create simple bordered map (original behavior)
            self._create_simple_map()
    
    def set_message_pane(self, message_pane):
        """Set the message pane for debug output."""
        self.message_pane = message_pane
        # Message pane is kept for compatibility but no longer used for debug
        # Debug messages now go to log files
    
    def _create_simple_map(self):
        """Create a simple map with walls around the border."""
        # Create walls
        for x in range(self.width):
            self.tiles[0][x] = '#'
            self.tiles[self.height - 1][x] = '#'
        for y in range(self.height):
            self.tiles[y][0] = '#'
            self.tiles[y][self.width - 1] = '#'
    
    def _generate_procedural_map(self):
        """Generate a procedural dungeon map."""
        self.logger.info("Generating procedural map")
        # Load map generation configuration
        map_config = get_config(ConfigSection.MAP_GENERATION)
        
        # Create map generator with configuration
        config = MapGeneratorConfig(
            width=self.width,
            height=self.height,
            min_room_size=map_config.min_room_size,
            max_room_size=map_config.max_room_size,
            max_rooms=map_config.max_rooms_base
        )
        
        # Generate the dungeon
        self.generator = DungeonGenerator(config, self.message_pane)
        self.generator.generate()
        
        # Convert TileType enum to string representation
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
            TileType.EMPTY: '#',  # Treat empty as wall
            # Resources
            TileType.RESOURCE_WOOD: 't',
            TileType.RESOURCE_STONE: '*',
            TileType.RESOURCE_ORE: 'o',
            TileType.RESOURCE_CRYSTAL: '♦',
            TileType.RESOURCE_ESSENCE: '◊',
            TileType.RESOURCE_MUSHROOM: '♠',
            TileType.RESOURCE_HERBS: '♣'
        }
        
        # Copy generated tiles to our map
        for y in range(self.height):
            for x in range(self.width):
                tile_type = self.generator.get_tile(x, y)
                self.tiles[y][x] = tile_map.get(tile_type, '#')

    def set_color_palette(self, term):
        """Initialize color palette with terminal instance.
        
        Args:
            term: Blessed terminal instance
        """
        self.color_palette = ColorPalette(term)

    def draw_static(self, term):
        """Draw all static map elements with colors."""
        if self.color_palette is None:
            self.set_color_palette(term)
            
        for y in range(self.height):
            for x in range(self.width):
                tile = self.tiles[y][x]
                # Apply both x and y offsets
                print(self.color_palette.render_colored_char(tile, x + self.x_offset, y + self.y_offset), end='', flush=True)

    def draw_player(self, term, player):
        """Draw player with color."""
        if self.color_palette is None:
            self.set_color_palette(term)
            
        # Apply both x and y offsets
        print(self.color_palette.render_colored_char('@', player.x + self.x_offset, player.y + self.y_offset), end='', flush=True)

    def clear_player(self, term, player):
        """Clear player position by redrawing the tile underneath."""
        if self.color_palette is None:
            self.set_color_palette(term)
            
        tile = self.tiles[player.y][player.x]
        # Apply both x and y offsets
        print(self.color_palette.render_colored_char(tile, player.x + self.x_offset, player.y + self.y_offset), end='', flush=True)

    def is_blocked(self, x, y):
        # Walls and closed doors block movement
        return self.tiles[y][x] in ['#', '+']
    
    def get_starting_position(self):
        """Get a suitable starting position for the player.
        
        Returns the position of the up stairs if using procedural generation,
        otherwise returns a default position.
        """
        if self.use_levels and self.level_manager:
            # Get starting position from current level
            level = self.level_manager.get_current_level()
            return level.get_spawn_position(from_above=True)
        elif self.generator:
            # Look for up stairs
            for y in range(self.height):
                for x in range(self.width):
                    if self.tiles[y][x] == '<':
                        return (x, y)
            
            # Fall back to finding an empty position
            pos = self.generator.find_empty_position()
            if pos:
                return pos
        
        # Default position for simple maps
        return (10, 10)
    
    def _load_current_level(self):
        """Load the current level from the level manager."""
        if not self.level_manager:
            return
        
        current_level = self.level_manager.get_current_level()
        self.tiles = current_level.tiles
        self.generator = current_level.generator
    
    def get_tile_at(self, x, y):
        """Get the tile at the given position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.tiles[y][x]
        return '#'
    
    def is_stairs_up(self, x, y):
        """Check if the position has stairs going up."""
        return self.get_tile_at(x, y) == '<'
    
    def is_stairs_down(self, x, y):
        """Check if the position has stairs going down."""
        return self.get_tile_at(x, y) == '>'
    
    def get_current_depth(self):
        """Get the current dungeon depth."""
        if self.level_manager:
            return self.level_manager.current_depth
        return 1
    
    def can_go_up(self):
        """Check if we can go up a level."""
        return self.level_manager and self.level_manager.can_go_up()
    
    def can_go_down(self):
        """Check if we can go down a level."""
        return self.level_manager and self.level_manager.can_go_down()
    
    def change_level(self, going_down=True):
        """Change to a different level.
        
        Args:
            going_down: True to go down, False to go up
            
        Returns:
            (success, new_player_position) or (False, None) if can't change
        """
        if not self.level_manager:
            return False, None
        
        if going_down:
            success, new_pos = self.level_manager.go_down()
        else:
            success, new_pos = self.level_manager.go_up()
        
        if success:
            self._load_current_level()
            return True, new_pos
        
        return False, None
    
    def open_door(self, x, y):
        """Open a door at the given position."""
        if 0 <= x < self.width and 0 <= y < self.height:
            if self.tiles[y][x] == '+':
                self.tiles[y][x] = '.'  # Convert door to floor
                return True
        return False
