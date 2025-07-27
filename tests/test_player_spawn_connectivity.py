"""Test to ensure player always spawns in a connected area."""

import sys
sys.path.insert(0, 'src')

from collections import deque
from magemines.game.map_generator import (
    MapGeneratorConfig, DungeonGenerator, 
    GenerationMethod, TileType
)

def check_player_connectivity(generator, player_x, player_y):
    """Check if player can reach all rooms from their starting position."""
    # Flood fill from player position
    visited = set()
    queue = deque([(player_x, player_y)])
    reachable_tiles = 0
    reachable_rooms = set()
    
    while queue:
        x, y = queue.popleft()
        
        if (x, y) in visited:
            continue
        
        if not generator.in_bounds(x, y):
            continue
            
        tile = generator.get_tile(x, y)
        if tile == TileType.WALL:
            continue
        
        visited.add((x, y))
        reachable_tiles += 1
        
        # Check which room this position belongs to
        for i, room in enumerate(generator.rooms):
            if room.contains(x, y):
                reachable_rooms.add(i)
                break
        
        # Add neighbors
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (nx, ny) not in visited:
                queue.append((nx, ny))
    
    return reachable_rooms, reachable_tiles


def test_player_spawn_connectivity():
    """Test that player spawns in connected area over many iterations."""
    print("Testing Player Spawn Connectivity (50 iterations)")
    print("=" * 80)
    
    failed_tests = []
    
    for iteration in range(50):
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
        
        # Find stairs up position (player spawn point)
        player_x, player_y = None, None
        for y in range(config.height):
            for x in range(config.width):
                if generator.get_tile(x, y) == TileType.STAIRS_UP:
                    player_x, player_y = x, y
                    break
            if player_x is not None:
                break
        
        if player_x is None:
            print(f"Iteration {iteration}: ERROR - No stairs up found!")
            continue
        
        # Check connectivity from player position
        reachable_rooms, reachable_tiles = check_player_connectivity(generator, player_x, player_y)
        total_rooms = len(generator.rooms)
        
        # Count total floor tiles
        total_floor_tiles = 0
        for y in range(config.height):
            for x in range(config.width):
                tile = generator.get_tile(x, y)
                if tile in [TileType.FLOOR, TileType.DOOR, TileType.STAIRS_UP, TileType.STAIRS_DOWN]:
                    total_floor_tiles += 1
        
        if len(reachable_rooms) < total_rooms:
            failed_tests.append({
                'iteration': iteration,
                'total_rooms': total_rooms,
                'reachable_rooms': len(reachable_rooms),
                'unreachable': set(range(total_rooms)) - reachable_rooms,
                'player_pos': (player_x, player_y),
                'reachable_tiles': reachable_tiles,
                'total_tiles': total_floor_tiles
            })
            
            # Print details for first failure
            if len(failed_tests) == 1:
                print(f"\nIteration {iteration}: FAILED")
                print(f"Player at ({player_x}, {player_y}) can only reach {len(reachable_rooms)}/{total_rooms} rooms")
                print(f"Unreachable rooms: {set(range(total_rooms)) - reachable_rooms}")
                print(f"Reachable tiles: {reachable_tiles}/{total_floor_tiles}")
        else:
            if iteration % 10 == 0:
                print(f"Iteration {iteration}: OK - Player can reach all {total_rooms} rooms")
    
    print(f"\n{'='*80}")
    print(f"Summary: {len(failed_tests)}/50 tests failed")
    
    if failed_tests:
        print("\nFailed test details:")
        for test in failed_tests[:5]:  # Show first 5 failures
            print(f"  Iteration {test['iteration']}: Player at {test['player_pos']} reached {test['reachable_rooms']}/{test['total_rooms']} rooms")
            print(f"    Unreachable rooms: {test['unreachable']}")
            print(f"    Tile coverage: {test['reachable_tiles']}/{test['total_tiles']} ({100*test['reachable_tiles']/test['total_tiles']:.1f}%)")


def visualize_connectivity_issue():
    """Generate and visualize a map with connectivity issues."""
    print("\n\nVisualizing Connectivity Issue")
    print("=" * 80)
    
    # Keep generating until we find one with issues (for demonstration)
    for attempt in range(10):
        config = MapGeneratorConfig(
            width=60,
            height=40,
            min_room_size=4,
            max_room_size=8,
            max_rooms=15,
            method=GenerationMethod.ROOMS_AND_CORRIDORS
        )
        
        generator = DungeonGenerator(config)
        generator.generate()
        
        # Find stairs
        stairs_x, stairs_y = None, None
        for y in range(config.height):
            for x in range(config.width):
                if generator.get_tile(x, y) == TileType.STAIRS_UP:
                    stairs_x, stairs_y = x, y
                    break
            if stairs_x is not None:
                break
        
        if stairs_x is None:
            continue
        
        # Check connectivity
        reachable_rooms, _ = check_player_connectivity(generator, stairs_x, stairs_y)
        
        if len(reachable_rooms) < len(generator.rooms):
            print(f"Found example with connectivity issue!")
            print(f"Player can reach {len(reachable_rooms)}/{len(generator.rooms)} rooms")
            
            # Visualize
            for y in range(config.height):
                line = ""
                for x in range(config.width):
                    tile = generator.get_tile(x, y)
                    
                    # Mark player position
                    if x == stairs_x and y == stairs_y:
                        line += "@"
                    elif tile == TileType.FLOOR:
                        # Check if reachable
                        test_reach, _ = check_player_connectivity(generator, x, y)
                        if stairs_x is not None and len(test_reach) == len(reachable_rooms):
                            line += "."  # Reachable floor
                        else:
                            line += "!"  # Unreachable floor
                    elif tile == TileType.WALL:
                        line += "#"
                    elif tile == TileType.DOOR:
                        line += "+"
                    elif tile == TileType.STAIRS_DOWN:
                        line += ">"
                    else:
                        line += "?"
                print(line)
            
            print("\nLegend: @ = Player, . = Reachable, ! = Unreachable, # = Wall")
            return
    
    print("No connectivity issues found in 10 attempts (good!)")


if __name__ == "__main__":
    test_player_spawn_connectivity()
    visualize_connectivity_issue()