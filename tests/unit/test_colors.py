"""Unit tests for the color system."""

import pytest
from unittest.mock import Mock
from magemines.ui.colors import ColorPalette
from magemines.core.terminal import Color


class TestColorPalette:
    """Test the ColorPalette class."""
    
    @pytest.fixture
    def mock_terminal(self):
        """Create a mock terminal."""
        term = Mock()
        term.color_rgb = Mock(side_effect=lambda r, g, b: f"\x1b[38;2;{r};{g};{b}m")
        term.on_color_rgb = Mock(side_effect=lambda r, g, b: f"\x1b[48;2;{r};{g};{b}m")
        term.normal = "\x1b[0m"
        term.move = Mock(side_effect=lambda y, x: f"\x1b[{y};{x}H")
        return term
    
    @pytest.fixture
    def palette(self, mock_terminal):
        """Create a color palette with mock terminal."""
        return ColorPalette(mock_terminal)
    
    def test_init(self, palette):
        """Test palette initialization."""
        # Check that colors are defined
        assert palette.PLAYER == (0, 255, 0)
        assert palette.MAGE_PRIMARY == (64, 156, 255)
        assert palette.MONSTER_PRIMARY == (220, 20, 60)
        assert palette.TERRAIN_WALL == (80, 80, 80)
    
    def test_entity_colors(self, palette):
        """Test entity color mappings."""
        assert palette.get_entity_color('@') == Color(0, 255, 0)  # Player green
        assert palette.get_entity_color('M') == Color(64, 156, 255)  # Mage blue
        assert palette.get_entity_color('O') == Color(255, 0, 0)  # Boss red
        assert palette.get_entity_color('?') == Color(200, 200, 200)  # Unknown defaults to UI_TEXT
    
    def test_terrain_colors(self, palette):
        """Test terrain color mappings."""
        assert palette.get_terrain_color('#') == Color(80, 80, 80)  # Wall gray
        assert palette.get_terrain_color('.') == Color(40, 40, 40)  # Floor dark gray
        assert palette.get_terrain_color('+') == Color(139, 69, 19)  # Door brown
        assert palette.get_terrain_color('?') == Color(40, 40, 40)  # Unknown defaults to floor
    
    def test_message_colors(self, palette):
        """Test message category colors."""
        assert palette.get_message_color('system') == Color(150, 150, 150)
        assert palette.get_message_color('combat') == Color(255, 100, 100)
        assert palette.get_message_color('magic') == Color(150, 150, 255)
        assert palette.get_message_color('unknown') == Color(150, 150, 150)  # Defaults to system
    
    def test_rgb_conversion(self, palette):
        """Test RGB to terminal escape sequence conversion."""
        result = palette.rgb(255, 0, 0)
        assert result == "\x1b[38;2;255;0;0m"
    
    def test_colorize(self, palette):
        """Test text colorization."""
        # Test foreground only
        result = palette.colorize("Hello", (255, 0, 0))
        assert result == "\x1b[38;2;255;0;0mHello\x1b[0m"
        
        # Test foreground and background
        result = palette.colorize("World", (255, 255, 255), (0, 0, 0))
        assert result == "\x1b[48;2;0;0;0m\x1b[38;2;255;255;255mWorld\x1b[0m"
    
    def test_render_colored_char(self, palette):
        """Test rendering a colored character at position."""
        # Test entity character
        result = palette.render_colored_char('@', 10, 5)
        assert "\x1b[5;10H" in result  # Move cursor
        assert "\x1b[38;2;0;255;0m" in result  # Player color
        
        # Test terrain character
        result = palette.render_colored_char('#', 0, 0)
        assert "\x1b[0;0H" in result
        assert "\x1b[38;2;80;80;80m" in result  # Wall color
        
        # Test with explicit colors
        result = palette.render_colored_char('X', 5, 5, (255, 0, 0), (0, 0, 255))
        assert "\x1b[5;5H" in result
        assert "\x1b[38;2;255;0;0m" in result  # Red foreground
        assert "\x1b[48;2;0;0;255m" in result  # Blue background
    
    def test_gradient(self, palette):
        """Test color gradient generation."""
        # Test simple gradient
        gradient = palette.gradient((0, 0, 0), (255, 255, 255), 5)
        assert len(gradient) == 5
        assert gradient[0] == (0, 0, 0)  # Start color
        assert gradient[4] == (255, 255, 255)  # End color
        assert gradient[2] == (127, 127, 127)  # Middle should be gray
        
        # Test single step gradient
        gradient = palette.gradient((100, 100, 100), (200, 200, 200), 1)
        assert len(gradient) == 1
        assert gradient[0] == (100, 100, 100)
        
        # Test gradient with different color channels
        gradient = palette.gradient((255, 0, 0), (0, 0, 255), 3)
        assert gradient[0] == (255, 0, 0)  # Red
        assert gradient[1] == (127, 0, 127)  # Purple
        assert gradient[2] == (0, 0, 255)  # Blue