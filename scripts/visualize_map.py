#!/usr/bin/env python
"""Script to visualize generated maps."""

import sys
sys.path.insert(0, 'src')

from magemines.game.map_generator import (
    MapGeneratorConfig, GenerationMethod, TileType,
    create_generator
)


def visualize_map(generator):
    """Print a text representation of the map."""
    # Map tiles to display characters
    tile_chars = {
        TileType.FLOOR: '.',
        TileType.WALL: '#',
        TileType.DOOR: '+',
        TileType.STAIRS_UP: '<',
        TileType.STAIRS_DOWN: '>',
        TileType.WATER: '~',
        TileType.LAVA: '=',
        TileType.CHEST: 'C',
        TileType.ALTAR: 'A',
        TileType.EMPTY: ' ',
    }
    
    for y in range(generator.height):
        for x in range(generator.width):
            tile = generator.get_tile(x, y)
            print(tile_chars.get(tile, '?'), end='')
        print()


def main():
    """Generate and display example maps."""
    # Smaller size for visualization
    
    print("=== DUNGEON (Rooms and Corridors) ===")
    config = MapGeneratorConfig(
        width=60,
        height=25,
        max_rooms=10,
        method=GenerationMethod.ROOMS_AND_CORRIDORS
    )
    generator = create_generator(config)
    generator.generate()
    visualize_map(generator)
    
    print("\n=== CAVE (Cellular Automata) ===")
    config = MapGeneratorConfig(
        width=60,
        height=25,
        method=GenerationMethod.CELLULAR_AUTOMATA
    )
    generator = create_generator(config)
    generator.generate()
    visualize_map(generator)
    
    print("\n=== TOWN ===")
    config = MapGeneratorConfig(
        width=60,
        height=25,
        max_rooms=6,  # Buildings
        method=GenerationMethod.TOWN
    )
    generator = create_generator(config)
    generator.generate()
    visualize_map(generator)


if __name__ == '__main__':
    main()