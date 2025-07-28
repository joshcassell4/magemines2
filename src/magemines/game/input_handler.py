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
    
    # UI
    SHOW_INVENTORY = auto()
    
    UNKNOWN = auto()


class InputHandler:
    """Handles keyboard input and converts to game actions."""
    
    def __init__(self):
        """Initialize input handler."""
        self.logger = logging.getLogger(__name__)
        self.awaiting_confirmation = False
        self.confirmation_action = None
        self._message_pane: Optional[MessagePane] = None
        self.inventory_visible = False
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
            
            # UI
            'i': InputAction.SHOW_INVENTORY,
            'I': InputAction.SHOW_INVENTORY,
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
        self.logger.debug(f"get_action called with key: '{key}'")
        
        # If inventory is visible, handle special keys
        if self.inventory_visible:
            if key == 'KEY_ESCAPE' or key == '\x1b':  # ESC key
                return InputAction.SHOW_INVENTORY  # Toggle it off
            elif key in ['i', 'I']:
                return InputAction.SHOW_INVENTORY  # Toggle it off
            # Block other actions while inventory is open
            return InputAction.UNKNOWN
        
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
        else:
            self.logger.debug(f"Unknown key pressed: '{key}'")
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
        self.logger.debug(f"handle_action called with action: {action.name}")
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
        
        # Handle inventory
        elif action == InputAction.SHOW_INVENTORY:
            self.inventory_visible = not self.inventory_visible
            return "SHOW_INVENTORY"
        
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
            's': "stone", 
            'o': "iron ore",
            '*': "magical gems",  # Could be crystal or essence  
            'm': "mushroom",
            'h': "healing herbs"
        }
        
        if tile in resource_tiles:
            if self._message_pane:
                resource_name = resource_tiles[tile]
                # Special handling for '*' to determine exact type
                if tile == '*' and game_map.generator:
                    from ..game.map_generation import TileType
                    tile_type = game_map.generator.get_tile(player.x, player.y)
                    if tile_type == TileType.RESOURCE_CRYSTAL:
                        resource_name = "magic crystal"
                    elif tile_type == TileType.RESOURCE_ESSENCE:
                        resource_name = "arcane essence"
                
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
        from ..game.resources import ResourceType, RESOURCE_PROPERTIES
        from ..game.map_generation import TileType
        from ..game.components import Gatherer, Inventory
        
        self.logger.debug(f"_handle_gather called at position ({player.x}, {player.y})")
        
        # Get the tile the player is standing on
        tile = game_map.get_tile_at(player.x, player.y)
        self.logger.debug(f"Tile at player position: '{tile}'")
        
        # Map of resource tiles to ResourceType
        resource_tile_map = {
            't': ResourceType.WOOD,
            's': ResourceType.STONE, 
            'o': ResourceType.ORE,
            '*': None,  # Special handling needed - could be crystal or essence
            'm': ResourceType.FOOD,     # mushroom
            'h': ResourceType.HERBS
        }
        
        if tile not in resource_tile_map:
            if self._message_pane:
                self._message_pane.add_message(
                    "There's nothing here to gather.",
                    MessageCategory.WARNING
                )
            return False
        
        # Get the resource type
        resource_type = resource_tile_map[tile]
        
        # Special handling for '*' symbol (crystal or essence)
        if tile == '*' and game_map.generator:
            # Check the actual tile type from the generator
            tile_type = game_map.generator.get_tile(player.x, player.y)
            if tile_type == TileType.RESOURCE_CRYSTAL:
                resource_type = ResourceType.CRYSTAL
            elif tile_type == TileType.RESOURCE_ESSENCE:
                resource_type = ResourceType.ESSENCE
            else:
                # Default to crystal if we can't determine
                resource_type = ResourceType.CRYSTAL
        elif tile == '*':
            # No generator available, default to crystal
            resource_type = ResourceType.CRYSTAL
            
        if resource_type is None:
            return False
            
        props = RESOURCE_PROPERTIES[resource_type]
        
        # Check if player has required tool
        gatherer = player.get_component(Gatherer)
        self.logger.debug(f"Gatherer component: {gatherer}")
        self.logger.debug(f"Tool required: {props.tool_required}")
        if gatherer:
            self.logger.debug(f"Player tools: {gatherer.tools}")
            self.logger.debug(f"Can gather: {gatherer.can_gather(props.tool_required)}")
        
        if gatherer and not gatherer.can_gather(props.tool_required):
            if self._message_pane:
                self._message_pane.add_message(
                    f"You need a {props.tool_required} to gather {props.name}.",
                    MessageCategory.WARNING
                )
            return False
        
        # Calculate yield (for now, use average)
        import random
        yield_amount = random.randint(props.min_yield, props.max_yield)
        
        # Add to inventory
        inventory = player.get_component(Inventory)
        if inventory:
            overflow = inventory.add_resource(resource_type, yield_amount)
            
            # Clear the resource from the map
            game_map.tiles[player.y][player.x] = '.'
            
            if overflow > 0:
                actual_gathered = yield_amount - overflow
                if self._message_pane:
                    self._message_pane.add_message(
                        f"You gather {actual_gathered} {props.name}. ({overflow} couldn't fit!)",
                        MessageCategory.WARNING
                    )
            else:
                # Show total count
                total = inventory.get_resource_count(resource_type)
                if self._message_pane:
                    self._message_pane.add_message(
                        f"You gather {yield_amount} {props.name}. [Total: {total}]",
                        MessageCategory.GENERAL
                    )
        
        return True


# Legacy function for compatibility
def handle_input(key, player, game_map):
    """Legacy input handler for compatibility."""
    handler = InputHandler()
    handler.process_input(key, player, game_map, None)