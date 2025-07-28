"""Mage entity factories."""

from typing import Optional, List
from ..entities import Entity
from ..components import (
    Position, Renderable, Name, Stats, Health, AI, 
    MagicUser, Faction, Inventory
)
from ..data.spells import get_starting_spells


def create_apprentice_mage(entity_id: int, x: int, y: int, 
                          name: Optional[str] = None) -> Entity:
    """Create an apprentice mage - friendly, weak, good for trading."""
    mage = Entity(entity_id)
    
    # Basic components
    mage.add_component(Position(x, y))
    mage.add_component(Renderable('a', (0, 255, 255)))  # Cyan 'a'
    mage.add_component(Name(name or "Apprentice Mage", "Novice"))
    
    # Stats - weak but intelligent
    mage.add_component(Stats(
        strength=6,
        intelligence=12,
        dexterity=8,
        wisdom=11
    ))
    
    # Health - fragile
    mage.add_component(Health(current=15, maximum=15))
    
    # Magic abilities
    stats = mage.get_component(Stats)
    magic = MagicUser(
        current_mana=stats.max_mana,
        max_mana=stats.max_mana,
        known_spells=get_starting_spells("arcane"),
        magic_school="arcane"
    )
    mage.add_component(magic)
    
    # AI - passive, will trade
    mage.add_component(AI(behavior_type="idle"))
    
    # Faction - neutral scholars
    faction = Faction(
        faction_id="neutral_scholars",
        base_hostility=-50  # Friendly by default
    )
    mage.add_component(faction)
    
    # Small inventory for trading
    mage.add_component(Inventory(capacity=10))
    
    return mage


def create_elemental_mage(entity_id: int, x: int, y: int,
                         element: str = "fire",
                         name: Optional[str] = None) -> Entity:
    """Create an elemental mage - moderate power, territorial."""
    mage = Entity(entity_id)
    
    # Element-specific attributes
    element_data = {
        "fire": {
            "color": (255, 0, 0),  # Red
            "spells": ["fireball", "magic_missile"],
            "name_prefix": "Pyromancer"
        },
        "ice": {
            "color": (173, 216, 230),  # Light blue
            "spells": ["frost_bolt", "arcane_shield"],
            "name_prefix": "Cryomancer"
        },
        "lightning": {
            "color": (255, 255, 0),  # Yellow
            "spells": ["lightning_strike", "teleport"],
            "name_prefix": "Electromancer"
        }
    }
    
    elem_info = element_data.get(element, element_data["fire"])
    
    # Basic components
    mage.add_component(Position(x, y))
    mage.add_component(Renderable('M', elem_info["color"]))
    mage.add_component(Name(name or f"{elem_info['name_prefix']} {element.title()}"))
    
    # Stats - balanced with focus on intelligence
    mage.add_component(Stats(
        strength=10,
        intelligence=15,
        dexterity=12,
        wisdom=13
    ))
    
    # Health - moderate
    mage.add_component(Health(current=30, maximum=30))
    
    # Magic abilities
    stats = mage.get_component(Stats)
    magic = MagicUser(
        current_mana=stats.max_mana,
        max_mana=stats.max_mana,
        known_spells=elem_info["spells"],
        magic_school="elemental"
    )
    mage.add_component(magic)
    
    # AI - territorial, will attack intruders
    mage.add_component(AI(behavior_type="patrol"))
    
    # Faction - rogue mages
    faction = Faction(
        faction_id="rogue_mages",
        base_hostility=25  # Slightly hostile
    )
    mage.add_component(faction)
    
    # Inventory for loot
    mage.add_component(Inventory(capacity=15))
    
    return mage


def create_ancient_scholar(entity_id: int, x: int, y: int,
                          name: Optional[str] = None) -> Entity:
    """Create an ancient scholar - high wisdom, utility spells, lore keeper."""
    mage = Entity(entity_id)
    
    # Basic components
    mage.add_component(Position(x, y))
    mage.add_component(Renderable('S', (138, 43, 226)))  # Blue violet
    mage.add_component(Name(name or "Ancient Scholar", "Keeper"))
    
    # Stats - very intelligent and wise
    mage.add_component(Stats(
        strength=8,
        intelligence=18,
        dexterity=9,
        wisdom=20
    ))
    
    # Health - moderate but protected by magic
    mage.add_component(Health(current=25, maximum=25))
    
    # Magic abilities - lots of utility spells
    stats = mage.get_component(Stats)
    magic = MagicUser(
        current_mana=stats.max_mana,
        max_mana=stats.max_mana,
        known_spells=["detect_magic", "identify", "light", "arcane_shield", 
                      "teleport", "heal"],
        magic_school="arcane"
    )
    mage.add_component(magic)
    
    # AI - study behavior, will share knowledge
    ai = AI(behavior_type="study")
    ai.memory["knowledge_topics"] = ["spells", "history", "artifacts", "prophecies"]
    mage.add_component(ai)
    
    # Faction - ancient order
    faction = Faction(
        faction_id="ancient_order",
        base_hostility=-75  # Very peaceful
    )
    mage.add_component(faction)
    
    # Large inventory for books and artifacts
    mage.add_component(Inventory(capacity=25))
    
    return mage


def create_mad_hermit(entity_id: int, x: int, y: int,
                     name: Optional[str] = None) -> Entity:
    """Create a mad hermit - unpredictable, wild magic, chaotic."""
    mage = Entity(entity_id)
    
    # Basic components  
    mage.add_component(Position(x, y))
    # Flickering color effect would be handled by renderer
    mage.add_component(Renderable('h', (147, 112, 219)))  # Medium purple
    mage.add_component(Name(name or "Mad Hermit", "the Unhinged"))
    
    # Stats - random but tend toward extremes
    import random
    mage.add_component(Stats(
        strength=random.randint(5, 15),
        intelligence=random.randint(10, 20),
        dexterity=random.randint(5, 15),
        wisdom=random.randint(5, 20)
    ))
    
    # Health - varies
    health_max = random.randint(20, 40)
    mage.add_component(Health(current=health_max, maximum=health_max))
    
    # Magic abilities - random assortment of spells
    stats = mage.get_component(Stats)
    all_spells = ["magic_missile", "fireball", "frost_bolt", "lightning_strike",
                  "heal", "entangle", "teleport", "drain_life", "curse"]
    known_spells = random.sample(all_spells, random.randint(3, 6))
    
    magic = MagicUser(
        current_mana=stats.max_mana,
        max_mana=stats.max_mana,
        known_spells=known_spells,
        magic_school="chaos"  # Special school for wild magic
    )
    mage.add_component(magic)
    
    # AI - erratic behavior
    ai = AI(behavior_type="erratic")
    ai.memory["mood"] = random.choice(["aggressive", "fearful", "curious", "helpful"])
    mage.add_component(ai)
    
    # Faction - mad hermits (unpredictable reputation)
    faction = Faction(
        faction_id="mad_hermits",
        base_hostility=random.randint(-50, 50)  # Could be friendly or hostile
    )
    mage.add_component(faction)
    
    # Inventory with random items
    mage.add_component(Inventory(capacity=20))
    
    return mage


def create_archmage(entity_id: int, x: int, y: int,
                   name: Optional[str] = None) -> Entity:
    """Create an archmage - boss-level mage with multiple schools."""
    mage = Entity(entity_id)
    
    # Basic components
    mage.add_component(Position(x, y))
    mage.add_component(Renderable('A', (255, 0, 255)))  # Bright magenta
    mage.add_component(Name(name or "Archmage", "the Magnificent"))
    
    # Stats - exceptional
    mage.add_component(Stats(
        strength=14,
        intelligence=22,
        dexterity=16,
        wisdom=20
    ))
    
    # Health - high with magical protection
    mage.add_component(Health(current=80, maximum=80))
    
    # Magic abilities - master of multiple schools
    stats = mage.get_component(Stats)
    magic = MagicUser(
        current_mana=stats.max_mana * 2,  # Extra mana pool
        max_mana=stats.max_mana * 2,
        known_spells=["magic_missile", "fireball", "frost_bolt", "lightning_strike",
                      "arcane_shield", "teleport", "heal", "entangle", 
                      "drain_life", "curse"],
        magic_school="master"  # Master of all schools
    )
    mage.add_component(magic)
    
    # AI - intelligent combat behavior
    ai = AI(behavior_type="boss")
    ai.memory["phase"] = 1  # Combat phases
    ai.memory["teleport_cooldown"] = 0
    mage.add_component(ai)
    
    # Faction - ancient order but corrupted
    faction = Faction(
        faction_id="ancient_order",
        base_hostility=75  # Hostile to intruders
    )
    mage.add_component(faction)
    
    # Large inventory with powerful items
    mage.add_component(Inventory(capacity=30))
    
    return mage


# Factory function for easy mage creation
def create_mage(mage_type: str, entity_id: int, x: int, y: int, **kwargs) -> Optional[Entity]:
    """Create a mage of the specified type."""
    mage_factories = {
        "apprentice": create_apprentice_mage,
        "elemental": create_elemental_mage,
        "scholar": create_ancient_scholar,
        "hermit": create_mad_hermit,
        "archmage": create_archmage,
    }
    
    factory = mage_factories.get(mage_type)
    if factory:
        return factory(entity_id, x, y, **kwargs)
    return None