"""Comprehensive test for room connectivity in dungeon generation."""

import sys
sys.path.insert(0, 'src')

from collections import deque
from magemines.game.map_generator import (
    MapGeneratorConfig, DungeonGenerator, 
    GenerationMethod, TileType
)

def flood_fill_from_room(generator, room_idx):
    """Flood fill from a room to see what other rooms are reachable."""
    if room_idx >= len(generator.rooms):
        return set()
        
    room = generator.rooms[room_idx]
    cx, cy = room.center()
    
    # Make sure starting position is floor
    if generator.get_tile(cx, cy) == TileType.WALL:
        # Find a floor tile in the room
        found = False
        for y in range(room.y + 1, room.y + room.height - 1):
            for x in range(room.x + 1, room.x + room.width - 1):
                if generator.get_tile(x, y) == TileType.FLOOR:
                    cx, cy = x, y
                    found = True
                    break
            if found:
                break
        if not found:
            return set()  # Room has no floor tiles?
    
    visited = set()
    queue = deque([(cx, cy)])
    reachable_rooms = set([room_idx])  # Include starting room
    
    while queue:
        x, y = queue.popleft()
        
        if (x, y) in visited:
            continue
        
        if not generator.in_bounds(x, y):
            continue
            
        tile = generator.get_tile(x, y)
        if tile not in [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN]:
            continue
        
        visited.add((x, y))
        
        # Check which room this position belongs to
        for i, r in enumerate(generator.rooms):
            if r.contains(x, y) and i != room_idx:
                reachable_rooms.add(i)
                break
        
        # Add neighbors
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in visited:
                queue.append((nx, ny))
    
    return reachable_rooms


def test_connectivity_multiple_times():
    """Test room connectivity multiple times to catch intermittent issues."""
    print("Testing Room Connectivity (10 iterations)")
    print("=" * 80)
    
    failed_tests = []
    
    for iteration in range(10):
        config = MapGeneratorConfig(
            width=80,
            height=50,
            min_room_size=4,
            max_room_size=10,
            max_rooms=20,
            method=GenerationMethod.ROOMS_AND_CORRIDORS,
            diagonal_corridors=True,
            diagonal_chance=0.5
        )
        
        generator = DungeonGenerator(config)
        generator.generate()
        
        num_rooms = len(generator.rooms)
        if num_rooms < 2:
            continue
        
        # Check connectivity from first room
        reachable = flood_fill_from_room(generator, 0)
        
        if len(reachable) != num_rooms:
            failed_tests.append({
                'iteration': iteration,
                'total_rooms': num_rooms,
                'reachable_rooms': len(reachable),
                'unreachable': set(range(num_rooms)) - reachable
            })
            
            # Print map for first failure
            if len(failed_tests) == 1:
                print(f"\nIteration {iteration}: FAILED - {len(reachable)}/{num_rooms} rooms connected")
                print("Unreachable rooms:", set(range(num_rooms)) - reachable)
                print("\nMap visualization:")
                
                # Create a visualization showing room numbers
                room_map = [[' ' for _ in range(config.width)] for _ in range(config.height)]
                
                for y in range(config.height):
                    for x in range(config.width):
                        tile = generator.get_tile(x, y)
                        if tile == TileType.FLOOR:
                            room_map[y][x] = '.'
                        elif tile == TileType.WALL:
                            room_map[y][x] = '#'
                        elif tile == TileType.DOOR:
                            room_map[y][x] = '+'
                        elif tile == TileType.STAIRS_UP:
                            room_map[y][x] = '<'
                        elif tile == TileType.STAIRS_DOWN:
                            room_map[y][x] = '>'
                
                # Mark room centers with their index
                for i, room in enumerate(generator.rooms):
                    cx, cy = room.center()
                    if i < 10:
                        room_map[cy][cx] = str(i)
                    else:
                        room_map[cy][cx] = chr(ord('A') + i - 10)
                
                # Print the map
                for row in room_map:
                    print(''.join(row))
        else:
            print(f"Iteration {iteration}: OK - All {num_rooms} rooms connected")
    
    print(f"\nSummary: {len(failed_tests)}/10 tests failed")
    if failed_tests:
        print("\nFailed test details:")
        for test in failed_tests:
            print(f"  Iteration {test['iteration']}: {test['reachable_rooms']}/{test['total_rooms']} connected, unreachable: {test['unreachable']}")


def test_corridor_carving():
    """Test that corridors are being carved properly."""
    print("\n\nTesting Corridor Carving")
    print("=" * 80)
    
    config = MapGeneratorConfig(
        width=40,
        height=30,
        min_room_size=4,
        max_room_size=6,
        max_rooms=5,
        method=GenerationMethod.ROOMS_AND_CORRIDORS,
        corridor_width=1
    )
    
    generator = DungeonGenerator(config)
    generator.generate()
    
    print(f"Generated {len(generator.rooms)} rooms")
    print(f"Generated {len(generator.corridors)} corridors")
    
    # Visualize
    for y in range(config.height):
        line = ""
        for x in range(config.width):
            tile = generator.get_tile(x, y)
            if tile == TileType.FLOOR:
                # Check if in a room
                in_room = False
                for room in generator.rooms:
                    if room.contains(x, y):
                        in_room = True
                        break
                line += "R" if in_room else "."
            elif tile == TileType.WALL:
                line += "#"
            elif tile == TileType.DOOR:
                line += "+"
            else:
                line += "?"
        print(line)
    
    print("\nLegend: R=Room floor, .=Corridor floor, #=Wall, +=Door")


if __name__ == "__main__":
    test_connectivity_multiple_times()
    test_corridor_carving()