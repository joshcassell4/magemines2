from magemines.ui.colors import ColorPalette


class GameMap:
    def __init__(self, width, height, y_offset=0):
        self.width = width
        self.height = height
        self.y_offset = y_offset  # Offset for header bar
        self.tiles = [['.' for _ in range(width)] for _ in range(height)]
        self.color_palette = None  # Will be set when terminal is available
        
        # Create walls
        for x in range(width):
            self.tiles[0][x] = '#'
            self.tiles[height - 1][x] = '#'
        for y in range(height):
            self.tiles[y][0] = '#'
            self.tiles[y][width - 1] = '#'

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
                # Apply y_offset for header bar
                print(self.color_palette.render_colored_char(tile, x, y + self.y_offset), end='', flush=True)

    def draw_player(self, term, player):
        """Draw player with color."""
        if self.color_palette is None:
            self.set_color_palette(term)
            
        # Apply y_offset for header bar
        print(self.color_palette.render_colored_char('@', player.x, player.y + self.y_offset), end='', flush=True)

    def clear_player(self, term, player):
        """Clear player position by redrawing the tile underneath."""
        if self.color_palette is None:
            self.set_color_palette(term)
            
        tile = self.tiles[player.y][player.x]
        # Apply y_offset for header bar
        print(self.color_palette.render_colored_char(tile, player.x, player.y + self.y_offset), end='', flush=True)

    def is_blocked(self, x, y):
        return self.tiles[y][x] == '#'
