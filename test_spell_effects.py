#!/usr/bin/env python
"""Test script to verify spell effects are working."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from magemines.game.entity_system import Entity, EntityManager
from magemines.game.components import Position, Health, Name, Stats, MagicUser, AI
from magemines.game.systems.ai_system import AISystem
from magemines.game.map import GameMap
from magemines.ui.message_pane import MessagePane, MessageCategory
from magemines.core.terminal import BlessedTerminal, Position as TermPos

def test_spell_effects():
    """Test spell damage and healing effects."""
    print("Testing spell effects...")
    
    # Create a simple game map
    game_map = GameMap(20, 20, use_procedural=False)
    
    # Create entity manager
    entity_manager = game_map.entity_manager
    
    # Create AI system
    ai_system = AISystem(entity_manager, game_map)
    
    # Create a mock message pane
    class MockMessagePane:
        def add_message(self, text, category, turn=None, color=None):
            print(f"[{category.name}] {text}")
    
    ai_system.set_message_pane(MockMessagePane())
    
    # Create a caster (mage)
    caster = Entity(1)
    caster.add_component(Position(5, 5))
    caster.add_component(Name("Fire Mage"))
    caster.add_component(Health(50, 50))
    caster.add_component(Stats(intelligence=15))  # Higher int for more damage
    caster.add_component(MagicUser(
        current_mana=50,
        max_mana=50,
        known_spells=["fireball", "magic_missile"],
        magic_school="elemental"
    ))
    caster.add_component(AI(behavior_type="attack"))
    entity_manager.add_entity(caster)
    
    # Create a target (player)
    target = Entity(2)
    target.add_component(Position(5, 6))
    target.add_component(Name("Player"))
    target.add_component(Health(100, 100))
    entity_manager.add_entity(target)
    
    # Test damage spell
    print("\nTesting damage spell (fireball)...")
    print(f"Target health before: {target.get_component(Health).current}/{target.get_component(Health).maximum}")
    
    # Execute fireball spell
    ai_system._execute_spell(caster, "fireball", target)
    
    print(f"Target health after: {target.get_component(Health).current}/{target.get_component(Health).maximum}")
    
    # Create a healer
    healer = Entity(3)
    healer.add_component(Position(5, 7))
    healer.add_component(Name("Nature Priest"))
    healer.add_component(Health(40, 40))
    healer.add_component(Stats(intelligence=12, wisdom=15))
    healer.add_component(MagicUser(
        current_mana=50,
        max_mana=50,
        known_spells=["heal"],
        magic_school="nature"
    ))
    entity_manager.add_entity(healer)
    
    # Test healing spell
    print("\nTesting healing spell...")
    print(f"Target health before heal: {target.get_component(Health).current}/{target.get_component(Health).maximum}")
    
    # Execute heal spell
    ai_system._execute_spell(healer, "heal", target)
    
    print(f"Target health after heal: {target.get_component(Health).current}/{target.get_component(Health).maximum}")
    
    # Test death
    print("\nTesting death mechanics...")
    # Deal massive damage
    for i in range(10):
        ai_system._execute_spell(caster, "fireball", target)
    
    if target.get_component(Health).is_dead:
        print("Target has died successfully!")
    else:
        print(f"Target still alive with {target.get_component(Health).current} health")

if __name__ == "__main__":
    test_spell_effects()