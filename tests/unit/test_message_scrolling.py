"""Test message scrolling and input buffer management."""

import pytest
from unittest.mock import Mock, patch
from src.magemines.ui.message_pane import MessagePane, MessageCategory, ScrollDirection
from src.magemines.core.terminal import MockTerminal, Position
from src.magemines.game.input_handler import InputHandler, InputAction
from src.magemines.core.state import GameState


class TestMessageScrolling:
    """Test message scrolling functionality."""
    
    def test_scroll_keys_mapped_correctly(self):
        """Test that scroll keys are properly mapped."""
        # Given
        handler = InputHandler()
        
        # Then
        assert handler.get_action('-') == InputAction.SCROLL_UP
        assert handler.get_action('+') == InputAction.SCROLL_DOWN
        assert handler.get_action('=') == InputAction.SCROLL_DOWN  # Convenience
    
    def test_scroll_up_increases_offset(self):
        """Test scrolling up increases scroll offset."""
        # Given
        terminal = MockTerminal()
        pane = MessagePane(terminal, Position(0, 0), 40, 10)
        
        # Add enough messages to enable scrolling
        for i in range(20):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
        
        initial_offset = pane.scroll_offset
        
        # When scrolling up
        pane.scroll(ScrollDirection.UP, 3)
        
        # Then offset should increase
        assert pane.scroll_offset == initial_offset + 3
    
    def test_scroll_down_decreases_offset(self):
        """Test scrolling down decreases scroll offset."""
        # Given
        terminal = MockTerminal()
        pane = MessagePane(terminal, Position(0, 0), 40, 10)
        
        # Add messages and scroll up first
        for i in range(20):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
        pane.scroll(ScrollDirection.UP, 5)
        
        initial_offset = pane.scroll_offset
        
        # When scrolling down
        pane.scroll(ScrollDirection.DOWN, 2)
        
        # Then offset should decrease
        assert pane.scroll_offset == initial_offset - 2
    
    def test_scroll_respects_boundaries(self):
        """Test scrolling doesn't go beyond message boundaries."""
        # Given
        terminal = MockTerminal()
        pane = MessagePane(terminal, Position(0, 0), 40, 10)
        
        # Add limited messages
        for i in range(5):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
        
        # When trying to scroll beyond boundaries
        pane.scroll(ScrollDirection.UP, 100)
        max_offset = pane._max_scroll_offset()
        
        # Then should stop at max
        assert pane.scroll_offset == max_offset
        
        # And when scrolling down beyond bottom
        pane.scroll(ScrollDirection.DOWN, 100)
        
        # Then should stop at 0
        assert pane.scroll_offset == 0
    
    def test_new_message_resets_scroll(self):
        """Test adding a new message resets scroll to show latest."""
        # Given
        terminal = MockTerminal()
        pane = MessagePane(terminal, Position(0, 0), 40, 10)
        
        # Add messages and scroll up
        for i in range(20):
            pane.add_message(f"Message {i}", MessageCategory.GENERAL)
        pane.scroll(ScrollDirection.UP, 5)
        
        assert pane.scroll_offset > 0
        
        # When adding a new message
        pane.add_message("New message", MessageCategory.GENERAL)
        
        # Then scroll should reset to show latest
        assert pane.scroll_offset == 0
    
    def test_scroll_action_returns_scroll_marker(self):
        """Test scroll actions return 'SCROLL' marker."""
        # Given
        handler = InputHandler()
        pane = MessagePane(MockTerminal(), Position(0, 0), 40, 10)
        handler.set_message_pane(pane)
        
        # When processing scroll keys
        result_up = handler.process_input('-', None, None, GameState())
        result_down = handler.process_input('+', None, None, GameState())
        
        # Then should return scroll marker
        assert result_up == "SCROLL"
        assert result_down == "SCROLL"


class TestInputBufferManagement:
    """Test input buffer overflow prevention."""
    
    def test_input_buffer_clearing_logic(self):
        """Test that we have logic to clear input buffer."""
        # This test verifies the design pattern exists in the code
        # The actual buffer clearing happens in the game loop
        
        # Given the game loop code
        import inspect
        from src.magemines.game import game_loop
        source = inspect.getsource(game_loop.run_game)
        
        # Then it should have timeout on input
        assert "inkey(timeout=" in source
        assert "0.01" in source or "0.1" in source
        
        # And it should have buffer clearing logic
        assert "while terminal_adapter._term.inkey(timeout=0):" in source
    
    def test_turn_advances_only_on_action(self):
        """Test turn number only advances on actual actions."""
        # Given
        handler = InputHandler()
        pane = MessagePane(MockTerminal(), Position(0, 0), 40, 10)
        handler.set_message_pane(pane)
        game_state = GameState()
        initial_turn = game_state.turn.turn_number
        
        # When processing a scroll action
        result = handler.process_input('-', None, None, game_state)
        
        # Then turn should not advance
        assert result == "SCROLL"
        assert game_state.turn.turn_number == initial_turn
    
    def test_movement_blocked_shows_descriptive_message(self):
        """Test blocked movement shows specific messages."""
        # Given
        handler = InputHandler()
        terminal = MockTerminal()
        pane = MessagePane(terminal, Position(0, 0), 40, 10)
        handler.set_message_pane(pane)
        
        player = Mock(x=5, y=5)  # Not at boundary
        game_map = Mock(width=10, height=10)
        game_map.is_blocked.return_value = True
        
        # When trying to move into a wall
        handler._handle_movement(InputAction.MOVE_WEST, player, game_map)
        
        # Then should show specific message
        assert len(pane.messages) == 1
        assert "wall blocks your path" in pane.messages[0].text.lower()
    
    def test_map_boundary_shows_different_message(self):
        """Test map boundary shows different message than walls."""
        # Given
        handler = InputHandler()
        terminal = MockTerminal()
        pane = MessagePane(terminal, Position(0, 0), 40, 10)
        handler.set_message_pane(pane)
        
        player = Mock(x=0, y=0)
        game_map = Mock(width=10, height=10)
        
        # When trying to move outside map
        handler._handle_movement(InputAction.MOVE_WEST, player, game_map)
        
        # Then should show boundary message
        assert len(pane.messages) == 1
        assert "can't leave the map" in pane.messages[0].text.lower()


class TestTurnTickMessages:
    """Test turn tick message formatting."""
    
    def test_messages_show_turn_number(self):
        """Test non-system messages show turn number."""
        # Given
        terminal = MockTerminal()
        pane = MessagePane(terminal, Position(0, 0), 40, 10)
        pane._current_turn = 5
        
        # When adding a general message
        pane.add_message("You move north.", MessageCategory.GENERAL)
        
        # Then formatted message should include turn
        formatted = pane.messages[-1].format()
        assert "[T5]" in formatted
        assert "You move north." in formatted
    
    def test_system_messages_no_turn_prefix(self):
        """Test system messages don't show turn prefix."""
        # Given
        terminal = MockTerminal()
        pane = MessagePane(terminal, Position(0, 0), 40, 10)
        pane._current_turn = 5
        
        # When adding a system message
        pane.add_message("Welcome to MageMines!", MessageCategory.SYSTEM)
        
        # Then formatted message should not include turn
        formatted = pane.messages[-1].format()
        assert "[T5]" not in formatted
        assert formatted == "Welcome to MageMines!"
    
    def test_turn_number_updates_correctly(self):
        """Test turn numbers update as game progresses."""
        # Given
        terminal = MockTerminal()
        pane = MessagePane(terminal, Position(0, 0), 40, 10)
        
        # When adding messages at different turns
        pane._current_turn = 1
        pane.add_message("Turn 1 action", MessageCategory.GENERAL)
        
        pane._current_turn = 2
        pane.add_message("Turn 2 action", MessageCategory.GENERAL)
        
        pane._current_turn = 3
        pane.add_message("Turn 3 action", MessageCategory.GENERAL)
        
        # Then messages should have correct turn numbers
        assert pane.messages[0].turn == 1
        assert pane.messages[1].turn == 2
        assert pane.messages[2].turn == 3
        
        # And formatting should show correct prefixes
        assert "[T1]" in pane.messages[0].format()
        assert "[T2]" in pane.messages[1].format()
        assert "[T3]" in pane.messages[2].format()