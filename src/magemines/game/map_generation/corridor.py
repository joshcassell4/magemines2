"""Corridor class and corridor building strategies."""

from dataclasses import dataclass
from typing import List, Tuple, Protocol
from abc import abstractmethod


@dataclass
class Corridor:
    """Represents a corridor between two points."""
    x1: int
    y1: int
    x2: int
    y2: int
    
    def get_points(self) -> List[Tuple[int, int]]:
        """Get all points in the corridor."""
        points = []
        
        # Create an L-shaped corridor
        # We go from (x1,y1) to (x2,y1) then from (x2,y1) to (x2,y2)
        
        # Horizontal segment
        if self.x1 < self.x2:
            for x in range(self.x1, self.x2 + 1):
                points.append((x, self.y1))
        else:
            for x in range(self.x2, self.x1 + 1):
                points.append((x, self.y1))
        
        # Vertical segment (excluding the corner point which is already added)
        if self.y1 < self.y2:
            for y in range(self.y1 + 1, self.y2 + 1):
                points.append((self.x2, y))
        elif self.y1 > self.y2:
            for y in range(self.y2, self.y1):
                points.append((self.x2, y))
        # If y1 == y2, no vertical segment needed
        
        return points


class CorridorBuilder(Protocol):
    """Protocol for corridor building strategies."""
    
    @abstractmethod
    def build_corridor(self, x1: int, y1: int, x2: int, y2: int) -> List[Tuple[int, int]]:
        """Build a corridor between two points.
        
        Args:
            x1, y1: Starting position
            x2, y2: Ending position
            
        Returns:
            List of (x, y) tuples representing the corridor path
        """
        pass