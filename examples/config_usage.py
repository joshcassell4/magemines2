#!/usr/bin/env python3
"""Example of using the MageMines configuration system."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from magemines.core.config import get_config, get_config_manager, ConfigSection


def demonstrate_basic_usage():
    """Show basic configuration usage."""
    print("=== Basic Configuration Usage ===\n")
    
    # Get game configuration
    game_config = get_config(ConfigSection.GAME)
    print(f"Game Difficulty: {game_config.difficulty}")
    print(f"Turn Duration: {game_config.turn_duration_ms}ms")
    print(f"Autosave Enabled: {game_config.autosave_enabled}")
    print(f"Autosave Interval: {game_config.autosave_interval} turns\n")
    
    # Get UI configuration
    ui_config = get_config(ConfigSection.UI)
    print(f"Message Pane Width: {ui_config.message_pane_width}")
    print(f"Message History Size: {ui_config.message_history_size}")
    print(f"Wall Color (RGB): {ui_config.color_scheme['wall']}")
    print(f"Player Color (RGB): {ui_config.color_scheme['player']}\n")
    
    # Get map generation configuration
    map_config = get_config(ConfigSection.MAP_GENERATION)
    print(f"Room Size Range: {map_config.min_room_size}-{map_config.max_room_size}")
    print(f"Max Rooms (base): {map_config.max_rooms_base}")
    print(f"Corridor Style: {map_config.corridor_style}")
    print(f"Door Chance: {map_config.door_chance * 100}%\n")


def demonstrate_advanced_usage():
    """Show advanced configuration features."""
    print("=== Advanced Configuration Usage ===\n")
    
    # Get the configuration manager
    config_manager = get_config_manager()
    
    # Show config directory
    print(f"Configuration Directory: {config_manager.config_dir}\n")
    
    # List all configuration files
    print("Configuration Files:")
    for config_file in sorted(config_manager.config_dir.glob("*.json")):
        print(f"  - {config_file.name}")
    print()
    
    # Demonstrate modifying configuration
    print("Modifying configuration in memory...")
    debug_config = get_config(ConfigSection.DEBUG)
    original_debug = debug_config.debug_mode
    debug_config.debug_mode = True
    print(f"Debug mode changed from {original_debug} to {debug_config.debug_mode}")
    
    # Note: Changes are only in memory unless saved
    print("\nNote: Changes are only in memory. Use config_manager.save_all() to persist.")


def demonstrate_override_system():
    """Show how overrides work."""
    print("\n=== Configuration Override System ===\n")
    
    override_file = get_config_manager().config_dir / "overrides.json"
    
    if override_file.exists():
        print(f"Override file found: {override_file}")
        print("Overrides will be applied on top of base configuration.")
    else:
        print("No override file found.")
        print(f"Copy 'overrides.example.json' to 'overrides.json' to use overrides.")
        print(f"Location: {get_config_manager().config_dir}")


def demonstrate_dynamic_difficulty():
    """Example of using configuration for dynamic difficulty."""
    print("\n=== Dynamic Difficulty Example ===\n")
    
    game_config = get_config(ConfigSection.GAME)
    map_config = get_config(ConfigSection.MAP_GENERATION)
    entity_config = get_config(ConfigSection.ENTITIES)
    
    difficulties = {
        "easy": {
            "rooms": 15,
            "monsters": 0.02,
            "mage_health": 150
        },
        "normal": {
            "rooms": 20,
            "monsters": 0.05,
            "mage_health": 100
        },
        "hard": {
            "rooms": 25,
            "monsters": 0.08,
            "mage_health": 75
        }
    }
    
    current_difficulty = game_config.difficulty
    if current_difficulty in difficulties:
        settings = difficulties[current_difficulty]
        print(f"Current Difficulty: {current_difficulty}")
        print(f"  Base Rooms: {settings['rooms']}")
        print(f"  Monster Spawn Chance: {settings['monsters'] * 100}%")
        print(f"  Mage Base Health: {settings['mage_health']}")
    
    print("\nIn a real game, these values would affect map generation and gameplay.")


def main():
    """Run all demonstrations."""
    demonstrate_basic_usage()
    demonstrate_advanced_usage()
    demonstrate_override_system()
    demonstrate_dynamic_difficulty()
    
    print("\n" + "="*50)
    print("Configuration system demonstration complete!")
    print("See docs/CONFIGURATION.md for full documentation.")


if __name__ == "__main__":
    main()