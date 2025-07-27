"""UI Layout Manager for calculating component positions and sizes."""

from dataclasses import dataclass
from typing import Tuple
from ..core.terminal import Position


@dataclass
class LayoutDimensions:
    """Holds calculated layout dimensions for UI components."""
    # Header
    header_position: Position
    header_width: int
    header_height: int
    
    # Map
    map_position: Position
    map_width: int
    map_height: int
    
    # Message pane
    message_position: Position
    message_width: int
    message_height: int


class LayoutManager:
    """Manages UI component layout calculations."""
    
    def __init__(self, terminal_width: int, terminal_height: int, 
                 message_pane_width: int = 30,
                 max_map_width: int = 80,
                 max_map_height: int = 40):
        """Initialize layout manager with terminal dimensions.
        
        Args:
            terminal_width: Total terminal width
            terminal_height: Total terminal height
            message_pane_width: Desired width for message pane
            max_map_width: Maximum width for map area
            max_map_height: Maximum height for map area
        """
        self.terminal_width = terminal_width
        self.terminal_height = terminal_height
        self.message_pane_width = message_pane_width
        self.max_map_width = max_map_width
        self.max_map_height = max_map_height
        
    def calculate_layout(self) -> LayoutDimensions:
        """Calculate positions and sizes for all UI components.
        
        Returns:
            LayoutDimensions containing all calculated values
        """
        # Header is always at top
        header_height = 1
        header_position = Position(0, 0)
        header_width = self.terminal_width
        
        # Adjust message pane width if terminal is too small
        # Leave at least 20 columns for the map area
        min_map_area = 20
        max_message_width = max(20, self.terminal_width - min_map_area - 2)
        actual_message_width = min(self.message_pane_width, max_message_width)
        
        # Message pane on the right side
        message_pane_x = self.terminal_width - actual_message_width
        message_pane_y = header_height
        message_pane_height = self.terminal_height - header_height - 2
        message_position = Position(message_pane_x, message_pane_y)
        
        # Calculate available space for map
        available_map_width = message_pane_x - 2  # Leave 2 chars margin
        available_map_height = self.terminal_height - header_height - 2
        
        # Ensure we have positive dimensions
        available_map_width = max(1, available_map_width)
        available_map_height = max(1, available_map_height)
        
        # Determine actual map size
        map_width = min(self.max_map_width, available_map_width)
        map_height = min(self.max_map_height, available_map_height)
        
        # Ensure positive map dimensions
        map_width = max(1, map_width)
        map_height = max(1, map_height)
        
        # Center the map in available space
        map_x_offset = max(0, (available_map_width - map_width) // 2)
        map_y_offset = header_height + max(0, (available_map_height - map_height) // 2)
        map_position = Position(map_x_offset, map_y_offset)
        
        return LayoutDimensions(
            header_position=header_position,
            header_width=header_width,
            header_height=header_height,
            map_position=map_position,
            map_width=map_width,
            map_height=map_height,
            message_position=message_position,
            message_width=actual_message_width,
            message_height=message_pane_height
        )
    
    def update_terminal_size(self, width: int, height: int) -> None:
        """Update terminal dimensions.
        
        Args:
            width: New terminal width
            height: New terminal height
        """
        self.terminal_width = width
        self.terminal_height = height