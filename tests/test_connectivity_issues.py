"""Test to diagnose connectivity and door placement issues."""

import sys
sys.path.insert(0, 'src')

from magemines.game.map_generator import (
    MapGeneratorConfig, DungeonGenerator, CaveGenerator, 
    GenerationMethod, TileType
)

def test_dungeon_connectivity():
    """Test dungeon room connectivity."""
    print("Testing Dungeon Room Connectivity")
    print("=" * 80)
    
    config = MapGeneratorConfig(
        width=80,
        height=50,
        min_room_size=4,
        max_room_size=10,
        max_rooms=15,
        method=GenerationMethod.ROOMS_AND_CORRIDORS,
        corridor_width=2  # Make corridors wider for better connectivity
    )
    
    generator = DungeonGenerator(config)
    generator.generate()
    
    # Visualize the map
    print(f"Generated {len(generator.rooms)} rooms")
    print(f"Generated {len(generator.corridors)} corridors")
    
    # Check connectivity
    if hasattr(generator, '_rooms_with_doors'):
        print(f"Rooms marked for doors: {len(generator._rooms_with_doors)}")
    
    # Simple visualization
    for y in range(config.height):
        line = ""
        for x in range(config.width):
            tile = generator.get_tile(x, y)
            if tile == TileType.FLOOR:
                line += "."
            elif tile == TileType.WALL:
                line += "#"
            elif tile == TileType.DOOR:
                line += "+"
            elif tile == TileType.STAIRS_UP:
                line += "<"
            elif tile == TileType.STAIRS_DOWN:
                line += ">"
            else:
                line += "?"
        print(line)
    
    print("\nChecking room connectivity...")
    # Check if all rooms have at least one floor tile adjacent to a corridor
    disconnected_rooms = []
    for i, room in enumerate(generator.rooms):
        connected = False
        # Check room perimeter
        for x in range(room.x, room.x + room.width):
            for y in [room.y - 1, room.y + room.height]:
                if generator.in_bounds(x, y) and generator.get_tile(x, y) == TileType.FLOOR:
                    connected = True
                    break
        
        for y in range(room.y, room.y + room.height):
            for x in [room.x - 1, room.x + room.width]:
                if generator.in_bounds(x, y) and generator.get_tile(x, y) == TileType.FLOOR:
                    connected = True
                    break
        
        if not connected:
            disconnected_rooms.append(i)
    
    if disconnected_rooms:
        print(f"WARNING: Found {len(disconnected_rooms)} disconnected rooms: {disconnected_rooms}")
    else:
        print("All rooms appear to be connected!")


def test_cave_generation():
    """Test cave generation to see door placement."""
    print("\n\nTesting Cave Generation (Should NOT have doors)")
    print("=" * 80)
    
    config = MapGeneratorConfig(
        width=80,
        height=50,
        method=GenerationMethod.CELLULAR_AUTOMATA,
        initial_density=0.45,
        smoothing_iterations=5
    )
    
    generator = CaveGenerator(config)
    generator.generate()
    
    # Count tiles
    floor_count = 0
    wall_count = 0
    door_count = 0
    
    # Simple visualization
    for y in range(config.height):
        line = ""
        for x in range(config.width):
            tile = generator.get_tile(x, y)
            if tile == TileType.FLOOR:
                line += "."
                floor_count += 1
            elif tile == TileType.WALL:
                line += "#"
                wall_count += 1
            elif tile == TileType.DOOR:
                line += "+"
                door_count += 1
            elif tile == TileType.STAIRS_UP:
                line += "<"
            elif tile == TileType.STAIRS_DOWN:
                line += ">"
            else:
                line += "?"
        print(line)
    
    print(f"\nFloor tiles: {floor_count}")
    print(f"Wall tiles: {wall_count}")
    print(f"Door tiles: {door_count}")
    
    if door_count > 0:
        print("WARNING: Cave has doors! This shouldn't happen.")


if __name__ == "__main__":
    test_dungeon_connectivity()
    test_cave_generation()