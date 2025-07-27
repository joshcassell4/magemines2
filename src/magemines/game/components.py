"""Entity Component System components for the game."""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List
from .resources import ResourceType, ResourceStack


@dataclass
class Component:
    """Base class for all ECS components."""
    pass


@dataclass
class Position(Component):
    """Position component for entities."""
    x: int
    y: int
    
    def move(self, dx: int, dy: int):
        """Move the position by the given deltas."""
        self.x += dx
        self.y += dy


@dataclass
class Renderable(Component):
    """Rendering information for entities."""
    char: str
    color: tuple[int, int, int] = (255, 255, 255)  # Default white
    priority: int = 0  # Higher priority renders on top


@dataclass
class Inventory(Component):
    """Inventory component for storing resources and items."""
    capacity: int = 20  # Number of stacks
    stacks: List[ResourceStack] = field(default_factory=list)
    
    def add_resource(self, resource_type: ResourceType, amount: int) -> int:
        """
        Add resources to the inventory.
        
        Args:
            resource_type: Type of resource to add
            amount: Amount to add
            
        Returns:
            Amount that couldn't be added (overflow)
        """
        remaining = amount
        
        # First, try to add to existing stacks
        for stack in self.stacks:
            if stack.resource_type == resource_type and not stack.is_full:
                remaining = stack.add(remaining)
                if remaining == 0:
                    return 0
        
        # Create new stacks if needed
        while remaining > 0 and len(self.stacks) < self.capacity:
            new_stack = ResourceStack(resource_type, 0)
            self.stacks.append(new_stack)
            remaining = new_stack.add(remaining)
        
        return remaining
    
    def remove_resource(self, resource_type: ResourceType, amount: int) -> int:
        """
        Remove resources from the inventory.
        
        Args:
            resource_type: Type of resource to remove
            amount: Amount to remove
            
        Returns:
            Amount actually removed
        """
        removed = 0
        stacks_to_remove = []
        
        for i, stack in enumerate(self.stacks):
            if stack.resource_type == resource_type:
                stack_removed = stack.remove(amount - removed)
                removed += stack_removed
                
                if stack.quantity == 0:
                    stacks_to_remove.append(i)
                
                if removed >= amount:
                    break
        
        # Remove empty stacks
        for i in reversed(stacks_to_remove):
            self.stacks.pop(i)
        
        return removed
    
    def get_resource_count(self, resource_type: ResourceType) -> int:
        """Get the total count of a resource type."""
        total = 0
        for stack in self.stacks:
            if stack.resource_type == resource_type:
                total += stack.quantity
        return total
    
    @property
    def is_full(self) -> bool:
        """Check if the inventory is full."""
        return len(self.stacks) >= self.capacity
    
    @property
    def is_empty(self) -> bool:
        """Check if the inventory is empty."""
        return len(self.stacks) == 0


@dataclass
class Gatherer(Component):
    """Component for entities that can gather resources."""
    skill_level: int = 1
    gathering: bool = False
    gather_target: Optional[tuple[int, int]] = None  # Position of resource being gathered
    gather_progress: int = 0  # Turns spent gathering current resource
    tools: set[str] = field(default_factory=set)  # Available tools
    
    def can_gather(self, tool_required: Optional[str]) -> bool:
        """Check if the entity can gather a resource requiring a specific tool."""
        return tool_required is None or tool_required in self.tools
    
    def start_gathering(self, x: int, y: int):
        """Start gathering a resource at the given position."""
        self.gathering = True
        self.gather_target = (x, y)
        self.gather_progress = 0
    
    def stop_gathering(self):
        """Stop gathering the current resource."""
        self.gathering = False
        self.gather_target = None
        self.gather_progress = 0


@dataclass
class Health(Component):
    """Health component for entities."""
    current: int
    maximum: int
    
    def damage(self, amount: int):
        """Apply damage to the entity."""
        self.current = max(0, self.current - amount)
    
    def heal(self, amount: int):
        """Heal the entity."""
        self.current = min(self.maximum, self.current + amount)
    
    @property
    def is_dead(self) -> bool:
        """Check if the entity is dead."""
        return self.current <= 0
    
    @property
    def percentage(self) -> float:
        """Get health as a percentage."""
        return self.current / self.maximum if self.maximum > 0 else 0.0


@dataclass
class AI(Component):
    """AI behavior component for entities."""
    behavior_type: str = "idle"  # idle, gather, flee, attack, etc.
    target: Optional[Any] = None
    memory: Dict[str, Any] = field(default_factory=dict)
    
    def set_behavior(self, behavior_type: str, target: Optional[Any] = None):
        """Set the current behavior and target."""
        self.behavior_type = behavior_type
        self.target = target
    
    def remember(self, key: str, value: Any):
        """Store something in memory."""
        self.memory[key] = value
    
    def recall(self, key: str) -> Optional[Any]:
        """Retrieve something from memory."""
        return self.memory.get(key)


@dataclass
class Name(Component):
    """Name component for entities."""
    name: str
    title: Optional[str] = None
    
    @property
    def full_name(self) -> str:
        """Get the full name including title."""
        if self.title:
            return f"{self.title} {self.name}"
        return self.name


@dataclass
class Stats(Component):
    """Basic stats for entities."""
    strength: int = 10
    intelligence: int = 10
    dexterity: int = 10
    wisdom: int = 10
    
    # Derived stats
    @property
    def gathering_speed(self) -> float:
        """How fast the entity can gather resources."""
        return 1.0 + (self.dexterity - 10) * 0.05
    
    @property
    def carrying_capacity(self) -> int:
        """Extra inventory slots based on strength."""
        return max(0, (self.strength - 10) // 2)