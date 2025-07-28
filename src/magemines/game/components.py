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
    
    @property
    def max_mana(self) -> int:
        """Maximum mana based on intelligence and wisdom."""
        return 10 + (self.intelligence - 10) * 2 + (self.wisdom - 10)
    
    @property
    def spell_power(self) -> float:
        """Spell damage/healing multiplier based on intelligence."""
        return 1.0 + (self.intelligence - 10) * 0.1
    
    @property
    def mana_regen_rate(self) -> float:
        """Mana regeneration per turn based on wisdom."""
        return 1.0 + (self.wisdom - 10) * 0.05


@dataclass
class MagicUser(Component):
    """Component for entities that can use magic."""
    current_mana: int = 10
    max_mana: int = 10
    known_spells: List[str] = field(default_factory=list)  # Spell IDs
    magic_school: str = "arcane"  # arcane, elemental, divine, nature
    spell_cooldowns: Dict[str, int] = field(default_factory=dict)  # spell_id -> turns remaining
    casting_spell: Optional[str] = None  # Currently casting spell ID
    cast_progress: int = 0  # Turns spent casting current spell
    
    def can_cast(self, spell_id: str, mana_cost: int) -> bool:
        """Check if the entity can cast a spell."""
        return (self.current_mana >= mana_cost and 
                spell_id in self.known_spells and
                self.spell_cooldowns.get(spell_id, 0) <= 0 and
                self.casting_spell is None)
    
    def start_casting(self, spell_id: str):
        """Start casting a spell."""
        self.casting_spell = spell_id
        self.cast_progress = 0
    
    def finish_casting(self, spell_id: str, cooldown: int):
        """Finish casting a spell and apply cooldown."""
        self.casting_spell = None
        self.cast_progress = 0
        if cooldown > 0:
            self.spell_cooldowns[spell_id] = cooldown
    
    def spend_mana(self, amount: int):
        """Spend mana, returns True if successful."""
        if self.current_mana >= amount:
            self.current_mana -= amount
            return True
        return False
    
    def regenerate_mana(self, amount: float):
        """Regenerate mana up to maximum."""
        self.current_mana = min(self.max_mana, int(self.current_mana + amount))
    
    def update_cooldowns(self):
        """Reduce all cooldowns by 1 turn."""
        for spell_id in list(self.spell_cooldowns.keys()):
            self.spell_cooldowns[spell_id] -= 1
            if self.spell_cooldowns[spell_id] <= 0:
                del self.spell_cooldowns[spell_id]


@dataclass
class Spell(Component):
    """Spell definition component (attached to spell entities)."""
    spell_id: str
    name: str
    description: str
    mana_cost: int
    range: int  # 0 = self, 1 = melee, 2+ = ranged
    area_of_effect: int = 0  # 0 = single target, 1+ = radius
    effect_type: str = "damage"  # damage, heal, buff, debuff, summon, utility
    effect_value: int = 10  # Base damage/healing/duration
    cast_time: int = 1  # Turns to cast (1 = instant)
    cooldown: int = 0  # Turns before can cast again
    school: str = "arcane"  # Magic school requirement
    
    @property
    def is_instant(self) -> bool:
        """Check if spell casts instantly."""
        return self.cast_time <= 1
    
    @property
    def is_self_cast(self) -> bool:
        """Check if spell can only target self."""
        return self.range == 0
    
    @property
    def is_area_effect(self) -> bool:
        """Check if spell affects an area."""
        return self.area_of_effect > 0


@dataclass
class MagicEffect(Component):
    """Active magical effect on an entity."""
    effect_id: str
    name: str
    effect_type: str  # buff, debuff, dot, hot, shield
    remaining_duration: int  # Turns remaining
    strength: int  # Effect strength/power
    source_entity_id: Optional[int] = None  # Who cast this effect
    
    def tick(self) -> bool:
        """
        Process one turn of the effect.
        Returns True if effect should continue, False if expired.
        """
        self.remaining_duration -= 1
        return self.remaining_duration > 0
    
    @property
    def is_beneficial(self) -> bool:
        """Check if this is a beneficial effect."""
        return self.effect_type in ["buff", "hot", "shield"]
    
    @property
    def is_harmful(self) -> bool:
        """Check if this is a harmful effect."""
        return self.effect_type in ["debuff", "dot"]


@dataclass 
class Faction(Component):
    """Faction alignment and reputation component."""
    faction_id: str  # ancient_order, rogue_mages, neutral_scholars, mad_hermits
    reputation: Dict[str, int] = field(default_factory=dict)  # entity_id -> reputation value
    base_hostility: int = 0  # -100 (peaceful) to 100 (hostile)
    
    def get_reputation(self, entity_id: int) -> int:
        """Get reputation with a specific entity."""
        return self.reputation.get(str(entity_id), 0)
    
    def modify_reputation(self, entity_id: int, amount: int):
        """Modify reputation with a specific entity."""
        entity_key = str(entity_id)
        current = self.reputation.get(entity_key, 0)
        self.reputation[entity_key] = max(-100, min(100, current + amount))
    
    def is_hostile_to(self, entity_id: int) -> bool:
        """Check if hostile to a specific entity."""
        rep = self.get_reputation(entity_id)
        return self.base_hostility + rep > 25
    
    def is_friendly_to(self, entity_id: int) -> bool:
        """Check if friendly to a specific entity."""
        rep = self.get_reputation(entity_id)
        return self.base_hostility + rep < -25