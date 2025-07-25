"""Test game layout and screen organization."""

import pytest
from src.magemines.core.terminal import MockTerminal, Position
from src.magemines.ui.message_pane import MessagePane, MessageCategory
from src.magemines.game.map import GameMap


class TestGameLayout:
    """Test the game layout with map and message pane side by side."""
    
    def test_layout_dimensions_standard_terminal(self):
        """Test layout fits in standard 80x24 terminal."""
        # Given a standard terminal size
        term_width = 80
        term_height = 24
        
        # When calculating layout
        map_width = min(60, term_width - 25)  # Should be 55 for 80 width
        map_height = min(24, term_height - 2)  # Should be 22
        message_pane_width = min(40, term_width - map_width - 2)  # Should be 23
        message_pane_x = map_width + 1  # Should be 56
        
        # Then dimensions should fit
        assert map_width == 55
        assert map_height == 22
        assert message_pane_width == 23
        assert message_pane_x == 56
        assert map_width + message_pane_width + 2 <= term_width
    
    def test_layout_dimensions_large_terminal(self):
        """Test layout in larger terminal (120x40)."""
        # Given a large terminal
        term_width = 120
        term_height = 40
        
        # When calculating layout
        map_width = min(60, term_width - 25)  # Should be 60 (max)
        map_height = min(24, term_height - 2)  # Should be 24 (max)
        message_pane_width = min(40, term_width - map_width - 2)  # Should be 40 (max)
        message_pane_x = map_width + 1  # Should be 61
        
        # Then dimensions should use maximums
        assert map_width == 60
        assert map_height == 24
        assert message_pane_width == 40
        assert message_pane_x == 61
    
    def test_message_pane_positioning(self):
        """Test message pane is positioned to the right of the map."""
        # Given
        terminal = MockTerminal(100, 30)
        map_width = 60
        
        # When creating message pane
        message_pane = MessagePane(
            terminal,
            Position(map_width + 1, 0),  # Right of map
            40,  # width
            28   # height (term_height - 2)
        )
        
        # Then position should be correct
        assert message_pane.position.x == 61
        assert message_pane.position.y == 0
        assert message_pane.width == 40
        assert message_pane.height == 28
    
    def test_map_respects_boundaries(self):
        """Test that map only draws within its defined area."""
        # Given
        map_width = 60
        map_height = 24
        game_map = GameMap(map_width, map_height)
        
        # Then map dimensions should be respected
        assert game_map.width == map_width
        assert game_map.height == map_height
        assert len(game_map.tiles) == map_height
        assert all(len(row) == map_width for row in game_map.tiles)
    
    def test_no_overlap_between_map_and_messages(self):
        """Test that map and message pane don't overlap."""
        # Given
        terminal = MockTerminal(100, 30)
        map_width = 60
        message_pane_x = map_width + 1
        message_pane_width = 40
        
        # When calculating boundaries
        map_right_edge = map_width - 1
        message_left_edge = message_pane_x
        message_right_edge = message_pane_x + message_pane_width - 1
        
        # Then there should be no overlap
        assert map_right_edge < message_left_edge
        assert message_left_edge > map_width
        assert message_right_edge <= terminal.width


class TestMessagePaneLayout:
    """Test message pane specific layout features."""
    
    def test_message_pane_uses_full_height(self):
        """Test message pane uses full terminal height minus margins."""
        # Given
        terminal = MockTerminal(100, 30)
        term_height = terminal.height
        
        # When creating message pane
        message_pane_height = term_height - 2  # Leave margin
        message_pane = MessagePane(
            terminal,
            Position(61, 0),
            40,
            message_pane_height
        )
        
        # Then height should use most of terminal
        assert message_pane.height == 28
        assert message_pane.height == term_height - 2
    
    def test_message_pane_title_centered(self):
        """Test that message pane title is centered."""
        # Given
        terminal = MockTerminal(100, 30)
        message_pane = MessagePane(terminal, Position(61, 0), 40, 28)
        
        # When rendering
        message_pane.render()
        
        # Then title should be centered
        title = " Messages "
        expected_x = 61 + (40 - len(title)) // 2
        
        # Check that title characters are in the right positions
        for i, char in enumerate(title):
            term_char = terminal.get_char_at(Position(expected_x + i, 0))
            if term_char and term_char.char != '-':  # Skip border chars
                assert term_char.char == char
    
    def test_scroll_indicators_visible(self):
        """Test scroll indicators appear when needed."""
        # Given
        terminal = MockTerminal(100, 30)
        message_pane = MessagePane(terminal, Position(61, 0), 40, 10)
        
        # When adding many messages
        for i in range(20):
            message_pane.add_message(f"Message {i}", MessageCategory.GENERAL)
        
        # And scrolling up
        from src.magemines.ui.message_pane import ScrollDirection
        message_pane.scroll(ScrollDirection.UP, 5)
        message_pane.render()
        
        # Then scroll indicators should be present
        # Check for up indicator at top
        up_indicator = terminal.get_char_at(Position(61 + 40 - 2, 1))
        assert up_indicator is not None
        assert up_indicator.char == '^'
        
        # Check for down indicator at bottom
        down_indicator = terminal.get_char_at(Position(61 + 40 - 2, 10 - 2))
        assert down_indicator is not None
        assert down_indicator.char == 'v'


class TestLayoutAdaptation:
    """Test layout adaptation for different terminal sizes."""
    
    @pytest.mark.parametrize("term_width,term_height,expected_map_w,expected_msg_w", [
        (80, 24, 55, 23),    # Standard terminal
        (100, 30, 60, 38),   # Medium terminal
        (120, 40, 60, 40),   # Large terminal (hits max sizes)
        (60, 20, 35, 23),    # Small terminal
    ])
    def test_layout_adapts_to_terminal_size(self, term_width, term_height, 
                                           expected_map_w, expected_msg_w):
        """Test layout calculations for various terminal sizes."""
        # When calculating layout
        map_width = min(60, term_width - 25)
        map_height = min(24, term_height - 2)
        message_pane_width = min(40, term_width - map_width - 2)
        
        # Then dimensions should adapt correctly
        assert map_width == expected_map_w
        assert message_pane_width == expected_msg_w
        assert map_width + message_pane_width + 2 <= term_width