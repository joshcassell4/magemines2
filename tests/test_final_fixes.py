"""Final test to verify all fixes are working."""

import sys
sys.path.insert(0, 'src')

from magemines.game.level_manager import LevelManager
from magemines.game.map_generator import TileType

def test_all_levels():
    """Test various levels to ensure fixes are working."""
    print("Final Verification Test")
    print("=" * 80)
    
    # Create level manager
    level_manager = LevelManager(width=80, height=50, max_depth=10)
    
    # Test levels 1, 2, 5, 6 (town, dungeon, cave, dungeon)
    test_depths = [1, 2, 5, 6]
    
    for depth in test_depths:
        print(f"\n{'='*40}")
        print(f"Testing Level {depth}")
        print(f"{'='*40}")
        
        # Go to the specific depth
        while level_manager.current_depth < depth:
            level_manager.go_down()
        
        # Get the current level
        level = level_manager.get_current_level()
        generator = level.generator
        
        # Check generator type
        print(f"Generator type: {type(generator).__name__}")
        
        # Count various tiles
        floor_count = 0
        wall_count = 0
        door_count = 0
        stairs_up_count = 0
        stairs_down_count = 0
        
        for y in range(level.height):
            for x in range(level.width):
                tile = level.tiles[y][x]
                if tile == '.':
                    floor_count += 1
                elif tile == '#':
                    wall_count += 1
                elif tile == '+':
                    door_count += 1
                elif tile == '<':
                    stairs_up_count += 1
                elif tile == '>':
                    stairs_down_count += 1
        
        print(f"Floor tiles: {floor_count}")
        print(f"Wall tiles: {wall_count}")
        print(f"Door tiles: {door_count}")
        print(f"Stairs up: {stairs_up_count}")
        print(f"Stairs down: {stairs_down_count}")
        
        # Check connectivity for dungeons
        if type(generator).__name__ == 'DungeonGenerator' and hasattr(generator, 'rooms'):
            print(f"Number of rooms: {len(generator.rooms)}")
            
            # Simple connectivity check - can we reach all floor tiles from stairs?
            if stairs_up_count > 0:
                # Find stairs up position
                start_x, start_y = None, None
                for y in range(level.height):
                    for x in range(level.width):
                        if level.tiles[y][x] == '<':
                            start_x, start_y = x, y
                            break
                    if start_x is not None:
                        break
                
                if start_x is not None:
                    # Flood fill from stairs
                    from collections import deque
                    visited = set()
                    queue = deque([(start_x, start_y)])
                    reachable_floor = 0
                    
                    while queue:
                        x, y = queue.popleft()
                        if (x, y) in visited:
                            continue
                        if not (0 <= x < level.width and 0 <= y < level.height):
                            continue
                        if level.tiles[y][x] == '#':
                            continue
                        
                        visited.add((x, y))
                        if level.tiles[y][x] in ['.', '<', '>', '+']:
                            reachable_floor += 1
                        
                        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nx, ny = x + dx, y + dy
                            if (nx, ny) not in visited:
                                queue.append((nx, ny))
                    
                    total_walkable = floor_count + door_count + stairs_up_count + stairs_down_count
                    print(f"Connectivity: {reachable_floor}/{total_walkable} tiles reachable from stairs")
                    if reachable_floor < total_walkable:
                        print("WARNING: Not all floor tiles are reachable!")
                    else:
                        print("SUCCESS: All floor tiles are connected!")
        
        # Special checks for caves
        if type(generator).__name__ == 'CaveGenerator':
            if door_count > 0:
                print("WARNING: Cave has doors! This is a bug.")
            else:
                print("SUCCESS: Cave has no doors (as expected)")


if __name__ == "__main__":
    test_all_levels()