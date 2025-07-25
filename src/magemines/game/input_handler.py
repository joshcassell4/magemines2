"""Input handling for the game."""

from enum import Enum, auto
from typing import Optional, Union

from ..ui.message_pane import MessagePane, MessageCategory, ScrollDirection


class InputAction(Enum):
    """Possible input actions."""
    # Movement
    MOVE_NORTH = auto()
    MOVE_SOUTH = auto()
    MOVE_EAST = auto()
    MOVE_WEST = auto()
    MOVE_NORTHWEST = auto()
    MOVE_NORTHEAST = auto()
    MOVE_SOUTHWEST = auto()
    MOVE_SOUTHEAST = auto()
    WAIT = auto()
    
    # System
    QUIT = auto()
    CONFIRM_YES = auto()
    CONFIRM_NO = auto()
    
    # UI
    SCROLL_UP = auto()
    SCROLL_DOWN = auto()
    
    UNKNOWN = auto()


class InputHandler:
    """Handles keyboard input and converts to game actions."""
    
    def __init__(self):
        """Initialize input handler."""
        self.awaiting_confirmation = False
        self.confirmation_action = None
        self._message_pane: Optional[MessagePane] = None
        
        # Key mappings
        self._key_map = {
            # Vim-style movement
            'h': InputAction.MOVE_WEST,
            'j': InputAction.MOVE_SOUTH,
            'k': InputAction.MOVE_NORTH,
            'l': InputAction.MOVE_EAST,
            
            # Diagonal movement
            'y': InputAction.MOVE_NORTHWEST,
            'u': InputAction.MOVE_NORTHEAST,
            'b': InputAction.MOVE_SOUTHWEST,
            'n': InputAction.MOVE_SOUTHEAST,
            
            # Other actions
            '.': InputAction.WAIT,
            'q': InputAction.QUIT,
            'Q': InputAction.QUIT,
            
            # UI actions
            '-': InputAction.SCROLL_UP,
            '+': InputAction.SCROLL_DOWN,
            '=': InputAction.SCROLL_DOWN,  # Allow = without shift for convenience
        }
        
        # Confirmation keys
        self._confirm_map = {
            'y': InputAction.CONFIRM_YES,
            'Y': InputAction.CONFIRM_YES,
            'n': InputAction.CONFIRM_NO,
            'N': InputAction.CONFIRM_NO,
        }
    
    def set_message_pane(self, message_pane: MessagePane) -> None:
        """Set the message pane for displaying messages."""
        self._message_pane = message_pane
    
    def get_action(self, key: str) -> InputAction:
        """Convert a key press to an action."""
        # If awaiting confirmation, only accept y/n
        if self.awaiting_confirmation:
            return self._confirm_map.get(key, InputAction.UNKNOWN)
        
        # Normal key mapping
        return self._key_map.get(key, InputAction.UNKNOWN)
    
    def handle_action(
        self,
        action: InputAction,
        player,
        game_map,
        game_state
    ) -> Union[bool, str]:
        """Handle an input action.
        
        Returns:
            bool: True if action was handled, False if blocked
            str: Special return values like "QUIT"
        """
        # Handle confirmation actions
        if action == InputAction.CONFIRM_YES and self.awaiting_confirmation:
            if self.confirmation_action == InputAction.QUIT:
                self.awaiting_confirmation = False
                return "QUIT"
                
        elif action == InputAction.CONFIRM_NO and self.awaiting_confirmation:
            self.awaiting_confirmation = False
            self.confirmation_action = None
            if self._message_pane:
                self._message_pane.add_message("Quit cancelled.", MessageCategory.SYSTEM)
            return True
        
        # Block other actions during confirmation
        if self.awaiting_confirmation:
            return False
        
        # Handle movement actions
        if action in [
            InputAction.MOVE_NORTH, InputAction.MOVE_SOUTH,
            InputAction.MOVE_EAST, InputAction.MOVE_WEST,
            InputAction.MOVE_NORTHWEST, InputAction.MOVE_NORTHEAST,
            InputAction.MOVE_SOUTHWEST, InputAction.MOVE_SOUTHEAST
        ]:
            return self._handle_movement(action, player, game_map)
        
        # Handle wait
        elif action == InputAction.WAIT:
            # Just pass the turn
            return True
        
        # Handle quit
        elif action == InputAction.QUIT:
            self.awaiting_confirmation = True
            self.confirmation_action = InputAction.QUIT
            if self._message_pane:
                self._message_pane.add_message(
                    "Do you really want to quit? (y/n)",
                    MessageCategory.WARNING
                )
            return True
        
        # Handle scrolling
        elif action == InputAction.SCROLL_UP:
            if self._message_pane:
                self._message_pane.scroll(ScrollDirection.UP, 1)
            return "SCROLL"
        elif action == InputAction.SCROLL_DOWN:
            if self._message_pane:
                self._message_pane.scroll(ScrollDirection.DOWN, 1)
            return "SCROLL"
        
        # Unknown action
        return False
    
    def _handle_movement(self, action: InputAction, player, game_map) -> bool:
        """Handle movement actions."""
        # Get movement deltas
        movement_map = {
            InputAction.MOVE_NORTH: (0, -1),
            InputAction.MOVE_SOUTH: (0, 1),
            InputAction.MOVE_EAST: (1, 0),
            InputAction.MOVE_WEST: (-1, 0),
            InputAction.MOVE_NORTHWEST: (-1, -1),
            InputAction.MOVE_NORTHEAST: (1, -1),
            InputAction.MOVE_SOUTHWEST: (-1, 1),
            InputAction.MOVE_SOUTHEAST: (1, 1),
        }
        
        dx, dy = movement_map[action]
        new_x = player.x + dx
        new_y = player.y + dy
        
        # Check if movement is blocked
        if new_x < 0 or new_x >= game_map.width or new_y < 0 or new_y >= game_map.height:
            if self._message_pane:
                self._message_pane.add_message(
                    "You can't leave the map!",
                    MessageCategory.WARNING
                )
            return False
        
        if game_map.is_blocked(new_x, new_y):
            if self._message_pane:
                self._message_pane.add_message(
                    "A wall blocks your path!",
                    MessageCategory.WARNING
                )
            return False
        
        # Move the player
        player.move(dx, dy)
        return True
    
    def process_input(self, key: str, player, game_map, game_state) -> Union[bool, str]:
        """Process a key press and return the result."""
        action = self.get_action(key)
        
        if action == InputAction.UNKNOWN:
            return False
        
        return self.handle_action(action, player, game_map, game_state)


# Legacy function for compatibility
def handle_input(key, player, game_map):
    """Legacy input handler for compatibility."""
    handler = InputHandler()
    handler.process_input(key, player, game_map, None)