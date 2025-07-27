"""Room class for map generation."""

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Room:
    """Represents a rectangular room."""
    x: int
    y: int
    width: int
    height: int
    
    def center(self) -> Tuple[int, int]:
        """Get the center point of the room."""
        cx = self.x + self.width // 2
        cy = self.y + self.height // 2
        return cx, cy
    
    def intersects(self, other: 'Room') -> bool:
        """Check if this room intersects with another."""
        return (self.x < other.x + other.width and
                self.x + self.width > other.x and
                self.y < other.y + other.height and
                self.y + self.height > other.y)
    
    def contains(self, x: int, y: int) -> bool:
        """Check if a point is inside the room."""
        return (x >= self.x and x < self.x + self.width and
                y >= self.y and y < self.y + self.height)