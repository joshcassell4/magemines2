"""Resource types and properties for the game."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Dict, Any


class ResourceType(Enum):
    """Types of resources available in the game."""
    # Basic materials
    WOOD = auto()
    STONE = auto()
    ORE = auto()
    
    # Magic materials
    CRYSTAL = auto()
    ESSENCE = auto()
    
    # Consumables
    FOOD = auto()
    HERBS = auto()
    
    # Liquids
    WATER = auto()


@dataclass
class ResourceProperties:
    """Properties that define a resource type."""
    name: str
    symbol: str
    color: tuple[int, int, int]  # RGB color
    rarity: float  # 0.0 (common) to 1.0 (ultra rare)
    stack_size: int  # Max items per stack
    gather_time: int  # Turns needed to gather
    tool_required: Optional[str] = None  # Tool needed to gather
    min_yield: int = 1  # Minimum amount gathered
    max_yield: int = 1  # Maximum amount gathered
    description: str = ""


# Resource definitions with their properties
RESOURCE_PROPERTIES: Dict[ResourceType, ResourceProperties] = {
    ResourceType.WOOD: ResourceProperties(
        name="Wood",
        symbol="t",
        color=(139, 69, 19),  # Saddle brown
        rarity=0.1,  # Common
        stack_size=100,
        gather_time=2,
        tool_required=None,  # Can gather by hand
        min_yield=2,
        max_yield=5,
        description="Basic building material from trees"
    ),
    
    ResourceType.STONE: ResourceProperties(
        name="Stone",
        symbol="s",
        color=(128, 128, 128),  # Gray
        rarity=0.15,  # Common
        stack_size=100,
        gather_time=3,
        tool_required="pickaxe",
        min_yield=1,
        max_yield=3,
        description="Solid rock for construction"
    ),
    
    ResourceType.ORE: ResourceProperties(
        name="Iron Ore",
        symbol="o",
        color=(184, 134, 11),  # Dark goldenrod
        rarity=0.4,  # Uncommon
        stack_size=50,
        gather_time=5,
        tool_required="pickaxe",
        min_yield=1,
        max_yield=2,
        description="Raw metal ore for smelting"
    ),
    
    ResourceType.CRYSTAL: ResourceProperties(
        name="Magic Crystal",
        symbol="*",
        color=(147, 112, 219),  # Medium purple
        rarity=0.7,  # Rare
        stack_size=20,
        gather_time=8,
        tool_required="magic_pickaxe",
        min_yield=1,
        max_yield=1,
        description="Crystallized magical energy"
    ),
    
    ResourceType.ESSENCE: ResourceProperties(
        name="Arcane Essence",
        symbol="*",  # Same as crystal
        color=(255, 20, 147),  # Deep pink
        rarity=0.85,  # Very rare
        stack_size=10,
        gather_time=10,
        tool_required=None,  # Requires magic to extract
        min_yield=1,
        max_yield=1,
        description="Pure magical essence"
    ),
    
    ResourceType.FOOD: ResourceProperties(
        name="Mushroom",
        symbol="m",
        color=(255, 140, 0),  # Dark orange
        rarity=0.25,  # Common
        stack_size=50,
        gather_time=1,
        tool_required=None,
        min_yield=1,
        max_yield=3,
        description="Edible cave mushroom"
    ),
    
    ResourceType.HERBS: ResourceProperties(
        name="Healing Herbs",
        symbol="h",
        color=(50, 205, 50),  # Lime green
        rarity=0.35,  # Uncommon
        stack_size=30,
        gather_time=2,
        tool_required=None,
        min_yield=1,
        max_yield=2,
        description="Medicinal plants"
    ),
    
    ResourceType.WATER: ResourceProperties(
        name="Water",
        symbol="~",
        color=(64, 164, 223),  # Light blue
        rarity=0.3,  # Common in certain areas
        stack_size=100,
        gather_time=1,
        tool_required="bucket",
        min_yield=5,
        max_yield=10,
        description="Fresh water source"
    ),
}


@dataclass
class ResourceNode:
    """A resource node that can be gathered from."""
    resource_type: ResourceType
    x: int
    y: int
    quantity: int  # How many times it can be gathered
    depleted: bool = False
    
    @property
    def properties(self) -> ResourceProperties:
        """Get the properties for this resource type."""
        return RESOURCE_PROPERTIES[self.resource_type]
    
    def gather(self, skill_level: int = 1) -> int:
        """
        Attempt to gather from this node.
        
        Args:
            skill_level: The gatherer's skill level (affects yield)
            
        Returns:
            Amount of resources gathered
        """
        if self.depleted:
            return 0
            
        props = self.properties
        
        # Calculate yield based on skill level
        base_yield = props.min_yield
        if props.max_yield > props.min_yield:
            import random
            skill_bonus = min(skill_level / 10, 1.0)  # Cap at 100% bonus
            yield_range = props.max_yield - props.min_yield
            base_yield += int(yield_range * skill_bonus * random.random())
        
        # Deplete the node
        self.quantity -= 1
        if self.quantity <= 0:
            self.depleted = True
            
        return base_yield


@dataclass 
class ResourceStack:
    """A stack of resources in an inventory."""
    resource_type: ResourceType
    quantity: int
    
    @property
    def properties(self) -> ResourceProperties:
        """Get the properties for this resource type."""
        return RESOURCE_PROPERTIES[self.resource_type]
    
    @property
    def is_full(self) -> bool:
        """Check if the stack is at max capacity."""
        return self.quantity >= self.properties.stack_size
    
    def add(self, amount: int) -> int:
        """
        Add resources to the stack.
        
        Args:
            amount: Amount to add
            
        Returns:
            Amount that couldn't be added (overflow)
        """
        space = self.properties.stack_size - self.quantity
        to_add = min(amount, space)
        self.quantity += to_add
        return amount - to_add
    
    def remove(self, amount: int) -> int:
        """
        Remove resources from the stack.
        
        Args:
            amount: Amount to remove
            
        Returns:
            Amount actually removed
        """
        to_remove = min(amount, self.quantity)
        self.quantity -= to_remove
        return to_remove


def get_resources_by_rarity(min_rarity: float = 0.0, max_rarity: float = 1.0) -> list[ResourceType]:
    """Get all resource types within a rarity range."""
    resources = []
    for resource_type, props in RESOURCE_PROPERTIES.items():
        if min_rarity <= props.rarity <= max_rarity:
            resources.append(resource_type)
    return resources


def get_gatherable_resources(tools: Optional[set[str]] = None) -> list[ResourceType]:
    """Get all resources that can be gathered with the given tools."""
    if tools is None:
        tools = set()
        
    resources = []
    for resource_type, props in RESOURCE_PROPERTIES.items():
        if props.tool_required is None or props.tool_required in tools:
            resources.append(resource_type)
    return resources