from magemines.ui.colors import ColorPalette
from .map_generator import MapGenerator, DungeonGenerator, MapGeneratorConfig, TileType


class GameMap:
    def __init__(self, width, height, x_offset=0, y_offset=0, use_procedural=True):
        self.width = width
        self.height = height
        self.x_offset = x_offset  # Horizontal offset for centering
        self.y_offset = y_offset  # Vertical offset for header bar
        self.tiles = [['.' for _ in range(width)] for _ in range(height)]
        self.color_palette = None  # Will be set when terminal is available
        self.generator = None  # Store generator for finding positions
        
        if use_procedural:
            # Generate procedural map
            self._generate_procedural_map()
        else:
            # Create simple bordered map (original behavior)
            self._create_simple_map()
    
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
        # Create map generator with configuration
        config = MapGeneratorConfig(
            width=self.width,
            height=self.height,
            min_room_size=4,
            max_room_size=10,
            max_rooms=15
        )
        
        # Generate the dungeon
        self.generator = DungeonGenerator(config)
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
            TileType.EMPTY: '#'  # Treat empty as wall
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
        if self.generator:
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
