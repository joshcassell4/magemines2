"""Inventory display overlay for the game."""

import logging
from typing import Optional, List
from ..core.terminal import BlessedTerminal, Position, Color, TerminalChar
from ..game.components import Inventory
from ..game.resources import ResourceType, RESOURCE_PROPERTIES


class InventoryDisplay:
    """Handles rendering of the inventory overlay."""
    
    def __init__(self, terminal: BlessedTerminal):
        """Initialize the inventory display.
        
        Args:
            terminal: The blessed terminal instance
        """
        self.terminal = terminal
        self.logger = logging.getLogger(__name__)
        self.visible = False
        self._needs_redraw = True  # Track if we need to redraw
        
        # Colors
        self.border_color = Color(100, 100, 100)  # Gray border
        self.title_color = Color(255, 255, 100)   # Yellow title
        self.text_color = Color(200, 200, 200)    # Light gray text
        self.empty_color = Color(100, 100, 100)   # Dark gray for empty slots
        self.highlight_color = Color(255, 255, 255)  # White for highlights
        self.bg_color = Color(20, 20, 20)  # Dark background
        
    def toggle(self):
        """Toggle inventory visibility."""
        self.visible = not self.visible
        self._needs_redraw = True  # Need to redraw when toggling
        self.logger.info(f"Inventory toggled, visible={self.visible}")
        
    def show(self):
        """Show the inventory."""
        self.visible = True
        self._needs_redraw = True
        
    def hide(self):
        """Hide the inventory."""
        self.visible = False
        self._needs_redraw = True
        
    def mark_dirty(self):
        """Mark the inventory as needing redraw."""
        self._needs_redraw = True
    
    def render(self, inventory: Optional[Inventory]) -> None:
        """Render the inventory overlay.
        
        Args:
            inventory: The inventory component to display
        """
        self.logger.debug(f"Inventory render called, visible={self.visible}, has_inventory={inventory is not None}, needs_redraw={self._needs_redraw}")
        if not self.visible or not inventory:
            return
            
        # Only redraw if needed
        if not self._needs_redraw:
            return
            
        try:
            # Calculate overlay dimensions
            width = 60
            height = 20
            x = (self.terminal.width - width) // 2
            y = (self.terminal.height - height) // 2
            
            self.logger.debug(f"Drawing inventory at ({x}, {y}), size={width}x{height}")
            
            # Draw background box
            self._draw_box(x, y, width, height)
            
            # Draw title
            title = "INVENTORY"
            title_x = x + (width - len(title)) // 2
            self._draw_text(title_x, y, title, self.title_color, self.bg_color)
            
            # Draw inventory contents
            self._draw_inventory_contents(x + 2, y + 2, width - 4, height - 4, inventory)
            
            # Draw help text
            help_text = "Press 'i' or ESC to close"
            help_x = x + (width - len(help_text)) // 2
            self._draw_text(help_x, y + height - 1, help_text, self.text_color, self.bg_color)
            
            self.logger.debug("Inventory render completed successfully")
            # Mark as redrawn
            self._needs_redraw = False
        except Exception as e:
            self.logger.error(f"Error rendering inventory: {e}", exc_info=True)
    
    def _draw_text(self, x: int, y: int, text: str, fg_color: Color, bg_color: Optional[Color] = None) -> None:
        """Draw text at a specific position with color.
        
        Args:
            x: X position
            y: Y position  
            text: Text to draw
            fg_color: Foreground color
            bg_color: Background color (optional)
        """
        try:
            for i, char in enumerate(text):
                if x + i < self.terminal.width:
                    self.terminal.write_char(
                        Position(x + i, y),
                        TerminalChar(char, fg_color, bg_color)
                    )
        except Exception as e:
            self.logger.error(f"Error drawing text at ({x}, {y}): {e}")
    
    def _draw_box(self, x: int, y: int, width: int, height: int) -> None:
        """Draw a box with borders.
        
        Args:
            x: X position
            y: Y position
            width: Box width
            height: Box height
        """
        # Draw top border
        self._draw_text(x, y, '+' + '-' * (width - 2) + '+', self.border_color, self.bg_color)
        
        # Draw sides and clear interior
        for i in range(1, height - 1):
            # Left border
            self.terminal.write_char(
                Position(x, y + i),
                TerminalChar('|', self.border_color, self.bg_color)
            )
            # Clear interior
            for j in range(1, width - 1):
                self.terminal.write_char(
                    Position(x + j, y + i),
                    TerminalChar(' ', self.text_color, self.bg_color)
                )
            # Right border
            self.terminal.write_char(
                Position(x + width - 1, y + i),
                TerminalChar('|', self.border_color, self.bg_color)
            )
        
        # Draw bottom border
        self._draw_text(x, y + height - 1, '+' + '-' * (width - 2) + '+', self.border_color, self.bg_color)
    
    def _draw_inventory_contents(self, x: int, y: int, width: int, height: int, inventory: Inventory) -> None:
        """Draw the inventory contents.
        
        Args:
            x: Content area X position
            y: Content area Y position
            width: Content area width
            height: Content area height
            inventory: The inventory to display
        """
        # Show capacity
        capacity_text = f"Capacity: {len(inventory.stacks)}/{inventory.capacity}"
        self._draw_text(x, y, capacity_text, self.text_color, self.bg_color)
        
        # Calculate extra capacity from strength
        if hasattr(inventory, '_entity'):
            entity = inventory._entity
            stats = entity.get_component('Stats') if hasattr(entity, 'get_component') else None
            if stats and hasattr(stats, 'carrying_capacity'):
                extra = stats.carrying_capacity
                if extra > 0:
                    extra_text = f" (+{extra} from strength)"
                    self._draw_text(x + len(capacity_text), y, extra_text, self.highlight_color, self.bg_color)
        
        # Display resources
        line = 2
        if inventory.stacks:
            # Group by resource type for cleaner display
            resource_totals = {}
            for stack in inventory.stacks:
                if stack.resource_type not in resource_totals:
                    resource_totals[stack.resource_type] = 0
                resource_totals[stack.resource_type] += stack.quantity
            
            # Sort by resource type name
            sorted_resources = sorted(resource_totals.items(), 
                                    key=lambda x: RESOURCE_PROPERTIES[x[0]].name)
            
            for resource_type, total in sorted_resources:
                if line >= height - 1:
                    break
                    
                props = RESOURCE_PROPERTIES[resource_type]
                
                # Draw symbol in resource color
                self.terminal.write_char(
                    Position(x, y + line),
                    TerminalChar(props.symbol, Color(*props.color), self.bg_color)
                )
                
                # Draw name and quantity in text color
                name_text = f" {props.name}: {total}"
                self._draw_text(x + 2, y + line, name_text, self.text_color, self.bg_color)
                
                line += 1
        else:
            # Empty inventory message
            empty_msg = "Your inventory is empty"
            msg_x = x + (width - len(empty_msg)) // 2
            msg_y = y + height // 2
            self._draw_text(msg_x, msg_y, empty_msg, self.empty_color, self.bg_color)