#!/usr/bin/env python3
"""Test dungeon connectivity."""

import sys
from src.magemines.game.map_generation.base import MapGeneratorConfig
from src.magemines.game.map_generation.dungeon import DungeonGenerator

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

def test_connectivity():
    """Test dungeon connectivity multiple times."""
    config = MapGeneratorConfig(
        width=80,
        height=24,
        min_room_size=5,
        max_room_size=10,
        max_rooms=10,
        corridor_width=1,
        diagonal_corridors=False
    )
    
    # Test multiple generations
    for i in range(5):
        print(f"\n--- Test {i+1} ---")
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Show room count
        print(f"Generated {len(generator.rooms)} rooms")
        
        # Check connectivity
        components = generator._find_connected_components()
        print(f"Connected components: {len(components)}")
        
        if len(components) > 1:
            print("WARNING: Dungeon has disconnected rooms!")
            for j, comp in enumerate(components):
                print(f"  Component {j}: {len(comp)} rooms")
        else:
            print("SUCCESS: All rooms are connected!")
        
        # Also check global connectivity
        if generator.rooms:
            reachable = generator._count_reachable_rooms_global()
            print(f"Global flood fill: {reachable}/{len(generator.rooms)} rooms reachable")
        
        # Visualize the map
        visualize_map(generator)

if __name__ == "__main__":
    test_connectivity()