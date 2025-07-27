"""Debug corridor carving issues."""

import sys
sys.path.insert(0, 'src')

from magemines.game.map_generator import (
    MapGeneratorConfig, DungeonGenerator, 
    GenerationMethod, TileType
)

def test_corridor_carving_debug():
    """Debug why corridors aren't being carved."""
    print("Debugging Corridor Carving")
    print("=" * 80)
    
    config = MapGeneratorConfig(
        width=40,
        height=30,
        min_room_size=4,
        max_room_size=6,
        max_rooms=3,  # Small number for easy debugging
        method=GenerationMethod.ROOMS_AND_CORRIDORS,
        diagonal_corridors=False,  # Disable diagonals for simpler debugging
        corridor_width=1
    )
    
    generator = DungeonGenerator(config)
    
    # Clear the map and create rooms manually for testing
    generator.clear(TileType.WALL)
    generator.rooms = []
    
    # Add 3 rooms manually
    from magemines.game.map_generator import Room
    
    room1 = Room(5, 5, 6, 6)
    generator._carve_room(room1)
    generator.rooms.append(room1)
    
    room2 = Room(20, 5, 6, 6)
    generator._carve_room(room2)
    generator.rooms.append(room2)
    
    room3 = Room(12, 15, 6, 6)
    generator._carve_room(room3)
    generator.rooms.append(room3)
    
    print(f"Created {len(generator.rooms)} rooms")
    for i, room in enumerate(generator.rooms):
        cx, cy = room.center()
        print(f"Room {i}: center at ({cx}, {cy})")
    
    # Show map before connecting
    print("\nMap BEFORE connecting rooms:")
    for y in range(30):
        line = ""
        for x in range(40):
            tile = generator.get_tile(x, y)
            if tile == TileType.FLOOR:
                line += "."
            elif tile == TileType.WALL:
                line += "#"
            else:
                line += "?"
        print(line)
    
    # Now connect rooms
    print("\nConnecting rooms...")
    generator._connect_rooms()
    
    print(f"Created {len(generator.corridors)} corridors")
    
    # Show map after connecting
    print("\nMap AFTER connecting rooms:")
    for y in range(30):
        line = ""
        for x in range(40):
            tile = generator.get_tile(x, y)
            if tile == TileType.FLOOR:
                # Mark room centers
                is_center = False
                for i, room in enumerate(generator.rooms):
                    cx, cy = room.center()
                    if x == cx and y == cy:
                        line += str(i)
                        is_center = True
                        break
                if not is_center:
                    line += "."
            elif tile == TileType.WALL:
                line += "#"
            else:
                line += "?"
        print(line)
    
    # Test a simple corridor manually
    print("\nTesting manual corridor from (8,8) to (23,8):")
    generator._carve_simple_corridor(8, 8, 23, 8)
    
    # Show result
    for y in range(5, 12):
        line = ""
        for x in range(40):
            tile = generator.get_tile(x, y)
            if tile == TileType.FLOOR:
                line += "."
            elif tile == TileType.WALL:
                line += "#"
            else:
                line += "?"
        print(line)


if __name__ == "__main__":
    test_corridor_carving_debug()