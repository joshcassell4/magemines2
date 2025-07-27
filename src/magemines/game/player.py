"""Player entity for the game."""

from .entities import Entity
from .components import Position, Renderable, Inventory, Gatherer, Name, Stats


class Player(Entity):
    """Player entity with ECS components."""
    
    def __init__(self, entity_id: int, x: int, y: int):
        """Initialize the player.
        
        Args:
            entity_id: Unique entity ID
            x: Starting X position
            y: Starting Y position
        """
        super().__init__(entity_id)
        
        # Add components
        self.add_component(Position(x, y))
        self.add_component(Renderable('@', (0, 255, 0)))  # Green @
        self.add_component(Inventory(capacity=20))
        self.add_component(Gatherer(skill_level=1))
        self.add_component(Name("Player"))
        self.add_component(Stats())
        
    # Convenience properties for backwards compatibility
    @property
    def x(self) -> int:
        """Get X position."""
        pos = self.position
        return pos.x if pos else 0
        
    @x.setter
    def x(self, value: int):
        """Set X position."""
        pos = self.position
        if pos:
            pos.x = value
            
    @property
    def y(self) -> int:
        """Get Y position."""
        pos = self.position
        return pos.y if pos else 0
        
    @y.setter
    def y(self, value: int):
        """Set Y position."""
        pos = self.position
        if pos:
            pos.y = value
    
    def move(self, dx: int, dy: int):
        """Move the player by the given deltas.
        
        Args:
            dx: X delta
            dy: Y delta
        """
        pos = self.position
        if pos:
            pos.move(dx, dy)
