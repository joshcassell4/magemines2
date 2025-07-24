"""Tests for the terminal abstraction layer."""

import pytest
from unittest.mock import Mock, patch

from magemines.core.terminal import (
    TerminalInterface,
    BlessedTerminal,
    MockTerminal,
    Color,
    Position,
    TerminalChar,
)


class TestColor:
    """Test the Color class for RGB color handling."""
    
    def test_color_creation(self):
        """Test creating a color with RGB values."""
        color = Color(255, 128, 0)
        assert color.r == 255
        assert color.g == 128
        assert color.b == 0
        
    def test_color_validation(self):
        """Test that invalid color values raise errors."""
        with pytest.raises(ValueError):
            Color(256, 0, 0)  # Too high
        with pytest.raises(ValueError):
            Color(-1, 0, 0)  # Too low
            
    def test_color_equality(self):
        """Test color equality comparison."""
        color1 = Color(100, 150, 200)
        color2 = Color(100, 150, 200)
        color3 = Color(100, 150, 201)
        
        assert color1 == color2
        assert color1 != color3
        
    def test_color_to_hex(self):
        """Test converting color to hex string."""
        color = Color(255, 128, 0)
        assert color.to_hex() == "#FF8000"
        
    def test_predefined_colors(self):
        """Test predefined color constants."""
        assert Color.WHITE == Color(255, 255, 255)
        assert Color.BLACK == Color(0, 0, 0)
        assert Color.RED == Color(255, 0, 0)
        assert Color.GREEN == Color(0, 255, 0)
        assert Color.BLUE == Color(0, 0, 255)
        assert Color.MAGE_BLUE == Color(100, 150, 255)
        assert Color.DIVINE_GOLD == Color(255, 215, 0)


class TestPosition:
    """Test the Position class for coordinate handling."""
    
    def test_position_creation(self):
        """Test creating a position."""
        pos = Position(10, 20)
        assert pos.x == 10
        assert pos.y == 20
        
    def test_position_equality(self):
        """Test position equality comparison."""
        pos1 = Position(5, 5)
        pos2 = Position(5, 5)
        pos3 = Position(5, 6)
        
        assert pos1 == pos2
        assert pos1 != pos3
        
    def test_position_addition(self):
        """Test adding positions."""
        pos1 = Position(10, 20)
        pos2 = Position(5, 3)
        result = pos1 + pos2
        
        assert result.x == 15
        assert result.y == 23
        
    def test_position_in_bounds(self):
        """Test checking if position is in bounds."""
        pos = Position(10, 20)
        
        assert pos.in_bounds(80, 24) is True
        assert pos.in_bounds(5, 24) is False  # x out of bounds
        assert pos.in_bounds(80, 10) is False  # y out of bounds


class TestTerminalChar:
    """Test the TerminalChar class for character rendering."""
    
    def test_terminal_char_creation(self):
        """Test creating a terminal character."""
        char = TerminalChar('@', Color.RED, Color.BLACK)
        assert char.char == '@'
        assert char.fg == Color.RED
        assert char.bg == Color.BLACK
        
    def test_terminal_char_defaults(self):
        """Test default colors for terminal character."""
        char = TerminalChar('X')
        assert char.char == 'X'
        assert char.fg == Color.WHITE
        assert char.bg == Color.BLACK


class TestTerminalInterface:
    """Test the abstract terminal interface."""
    
    def test_interface_cannot_be_instantiated(self):
        """Test that the interface cannot be directly instantiated."""
        with pytest.raises(TypeError):
            TerminalInterface()
            
    def test_interface_defines_required_methods(self):
        """Test that interface defines all required methods."""
        # This test ensures the interface has the right structure
        assert hasattr(TerminalInterface, 'width')
        assert hasattr(TerminalInterface, 'height')
        assert hasattr(TerminalInterface, 'clear')
        assert hasattr(TerminalInterface, 'move_cursor')
        assert hasattr(TerminalInterface, 'write_char')
        assert hasattr(TerminalInterface, 'write_text')
        assert hasattr(TerminalInterface, 'get_key')
        assert hasattr(TerminalInterface, 'setup')
        assert hasattr(TerminalInterface, 'cleanup')


class TestMockTerminal:
    """Test the mock terminal implementation."""
    
    def test_mock_terminal_creation(self):
        """Test creating a mock terminal."""
        term = MockTerminal(width=40, height=20)
        assert term.width == 40
        assert term.height == 20
        
    def test_mock_terminal_write_char(self):
        """Test writing a character to mock terminal."""
        term = MockTerminal()
        pos = Position(10, 5)
        char = TerminalChar('@', Color.RED)
        
        term.write_char(pos, char)
        
        assert term.get_char_at(pos) == char
        assert term.buffer[(10, 5)] == char
        
    def test_mock_terminal_write_text(self):
        """Test writing text to mock terminal."""
        term = MockTerminal()
        pos = Position(5, 10)
        
        term.write_text(pos, "Hello", Color.GREEN, Color.BLACK)
        
        assert term.get_char_at(Position(5, 10)).char == 'H'
        assert term.get_char_at(Position(6, 10)).char == 'e'
        assert term.get_char_at(Position(9, 10)).char == 'o'
        assert term.get_char_at(Position(9, 10)).fg == Color.GREEN
        
    def test_mock_terminal_clear(self):
        """Test clearing the mock terminal."""
        term = MockTerminal()
        term.write_text(Position(0, 0), "Test")
        
        assert len(term.buffer) > 0
        term.clear()
        assert len(term.buffer) == 0
        
    def test_mock_terminal_move_cursor(self):
        """Test moving cursor in mock terminal."""
        term = MockTerminal()
        pos = Position(15, 8)
        
        term.move_cursor(pos)
        assert term.cursor_pos == pos
        
    def test_mock_terminal_get_screen_content(self):
        """Test getting screen content as strings."""
        term = MockTerminal(width=10, height=3)
        term.write_text(Position(0, 0), "Hello")
        term.write_text(Position(0, 1), "World")
        
        content = term.get_screen_content()
        
        assert len(content) == 3
        assert content[0] == "Hello"
        assert content[1] == "World"
        assert content[2] == ""
        
    def test_mock_terminal_input_queue(self):
        """Test input queue functionality."""
        term = MockTerminal()
        term.add_key('w')
        term.add_key('a')
        term.add_key('s')
        
        assert term.get_key() == 'w'
        assert term.get_key() == 'a'
        assert term.get_key() == 's'
        assert term.get_key() is None  # Empty queue
        
    def test_mock_terminal_operation_tracking(self):
        """Test that operations are tracked."""
        term = MockTerminal()
        
        term.clear()
        term.write_char(Position(0, 0), TerminalChar('X'))
        term.move_cursor(Position(5, 5))
        
        assert term.count_operations('clear') == 1
        assert term.count_operations('write_char') == 1
        assert term.count_operations('move_cursor') == 1


class TestBlessedTerminal:
    """Test the blessed terminal implementation."""
    
    @patch('magemines.core.terminal.Terminal')
    def test_blessed_terminal_creation(self, mock_terminal_class):
        """Test creating a blessed terminal wrapper."""
        mock_term = Mock()
        mock_term.width = 80
        mock_term.height = 24
        mock_terminal_class.return_value = mock_term
        
        term = BlessedTerminal()
        
        assert term.width == 80
        assert term.height == 24
        assert term._term == mock_term
        
    @patch('magemines.core.terminal.Terminal')
    def test_blessed_terminal_write_char_with_color(self, mock_terminal_class):
        """Test writing colored character with blessed terminal."""
        mock_term = Mock()
        mock_term.move = Mock(return_value="[MOVE]")
        mock_term.color_rgb = Mock(return_value="[FG]")
        mock_term.on_color_rgb = Mock(return_value="[BG]")
        mock_term.normal = "[NORMAL]"
        mock_term.number_of_colors = 256  # Set color support
        mock_terminal_class.return_value = mock_term
        
        term = BlessedTerminal()
        pos = Position(10, 5)
        char = TerminalChar('@', Color(255, 0, 0), Color(0, 0, 255))
        
        with patch('builtins.print') as mock_print:
            term.write_char(pos, char)
            
        mock_term.move.assert_called_with(5, 10)  # Note: y, x order
        mock_term.color_rgb.assert_called_with(255, 0, 0)
        mock_term.on_color_rgb.assert_called_with(0, 0, 255)
        
        # Should print move + colors + char + normal
        expected = "[MOVE][FG][BG]@[NORMAL]"
        mock_print.assert_called_with(expected, end='', flush=True)
        
    @patch('magemines.core.terminal.Terminal')  
    def test_blessed_terminal_setup_and_cleanup(self, mock_terminal_class):
        """Test terminal setup and cleanup."""
        mock_term = Mock()
        mock_context = Mock()
        mock_term.fullscreen.return_value = mock_context
        mock_term.cbreak.return_value = mock_context
        mock_term.hidden_cursor.return_value = mock_context
        mock_terminal_class.return_value = mock_term
        
        term = BlessedTerminal()
        
        # Test setup
        term.setup()
        mock_term.fullscreen.assert_called_once()
        mock_term.cbreak.assert_called_once()
        mock_term.hidden_cursor.assert_called_once()
        
        # Test cleanup
        term.cleanup()
        # Cleanup happens via context manager exit
        
    @patch('magemines.core.terminal.Terminal')
    def test_blessed_terminal_get_key(self, mock_terminal_class):
        """Test getting keyboard input."""
        mock_term = Mock()
        mock_term.inkey = Mock(return_value=Mock(code=None, __str__=lambda self: 'w'))
        mock_terminal_class.return_value = mock_term
        
        term = BlessedTerminal()
        key = term.get_key()
        
        assert key == 'w'
        mock_term.inkey.assert_called_once()
        
    @patch('magemines.core.terminal.Terminal')
    def test_blessed_terminal_clear(self, mock_terminal_class):
        """Test clearing the terminal."""
        mock_term = Mock()
        mock_term.clear = "[CLEAR]"
        mock_terminal_class.return_value = mock_term
        
        term = BlessedTerminal()
        
        with patch('builtins.print') as mock_print:
            term.clear()
            
        mock_print.assert_called_with("[CLEAR]", end='', flush=True)


class TestTerminalPerformance:
    """Test terminal performance characteristics."""
    
    @pytest.mark.benchmark
    def test_mock_terminal_write_performance(self, benchmark):
        """Benchmark writing many characters to mock terminal."""
        term = MockTerminal(width=100, height=50)
        
        def write_many_chars():
            for y in range(50):
                for x in range(100):
                    term.write_char(
                        Position(x, y),
                        TerminalChar('#', Color.WHITE, Color.BLACK)
                    )
                    
        result = benchmark(write_many_chars)
        
        # Should be very fast for mock terminal
        assert result is None  # Function returns None
        assert len(term.buffer) == 5000
        
    def test_partial_update_tracking(self):
        """Test tracking which positions have been updated."""
        term = MockTerminal()
        
        # Write initial state
        for x in range(10):
            term.write_char(Position(x, 0), TerminalChar('.'))
            
        term.clear_dirty()  # Reset dirty tracking
        
        # Make some changes
        term.write_char(Position(2, 0), TerminalChar('@'))
        term.write_char(Position(5, 0), TerminalChar('#'))
        
        dirty = term.get_dirty_positions()
        assert len(dirty) == 2
        assert Position(2, 0) in dirty
        assert Position(5, 0) in dirty