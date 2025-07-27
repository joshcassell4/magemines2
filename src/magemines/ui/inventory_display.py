"""Inventory display overlay for the game."""

import logging
from typing import Optional, List
from ..core.terminal import BlessedTerminal, Position, Color
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
        
        # Colors
        self.border_color = Color(100, 100, 100)  # Gray border
        self.title_color = Color(255, 255, 100)   # Yellow title
        self.text_color = Color(200, 200, 200)    # Light gray text
        self.empty_color = Color(100, 100, 100)   # Dark gray for empty slots
        self.highlight_color = Color(255, 255, 255)  # White for highlights
        
    def toggle(self):
        """Toggle inventory visibility."""
        self.visible = not self.visible
        
    def show(self):
        """Show the inventory."""
        self.visible = True
        
    def hide(self):
        """Hide the inventory."""
        self.visible = False
    
    def render(self, inventory: Optional[Inventory]) -> None:
        """Render the inventory overlay.
        
        Args:
            inventory: The inventory component to display
        """
        if not self.visible or not inventory:
            return
            
        # Calculate overlay dimensions
        width = 60
        height = 20
        x = (self.terminal.width - width) // 2
        y = (self.terminal.height - height) // 2
        
        # Draw background box
        self._draw_box(x, y, width, height)
        
        # Draw title
        title = "INVENTORY"
        title_x = x + (width - len(title)) // 2
        with self.terminal.location(title_x, y):
            print(self.terminal.color_rgb(*self.title_color.rgb) + title + self.terminal.normal)
        
        # Draw inventory contents
        self._draw_inventory_contents(x + 2, y + 2, width - 4, height - 4, inventory)
        
        # Draw help text
        help_text = "Press 'i' or ESC to close"
        help_x = x + (width - len(help_text)) // 2
        with self.terminal.location(help_x, y + height - 1):
            print(self.terminal.color_rgb(*self.text_color.rgb) + help_text + self.terminal.normal)
    
    def _draw_box(self, x: int, y: int, width: int, height: int) -> None:
        """Draw a box with borders.
        
        Args:
            x: X position
            y: Y position
            width: Box width
            height: Box height
        """
        term = self.terminal
        border_style = term.color_rgb(*self.border_color.rgb)
        
        # Top border
        with term.location(x, y):
            print(border_style + '╔' + '═' * (width - 2) + '╗' + term.normal)
        
        # Side borders and clear interior
        for i in range(1, height - 1):
            with term.location(x, y + i):
                print(border_style + '║' + term.normal + ' ' * (width - 2) + border_style + '║' + term.normal)
        
        # Bottom border
        with term.location(x, y + height - 1):
            print(border_style + '╚' + '═' * (width - 2) + '╝' + term.normal)
    
    def _draw_inventory_contents(self, x: int, y: int, width: int, height: int, inventory: Inventory) -> None:
        """Draw the inventory contents.
        
        Args:
            x: Content area X position
            y: Content area Y position
            width: Content area width
            height: Content area height
            inventory: The inventory to display
        """
        term = self.terminal
        
        # Show capacity
        capacity_text = f"Capacity: {len(inventory.stacks)}/{inventory.capacity}"
        with term.location(x, y):
            print(term.color_rgb(*self.text_color.rgb) + capacity_text + term.normal)
        
        # Calculate extra capacity from strength
        if hasattr(inventory, '_entity'):
            entity = inventory._entity
            stats = entity.get_component('Stats') if hasattr(entity, 'get_component') else None
            if stats and hasattr(stats, 'carrying_capacity'):
                extra = stats.carrying_capacity
                if extra > 0:
                    extra_text = f" (+{extra} from strength)"
                    with term.location(x + len(capacity_text), y):
                        print(term.color_rgb(*self.highlight_color.rgb) + extra_text + term.normal)
        
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
                
                # Format: [symbol] Resource Name: quantity
                resource_line = f"{props.symbol} {props.name}: {total}"
                
                # Use resource color for the symbol
                with term.location(x, y + line):
                    # Symbol in resource color
                    print(term.color_rgb(*props.color) + props.symbol + term.normal, end=' ')
                    # Name and quantity in text color
                    print(term.color_rgb(*self.text_color.rgb) + 
                          f"{props.name}: {total}" + term.normal)
                
                line += 1
        else:
            # Empty inventory message
            empty_msg = "Your inventory is empty"
            with term.location(x + (width - len(empty_msg)) // 2, y + height // 2):
                print(term.color_rgb(*self.empty_color.rgb) + empty_msg + term.normal)