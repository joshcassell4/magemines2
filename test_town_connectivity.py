#!/usr/bin/env python3
"""Test town connectivity."""

import sys
import logging
from src.magemines.game.map_generation.base import MapGeneratorConfig, TileType
from src.magemines.game.map_generation.town import TownGenerator
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
    print("\nGenerated Town:")
    print("=" * generator.width)
    
    # Create tile display mapping
    from src.magemines.game.map_generation.base import TileType
    tile_map = {
        TileType.FLOOR: '.',
        TileType.WALL: '#',
        TileType.DOOR: '+',
        TileType.STAIRS_UP: '<',
        TileType.STAIRS_DOWN: '>',
        TileType.WATER: '~',
        TileType.LAVA: '!',
        TileType.CHEST: 'C',
        TileType.ALTAR: '*',
        TileType.RESOURCE_WOOD: 't',
        TileType.RESOURCE_STONE: 'o',
        TileType.RESOURCE_ORE: '^',
        TileType.RESOURCE_CRYSTAL: '♦',
        TileType.RESOURCE_ESSENCE: '✦',
        TileType.RESOURCE_MUSHROOM: '♣',
        TileType.RESOURCE_HERBS: '♠',
    }
    
    for y in range(generator.height):
        line = ""
        for x in range(generator.width):
            tile = generator.get_tile(x, y)
            # Use the tile display mapping
            line += tile_map.get(tile, '?')
        print(line)
    print("=" * generator.width)

def test_town_connectivity():
    """Test town connectivity multiple times."""
    config = MapGeneratorConfig(
        width=80,
        height=40,
        min_room_size=5,
        max_room_size=10,
        max_rooms=15,
        road_width=2
    )
    
    # Test multiple generations
    failed_count = 0
    for i in range(5):
        print(f"\n--- Test {i+1} ---")
        generator = TownGenerator(config)
        generator.generate()
        
        # Show building count
        print(f"Generated {len(generator.buildings)} buildings")
        
        # Count doors
        door_count = 0
        for y in range(generator.height):
            for x in range(generator.width):
                if generator.get_tile(x, y) == TileType.DOOR:
                    door_count += 1
        print(f"Placed {door_count} doors")
        
        # Check connectivity using the same flood fill approach
        from collections import deque
        
        # Find all floor regions
        visited = set()
        regions = []
        
        for y in range(generator.height):
            for x in range(generator.width):
                if (x, y) not in visited:
                    tile = generator.get_tile(x, y)
                    # Check for walkable tiles
                    walkable_tiles = [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, 
                                      TileType.STAIRS_DOWN, TileType.ALTAR]
                    if tile in walkable_tiles:
                        # Start flood fill
                        region = []
                        queue = deque([(x, y)])
                        
                        while queue:
                            cx, cy = queue.popleft()
                            if (cx, cy) in visited or not generator.in_bounds(cx, cy):
                                continue
                            
                            ctile = generator.get_tile(cx, cy)
                            if ctile not in walkable_tiles:
                                continue
                            
                            visited.add((cx, cy))
                            region.append((cx, cy))
                            
                            # Add neighbors
                            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                                queue.append((cx + dx, cy + dy))
                        
                        if region:
                            regions.append(region)
        
        print(f"Found {len(regions)} disconnected regions")
        
        if len(regions) > 1:
            print("WARNING: Town has disconnected areas!")
            failed_count += 1
            for j, region in enumerate(regions):
                print(f"  Region {j}: {len(region)} tiles")
            # Show the failed map
            visualize_map(generator)
        else:
            print("SUCCESS: All areas are connected!")
            print(f"  Total accessible tiles: {len(regions[0]) if regions else 0}")
    
    print(f"\n=== Summary ===")
    print(f"Total tests: 5")
    print(f"Failed: {failed_count}")
    print(f"Success rate: {(5 - failed_count) / 5 * 100:.1f}%")

if __name__ == "__main__":
    test_town_connectivity()