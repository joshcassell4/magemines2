"""Tests for input handling."""

import pytest
from unittest.mock import Mock, MagicMock

from magemines.game.input_handler import InputHandler, InputAction
from magemines.game.player import Player
from magemines.game.map import GameMap
from magemines.core.state import GameState, GamePhase
from magemines.ui.message_pane import MessagePane


class TestInputAction:
    """Test input action enum."""
    
    def test_input_actions_exist(self):
        """Test all input actions are defined."""
        assert InputAction.MOVE_NORTH
        assert InputAction.MOVE_SOUTH
        assert InputAction.MOVE_EAST
        assert InputAction.MOVE_WEST
        assert InputAction.MOVE_NORTHWEST
        assert InputAction.MOVE_NORTHEAST
        assert InputAction.MOVE_SOUTHWEST
        assert InputAction.MOVE_SOUTHEAST
        assert InputAction.WAIT
        assert InputAction.QUIT
        assert InputAction.CONFIRM_YES
        assert InputAction.CONFIRM_NO
        assert InputAction.UNKNOWN


class TestInputHandler:
    """Test the input handler."""
    
    def test_input_handler_creation(self):
        """Test creating input handler."""
        handler = InputHandler()
        assert handler is not None
        assert handler.awaiting_confirmation is False
        assert handler.confirmation_action is None
        
    def test_movement_keys(self):
        """Test vim-style movement keys."""
        handler = InputHandler()
        
        # Basic movement
        assert handler.get_action('h') == InputAction.MOVE_WEST
        assert handler.get_action('j') == InputAction.MOVE_SOUTH
        assert handler.get_action('k') == InputAction.MOVE_NORTH
        assert handler.get_action('l') == InputAction.MOVE_EAST
        
        # Diagonal movement
        assert handler.get_action('y') == InputAction.MOVE_NORTHWEST
        assert handler.get_action('u') == InputAction.MOVE_NORTHEAST
        assert handler.get_action('b') == InputAction.MOVE_SOUTHWEST
        assert handler.get_action('n') == InputAction.MOVE_SOUTHEAST
        
        # Wait
        assert handler.get_action('.') == InputAction.WAIT
        
    def test_quit_key(self):
        """Test quit key."""
        handler = InputHandler()
        assert handler.get_action('q') == InputAction.QUIT
        assert handler.get_action('Q') == InputAction.QUIT
        
    def test_unknown_key(self):
        """Test unknown keys."""
        handler = InputHandler()
        assert handler.get_action('x') == InputAction.UNKNOWN
        assert handler.get_action('?') == InputAction.UNKNOWN
        assert handler.get_action('w') == InputAction.UNKNOWN  # Old movement key
        
    def test_handle_movement(self):
        """Test handling movement actions."""
        handler = InputHandler()
        player = Mock()
        game_map = Mock()
        game_state = Mock()
        
        # Mock the map to allow movement
        game_map.is_blocked.return_value = False
        player.x = 10
        player.y = 10
        
        # Test north movement
        result = handler.handle_action(
            InputAction.MOVE_NORTH,
            player,
            game_map,
            game_state
        )
        
        assert result is True  # Action was handled
        player.move.assert_called_once_with(0, -1)
        
    def test_handle_blocked_movement(self):
        """Test handling blocked movement."""
        handler = InputHandler()
        player = Mock()
        game_map = Mock()
        game_state = Mock()
        message_pane = Mock()
        
        handler.set_message_pane(message_pane)
        
        # Mock the map to block movement
        game_map.is_blocked.return_value = True
        player.x = 10
        player.y = 10
        
        # Test blocked movement
        result = handler.handle_action(
            InputAction.MOVE_NORTH,
            player,
            game_map,
            game_state
        )
        
        assert result is False  # Action was blocked
        player.move.assert_not_called()
        message_pane.add_message.assert_called_once()
        
    def test_diagonal_movement(self):
        """Test diagonal movement."""
        handler = InputHandler()
        player = Mock()
        game_map = Mock()
        game_state = Mock()
        
        game_map.is_blocked.return_value = False
        player.x = 10
        player.y = 10
        
        # Test northwest movement
        handler.handle_action(
            InputAction.MOVE_NORTHWEST,
            player,
            game_map,
            game_state
        )
        
        player.move.assert_called_with(-1, -1)
        
    def test_wait_action(self):
        """Test wait action."""
        handler = InputHandler()
        player = Mock()
        game_map = Mock()
        game_state = Mock()
        
        result = handler.handle_action(
            InputAction.WAIT,
            player,
            game_map,
            game_state
        )
        
        assert result is True
        # Player shouldn't move when waiting
        player.move.assert_not_called()
        
    def test_quit_confirmation_start(self):
        """Test starting quit confirmation."""
        handler = InputHandler()
        player = Mock()
        game_map = Mock()
        game_state = Mock()
        message_pane = Mock()
        
        handler.set_message_pane(message_pane)
        
        # Handle quit action
        result = handler.handle_action(
            InputAction.QUIT,
            player,
            game_map,
            game_state
        )
        
        assert result is True
        assert handler.awaiting_confirmation is True
        assert handler.confirmation_action == InputAction.QUIT
        
        # Should show confirmation message
        message_pane.add_message.assert_called()
        call_args = message_pane.add_message.call_args[0]
        assert "really want to quit" in call_args[0].lower()
        
    def test_quit_confirmation_yes(self):
        """Test confirming quit."""
        handler = InputHandler()
        player = Mock()
        game_map = Mock()
        game_state = Mock()
        
        # Set up confirmation state
        handler.awaiting_confirmation = True
        handler.confirmation_action = InputAction.QUIT
        
        # Confirm with 'y'
        action = handler.get_action('y')
        assert action == InputAction.CONFIRM_YES
        
        result = handler.handle_action(
            action,
            player,
            game_map,
            game_state
        )
        
        assert result == "QUIT"  # Special return value to signal quit
        assert handler.awaiting_confirmation is False
        
    def test_quit_confirmation_no(self):
        """Test canceling quit."""
        handler = InputHandler()
        player = Mock()
        game_map = Mock()
        game_state = Mock()
        message_pane = Mock()
        
        handler.set_message_pane(message_pane)
        
        # Set up confirmation state
        handler.awaiting_confirmation = True
        handler.confirmation_action = InputAction.QUIT
        
        # Cancel with 'n'
        action = handler.get_action('n')
        assert action == InputAction.CONFIRM_NO
        
        result = handler.handle_action(
            action,
            player,
            game_map,
            game_state
        )
        
        assert result is True
        assert handler.awaiting_confirmation is False
        message_pane.add_message.assert_called_with("Quit cancelled.", "system")
        
    def test_movement_during_confirmation(self):
        """Test that movement is blocked during confirmation."""
        handler = InputHandler()
        player = Mock()
        game_map = Mock()
        game_state = Mock()
        
        # Set up confirmation state
        handler.awaiting_confirmation = True
        handler.confirmation_action = InputAction.QUIT
        
        # Try to move
        result = handler.handle_action(
            InputAction.MOVE_NORTH,
            player,
            game_map,
            game_state
        )
        
        assert result is False
        player.move.assert_not_called()
        
    def test_process_input_integration(self):
        """Test the full input processing flow."""
        handler = InputHandler()
        player = Mock()
        game_map = Mock()
        game_state = Mock()
        
        game_map.is_blocked.return_value = False
        player.x = 5
        player.y = 5
        
        # Process a movement key
        result = handler.process_input('h', player, game_map, game_state)
        assert result is True
        player.move.assert_called_with(-1, 0)
        
        # Process quit
        result = handler.process_input('q', player, game_map, game_state)
        assert result is True
        assert handler.awaiting_confirmation is True
        
        # Confirm quit
        result = handler.process_input('y', player, game_map, game_state)
        assert result == "QUIT"