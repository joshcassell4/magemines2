#!/usr/bin/env python3
"""Test dungeon connectivity with doors."""

import sys
import logging
from src.magemines.game.map_generation.base import MapGeneratorConfig
from src.magemines.game.map_generation.dungeon import DungeonGenerator
from src.magemines.core.logging_config import LoggingConfig

# Setup logging to see debug messages
LoggingConfig.setup_logging(
    log_level="DEBUG",
    log_to_console=True,
    log_to_file=True,
    detailed_format=True
)

def visualize_map(generator):
    """Visualize the map in ASCII."""
    print("\nGenerated Dungeon:")
    print("=" * generator.width)
    
    for y in range(generator.height):
        line = ""
        for x in range(generator.width):
            tile = generator.get_tile(x, y)
            # Use the tile's string representation
            line += str(tile.value)
        print(line)
    print("=" * generator.width)

def test_door_connectivity():
    """Test dungeon connectivity with doors."""
    config = MapGeneratorConfig(
        width=60,
        height=20,
        min_room_size=5,
        max_room_size=8,
        max_rooms=8,
        corridor_width=1,
        diagonal_corridors=False
    )
    
    # Test multiple generations
    failed_count = 0
    for i in range(10):
        print(f"\n--- Test {i+1} ---")
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Show room count
        print(f"Generated {len(generator.rooms)} rooms")
        
        # Count doors
        door_count = 0
        for y in range(generator.height):
            for x in range(generator.width):
                if generator.get_tile(x, y).value == "+":
                    door_count += 1
        print(f"Placed {door_count} doors")
        
        # Check connectivity
        components = generator._find_connected_components()
        print(f"Connected components: {len(components)}")
        
        if len(components) > 1:
            print("WARNING: Dungeon has disconnected rooms!")
            failed_count += 1
            for j, comp in enumerate(components):
                print(f"  Component {j}: {len(comp)} rooms")
            # Show the failed map
            visualize_map(generator)
        else:
            print("SUCCESS: All rooms are connected!")
        
        # Also check global connectivity
        if generator.rooms:
            reachable = generator._count_reachable_rooms_global()
            print(f"Global flood fill: {reachable}/{len(generator.rooms)} rooms reachable")
            
            if reachable != len(generator.rooms):
                print("WARNING: Global flood fill found unreachable rooms!")
                if len(components) == 1:
                    print("  This suggests an issue with the flood fill algorithm")
                visualize_map(generator)
    
    print(f"\n=== Summary ===")
    print(f"Total tests: 10")
    print(f"Failed: {failed_count}")
    print(f"Success rate: {(10 - failed_count) / 10 * 100:.1f}%")

if __name__ == "__main__":
    test_door_connectivity()