"""
Color system for MageMines using blessed's RGB support.

This module provides a centralized color management system with themed palettes
for different game elements (mages, spells, monsters, resources, UI).
"""

from typing import Dict, Tuple, Optional, Union
from blessed import Terminal
from ..core.terminal import Color, TerminalInterface


class ColorPalette:
    """Manages RGB color definitions for all game elements."""
    
    def __init__(self, term: Union[Terminal, TerminalInterface]):
        """Initialize color palette with terminal instance.
        
        Args:
            term: Terminal instance for color formatting
        """
        self.term = term
        self._init_color_definitions()
        self._init_color_mappings()
    
    def _init_color_definitions(self):
        """Initialize all RGB color definitions."""
        # Mage colors (blue shades)
        self.MAGE_PRIMARY = (64, 156, 255)      # Bright blue
        self.MAGE_SECONDARY = (30, 100, 200)    # Deep blue
        self.MAGE_HIGHLIGHT = (120, 180, 255)   # Light blue
        self.MAGE_SHADOW = (20, 60, 120)        # Dark blue
        
        # Divine spell effects (gold/white)
        self.DIVINE_PRIMARY = (255, 215, 0)     # Gold
        self.DIVINE_SECONDARY = (255, 255, 224) # Light yellow
        self.DIVINE_HOLY = (255, 255, 255)     # Pure white
        self.DIVINE_BLESSING = (255, 239, 150)  # Soft gold
        
        # Monster colors (red/purple)
        self.MONSTER_PRIMARY = (220, 20, 60)    # Crimson
        self.MONSTER_SECONDARY = (139, 0, 139)  # Dark magenta
        self.MONSTER_BOSS = (255, 0, 0)        # Pure red
        self.MONSTER_LESSER = (205, 92, 92)    # Indian red
        
        # Resource colors (earth tones)
        self.RESOURCE_WOOD = (139, 90, 43)     # Brown
        self.RESOURCE_STONE = (136, 140, 141)  # Gray
        self.RESOURCE_ORE = (192, 192, 192)    # Silver
        self.RESOURCE_CRYSTAL = (147, 112, 219) # Medium purple
        self.RESOURCE_ESSENCE = (64, 224, 208) # Turquoise
        
        # UI chrome colors
        self.UI_BORDER = (100, 100, 100)       # Medium gray
        self.UI_HIGHLIGHT = (255, 255, 255)    # White
        self.UI_SHADOW = (50, 50, 50)          # Dark gray
        self.UI_TEXT = (200, 200, 200)         # Light gray
        self.UI_ACCENT = (255, 165, 0)         # Orange
        
        # Message categories
        self.MSG_SYSTEM = (150, 150, 150)      # Gray
        self.MSG_ACTION = (100, 200, 100)      # Green
        self.MSG_COMBAT = (255, 100, 100)      # Light red
        self.MSG_MAGIC = (150, 150, 255)       # Light blue
        self.MSG_DIALOGUE = (255, 200, 100)    # Gold
        self.MSG_WARNING = (255, 165, 0)       # Orange
        self.MSG_ERROR = (255, 0, 0)           # Red
        
        # Terrain colors
        self.TERRAIN_WALL = (80, 80, 80)       # Dark gray
        self.TERRAIN_FLOOR = (40, 40, 40)      # Very dark gray
        self.TERRAIN_DOOR = (139, 69, 19)      # Saddle brown
        self.TERRAIN_STAIRS_UP = (200, 200, 100) # Yellow-gray
        self.TERRAIN_STAIRS_DOWN = (100, 100, 200) # Blue-gray
        self.TERRAIN_WATER = (0, 100, 200)     # Deep blue
        self.TERRAIN_LAVA = (255, 60, 0)       # Orange-red
        self.TERRAIN_CHEST = (139, 90, 43)     # Wood brown
        self.TERRAIN_ALTAR = (255, 215, 0)     # Gold
        
        # Player color
        self.PLAYER = (0, 255, 0)              # Bright green
    
    def _init_color_mappings(self):
        """Initialize mappings from game elements to colors."""
        self.entity_colors = {
            '@': self.PLAYER,
            'M': self.MAGE_PRIMARY,
            'm': self.MAGE_SECONDARY,
            'O': self.MONSTER_BOSS,
            'o': self.MONSTER_PRIMARY,
            'g': self.MONSTER_LESSER,
        }
        
        self.terrain_colors = {
            '#': self.TERRAIN_WALL,
            '.': self.TERRAIN_FLOOR,
            '+': self.TERRAIN_DOOR,
            '<': self.TERRAIN_STAIRS_UP,
            '>': self.TERRAIN_STAIRS_DOWN,
            '~': self.TERRAIN_WATER,
            '≈': self.TERRAIN_LAVA,  # ≈ symbol
            '□': self.TERRAIN_CHEST,  # □ symbol
            '▲': self.TERRAIN_ALTAR,  # ▲ symbol
        }
        
        self.resource_colors = {
            'w': self.RESOURCE_WOOD,
            's': self.RESOURCE_STONE,
            'i': self.RESOURCE_ORE,
            '*': self.RESOURCE_CRYSTAL,
            '~': self.RESOURCE_ESSENCE,
        }
    
    def rgb(self, r: int, g: int, b: int) -> str:
        """Convert RGB values to terminal color escape sequence.
        
        Args:
            r: Red value (0-255)
            g: Green value (0-255)
            b: Blue value (0-255)
            
        Returns:
            Terminal color escape sequence
        """
        return self.term.color_rgb(r, g, b)
    
    def get_color(self, rgb_tuple: Tuple[int, int, int]) -> str:
        """Get terminal color from RGB tuple.
        
        Args:
            rgb_tuple: (r, g, b) values
            
        Returns:
            Terminal color escape sequence
        """
        return self.rgb(*rgb_tuple)
    
    def colorize(self, text: str, color: Tuple[int, int, int], 
                 bg_color: Optional[Tuple[int, int, int]] = None) -> str:
        """Colorize text with foreground and optional background color.
        
        Args:
            text: Text to colorize
            color: Foreground RGB color
            bg_color: Optional background RGB color
            
        Returns:
            Colorized text string
        """
        result = self.get_color(color) + text
        if bg_color:
            bg = self.term.on_color_rgb(*bg_color)
            result = bg + result
        return result + self.term.normal
    
    def get_entity_color(self, symbol: str) -> Color:
        """Get color for an entity symbol.
        
        Args:
            symbol: Entity character symbol
            
        Returns:
            Color object
        """
        rgb = self.entity_colors.get(symbol, self.UI_TEXT)
        return Color(*rgb)
    
    def get_terrain_color(self, symbol: str) -> Color:
        """Get color for a terrain symbol.
        
        Args:
            symbol: Terrain character symbol
            
        Returns:
            Color object
        """
        rgb = self.terrain_colors.get(symbol, self.TERRAIN_FLOOR)
        return Color(*rgb)
    
    def get_message_color(self, category: str) -> Color:
        """Get color for a message category.
        
        Args:
            category: Message category (system, action, combat, etc.)
            
        Returns:
            Color object
        """
        category_colors = {
            'system': self.MSG_SYSTEM,
            'action': self.MSG_ACTION,
            'combat': self.MSG_COMBAT,
            'magic': self.MSG_MAGIC,
            'dialogue': self.MSG_DIALOGUE,
            'warning': self.MSG_WARNING,
            'error': self.MSG_ERROR,
        }
        rgb = category_colors.get(category, self.MSG_SYSTEM)
        return Color(*rgb)
    
    def render_colored_char(self, char: str, x: int, y: int,
                           fg_color: Optional[Tuple[int, int, int]] = None,
                           bg_color: Optional[Tuple[int, int, int]] = None) -> str:
        """Render a colored character at a specific position.
        
        Args:
            char: Character to render
            x: X coordinate
            y: Y coordinate
            fg_color: Foreground color (uses default if None)
            bg_color: Background color (transparent if None)
            
        Returns:
            Terminal string to render colored character at position
        """
        # Determine color based on character type if not specified
        if fg_color is None:
            if char in self.entity_colors:
                fg_color = self.entity_colors[char]
            elif char in self.terrain_colors:
                fg_color = self.terrain_colors[char]
            elif char in self.resource_colors:
                fg_color = self.resource_colors[char]
            else:
                fg_color = self.UI_TEXT
        
        # Build the colored string
        move_cursor = self.term.move(y, x)
        colored_char = self.colorize(char, fg_color, bg_color)
        
        return move_cursor + colored_char
    
    def gradient(self, start_color: Tuple[int, int, int],
                 end_color: Tuple[int, int, int],
                 steps: int) -> list[Tuple[int, int, int]]:
        """Generate a color gradient between two colors.
        
        Args:
            start_color: Starting RGB color
            end_color: Ending RGB color
            steps: Number of gradient steps
            
        Returns:
            List of RGB color tuples forming the gradient
        """
        if steps <= 1:
            return [start_color]
        
        gradient_colors = []
        for i in range(steps):
            t = i / (steps - 1)
            r = int(start_color[0] + (end_color[0] - start_color[0]) * t)
            g = int(start_color[1] + (end_color[1] - start_color[1]) * t)
            b = int(start_color[2] + (end_color[2] - start_color[2]) * t)
            gradient_colors.append((r, g, b))
        
        return gradient_colors