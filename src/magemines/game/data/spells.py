"""Spell definitions for the game."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class SpellData:
    """Data structure for spell definitions."""
    spell_id: str
    name: str
    description: str
    mana_cost: int
    range: int
    area_of_effect: int = 0
    effect_type: str = "damage"
    effect_value: int = 10
    cast_time: int = 1
    cooldown: int = 0
    school: str = "arcane"
    symbol: str = "*"
    color: tuple[int, int, int] = (255, 255, 255)


# Spell definitions organized by school
SPELL_DATABASE: Dict[str, SpellData] = {
    # Arcane spells
    "magic_missile": SpellData(
        spell_id="magic_missile",
        name="Magic Missile",
        description="A bolt of pure magical energy that never misses",
        mana_cost=3,
        range=5,
        effect_type="damage",
        effect_value=5,
        cast_time=1,
        cooldown=0,
        school="arcane",
        symbol="*",
        color=(147, 112, 219)  # Medium purple
    ),
    
    "arcane_shield": SpellData(
        spell_id="arcane_shield",
        name="Arcane Shield",
        description="A protective barrier of magical energy",
        mana_cost=5,
        range=0,  # Self only
        effect_type="buff",
        effect_value=10,  # Shield strength
        cast_time=1,
        cooldown=10,
        school="arcane",
        symbol="O",
        color=(100, 149, 237)  # Cornflower blue
    ),
    
    "teleport": SpellData(
        spell_id="teleport",
        name="Teleport",
        description="Instantly transport to a visible location",
        mana_cost=8,
        range=10,
        effect_type="utility",
        effect_value=0,
        cast_time=2,
        cooldown=5,
        school="arcane",
        symbol="§",
        color=(255, 0, 255)  # Magenta
    ),
    
    # Elemental spells
    "fireball": SpellData(
        spell_id="fireball",
        name="Fireball",
        description="An explosive ball of fire",
        mana_cost=6,
        range=8,
        area_of_effect=2,  # Explosion radius
        effect_type="damage",
        effect_value=8,
        cast_time=2,
        cooldown=3,
        school="elemental",
        symbol="*",
        color=(255, 69, 0)  # Orange red
    ),
    
    "frost_bolt": SpellData(
        spell_id="frost_bolt",
        name="Frost Bolt",
        description="A shard of ice that slows enemies",
        mana_cost=4,
        range=6,
        effect_type="damage",
        effect_value=6,
        cast_time=1,
        cooldown=2,
        school="elemental",
        symbol="*",
        color=(173, 216, 230)  # Light blue
    ),
    
    "lightning_strike": SpellData(
        spell_id="lightning_strike",
        name="Lightning Strike",
        description="Call down a bolt of lightning",
        mana_cost=7,
        range=10,
        effect_type="damage",
        effect_value=12,
        cast_time=3,
        cooldown=5,
        school="elemental",
        symbol="!",
        color=(255, 255, 0)  # Yellow
    ),
    
    # Nature spells
    "heal": SpellData(
        spell_id="heal",
        name="Heal",
        description="Restore health with nature's energy",
        mana_cost=4,
        range=1,  # Touch range
        effect_type="heal",
        effect_value=8,
        cast_time=2,
        cooldown=0,
        school="nature",
        symbol="+",
        color=(0, 255, 0)  # Green
    ),
    
    "entangle": SpellData(
        spell_id="entangle",
        name="Entangle",
        description="Vines grasp and hold the target",
        mana_cost=5,
        range=4,
        effect_type="debuff",
        effect_value=3,  # Duration
        cast_time=1,
        cooldown=4,
        school="nature",
        symbol="#",
        color=(34, 139, 34)  # Forest green
    ),
    
    # Utility spells
    "light": SpellData(
        spell_id="light",
        name="Light",
        description="Create a magical light source",
        mana_cost=1,
        range=0,
        effect_type="utility",
        effect_value=10,  # Light radius
        cast_time=1,
        cooldown=0,
        school="arcane",
        symbol="☼",
        color=(255, 255, 224)  # Light yellow
    ),
    
    "detect_magic": SpellData(
        spell_id="detect_magic",
        name="Detect Magic",
        description="Reveal magical auras nearby",
        mana_cost=2,
        range=0,
        area_of_effect=5,  # Detection radius
        effect_type="utility",
        effect_value=0,
        cast_time=1,
        cooldown=0,
        school="arcane",
        symbol="?",
        color=(255, 20, 147)  # Deep pink
    ),
    
    "identify": SpellData(
        spell_id="identify",
        name="Identify",
        description="Learn the properties of an item",
        mana_cost=3,
        range=1,
        effect_type="utility",
        effect_value=0,
        cast_time=3,
        cooldown=0,
        school="arcane",
        symbol="i",
        color=(255, 215, 0)  # Gold
    ),
    
    # Dark magic (for evil mages)
    "drain_life": SpellData(
        spell_id="drain_life",
        name="Drain Life",
        description="Steal life force from the target",
        mana_cost=6,
        range=3,
        effect_type="damage",
        effect_value=6,  # Also heals caster for half
        cast_time=2,
        cooldown=5,
        school="dark",
        symbol="◊",
        color=(139, 0, 0)  # Dark red
    ),
    
    "curse": SpellData(
        spell_id="curse",
        name="Curse",
        description="Afflict the target with misfortune",
        mana_cost=5,
        range=5,
        effect_type="debuff",
        effect_value=5,  # Duration
        cast_time=2,
        cooldown=8,
        school="dark",
        symbol="X",
        color=(75, 0, 130)  # Indigo
    ),
}


def get_spell(spell_id: str) -> SpellData:
    """Get a spell by its ID."""
    return SPELL_DATABASE.get(spell_id)


def get_spells_by_school(school: str) -> list[SpellData]:
    """Get all spells of a specific school."""
    return [spell for spell in SPELL_DATABASE.values() if spell.school == school]


def get_starting_spells(school: str) -> list[str]:
    """Get the starting spells for a mage of a specific school."""
    starting_spells = {
        "arcane": ["magic_missile", "light"],
        "elemental": ["frost_bolt"],
        "nature": ["heal"],
        "dark": ["drain_life"],
    }
    return starting_spells.get(school, ["magic_missile"])