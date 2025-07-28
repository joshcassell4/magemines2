"""Game data definitions."""

from .spells import SPELL_DATABASE, SpellData, get_spell, get_spells_by_school, get_starting_spells

__all__ = [
    'SPELL_DATABASE',
    'SpellData', 
    'get_spell',
    'get_spells_by_school',
    'get_starting_spells'
]