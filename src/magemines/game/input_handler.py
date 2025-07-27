"""Input handling for the game."""

import logging
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
    
    # Level transitions
    GO_UP_STAIRS = auto()
    GO_DOWN_STAIRS = auto()
    
    # Interactions
    OPEN_DOOR = auto()
    GATHER = auto()
    
    UNKNOWN = auto()


class InputHandler:
    """Handles keyboard input and converts to game actions."""
    
    def __init__(self):
        """Initialize input handler."""
        self.logger = logging.getLogger(__name__)
        self.awaiting_confirmation = False
        self.confirmation_action = None
        self._message_pane: Optional[MessagePane] = None
        self.logger.debug("InputHandler initialized")
        
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
            
            # Level transitions
            '<': InputAction.GO_UP_STAIRS,
            '>': InputAction.GO_DOWN_STAIRS,
            
            # Interactions
            'o': InputAction.OPEN_DOOR,
            'O': InputAction.OPEN_DOOR,
            'g': InputAction.GATHER,
            'G': InputAction.GATHER,
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
            action = self._confirm_map.get(key, InputAction.UNKNOWN)
            if action != InputAction.UNKNOWN:
                self.logger.debug(f"Confirmation key pressed: {key} -> {action.name}")
            return action
        
        # Normal key mapping
        action = self._key_map.get(key, InputAction.UNKNOWN)
        if action != InputAction.UNKNOWN:
            self.logger.debug(f"Key pressed: {key} -> {action.name}")
        return action
    
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
        
        # Handle stairs
        elif action == InputAction.GO_UP_STAIRS:
            return self._handle_stairs(player, game_map, going_down=False)
        elif action == InputAction.GO_DOWN_STAIRS:
            return self._handle_stairs(player, game_map, going_down=True)
        
        # Handle door opening
        elif action == InputAction.OPEN_DOOR:
            return self._handle_open_door(player, game_map)
        
        # Handle gathering
        elif action == InputAction.GATHER:
            return self._handle_gather(player, game_map)
        
        # Unknown action
        return False
    
    def _handle_movement(self, action: InputAction, player, game_map) -> Union[bool, str]:
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
            # Check if it's a door
            if game_map.get_tile_at(new_x, new_y) == '+':
                if self._message_pane:
                    self._message_pane.add_message(
                        "A closed door blocks your path! Press 'o' to open it.",
                        MessageCategory.WARNING
                    )
            else:
                if self._message_pane:
                    self._message_pane.add_message(
                        "A wall blocks your path!",
                        MessageCategory.WARNING
                    )
            return False
        
        # Move the player
        player.move(dx, dy)
        
        # Check if player stepped on a resource
        tile = game_map.get_tile_at(player.x, player.y)
        resource_tiles = {
            't': "wood",
            '*': "stone", 
            'o': "iron ore",
            '♦': "magic crystal",
            '◊': "arcane essence",
            '♠': "mushroom",
            '♣': "healing herbs"
        }
        
        if tile in resource_tiles:
            if self._message_pane:
                resource_name = resource_tiles[tile]
                self._message_pane.add_message(
                    f"You see some {resource_name} here. Press 'g' to gather it.",
                    MessageCategory.INFO
                )
        
        # Check if player stepped on stairs
        if game_map.is_stairs_down(player.x, player.y):
            if self._message_pane:
                if game_map.can_go_down():
                    self._message_pane.add_message(
                        "You see stairs leading down. Press '>' to descend.",
                        MessageCategory.INFO
                    )
                else:
                    self._message_pane.add_message(
                        "These stairs seem to lead nowhere...",
                        MessageCategory.INFO
                    )
        elif game_map.is_stairs_up(player.x, player.y):
            if self._message_pane:
                if game_map.can_go_up():
                    self._message_pane.add_message(
                        "You see stairs leading up. Press '<' to ascend.",
                        MessageCategory.INFO
                    )
                else:
                    self._message_pane.add_message(
                        "You are at the surface level.",
                        MessageCategory.INFO
                    )
        
        return True
    
    def _handle_stairs(self, player, game_map, going_down: bool) -> Union[bool, str]:
        """Handle using stairs to change levels."""
        # Check if player is on appropriate stairs
        if going_down and not game_map.is_stairs_down(player.x, player.y):
            if self._message_pane:
                self._message_pane.add_message(
                    "You need to be on stairs going down (>) to descend.",
                    MessageCategory.WARNING
                )
            return False
        elif not going_down and not game_map.is_stairs_up(player.x, player.y):
            if self._message_pane:
                self._message_pane.add_message(
                    "You need to be on stairs going up (<) to ascend.",
                    MessageCategory.WARNING
                )
            return False
        
        # Try to change level
        success, new_pos = game_map.change_level(going_down)
        
        if success:
            # Update player position
            player.x, player.y = new_pos
            
            # Add message about level change
            if self._message_pane:
                depth = game_map.get_current_depth()
                if going_down:
                    self._message_pane.add_message(
                        f"You descend deeper into the dungeon... (Level {depth})",
                        MessageCategory.INFO
                    )
                else:
                    self._message_pane.add_message(
                        f"You climb back towards the surface... (Level {depth})",
                        MessageCategory.INFO
                    )
            
            return "LEVEL_CHANGE"
        else:
            if self._message_pane:
                if going_down:
                    self._message_pane.add_message(
                        "You cannot go any deeper!",
                        MessageCategory.WARNING
                    )
                else:
                    self._message_pane.add_message(
                        "You are already at the surface!",
                        MessageCategory.WARNING
                    )
            return False
    
    def _handle_open_door(self, player, game_map) -> Union[bool, str]:
        """Handle opening doors."""
        # Check all adjacent tiles for doors
        directions = [
            (-1, -1), (0, -1), (1, -1),  # NW, N, NE
            (-1, 0),           (1, 0),    # W,     E
            (-1, 1),  (0, 1),  (1, 1)     # SW, S, SE
        ]
        
        doors_found = []
        for dx, dy in directions:
            x, y = player.x + dx, player.y + dy
            if 0 <= x < game_map.width and 0 <= y < game_map.height:
                if game_map.get_tile_at(x, y) == '+':
                    doors_found.append((x, y))
        
        if not doors_found:
            if self._message_pane:
                self._message_pane.add_message(
                    "There are no doors nearby to open.",
                    MessageCategory.WARNING
                )
            return False
        
        # Open all adjacent doors
        for x, y in doors_found:
            game_map.open_door(x, y)
            
        if self._message_pane:
            if len(doors_found) == 1:
                self._message_pane.add_message(
                    "You open the door.",
                    MessageCategory.SYSTEM
                )
            else:
                self._message_pane.add_message(
                    f"You open {len(doors_found)} doors.",
                    MessageCategory.SYSTEM
                )
        
        return True
    
    def process_input(self, key: str, player, game_map, game_state) -> Union[bool, str]:
        """Process a key press and return the result."""
        action = self.get_action(key)
        
        if action == InputAction.UNKNOWN:
            return False
        
        return self.handle_action(action, player, game_map, game_state)
    
    def _handle_gather(self, player, game_map) -> Union[bool, str]:
        """Handle gathering resources."""
        # Get the tile the player is standing on
        tile = game_map.get_tile_at(player.x, player.y)
        
        # Map of resource tiles to their names
        resource_tiles = {
            't': "wood",
            '*': "stone", 
            'o': "iron ore",
            '♦': "magic crystal",
            '◊': "arcane essence",
            '♠': "mushroom",
            '♣': "healing herbs"
        }
        
        if tile not in resource_tiles:
            if self._message_pane:
                self._message_pane.add_message(
                    "There's nothing here to gather.",
                    MessageCategory.WARNING
                )
            return False
        
        # Get the resource name
        resource_name = resource_tiles[tile]
        
        # For now, just pick it up instantly (later we'll add gathering time)
        # Clear the resource from the map
        game_map.tiles[player.y][player.x] = '.'
        
        if self._message_pane:
            self._message_pane.add_message(
                f"You gather some {resource_name}.",
                MessageCategory.GENERAL
            )
        
        # TODO: Add the resource to player's inventory when inventory system is ready
        
        return True


# Legacy function for compatibility
def handle_input(key, player, game_map):
    """Legacy input handler for compatibility."""
    handler = InputHandler()
    handler.process_input(key, player, game_map, None)